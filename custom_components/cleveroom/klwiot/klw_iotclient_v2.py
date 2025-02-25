import asyncio
import time
from typing import List, Callable

from .klw_iotclient import KLWIOTClient
from .klw_security import Crypto


class KLWIOTClientLC(KLWIOTClient):
    def __init__(self, host='192.168.1.178', port=4196, code=None, client_id=None, password="1234", system_level=0,
                 connect_timeout=10, reconnect_interval=15, keeplive=True, language="zh-Hans", bucket_manager=None,
                 data_changed_callback: Callable[[], None] = None):
        super().__init__(host, port, client_id, password, system_level, connect_timeout, reconnect_interval, keeplive,
                         language, bucket_manager, data_changed_callback)
        self._code = code

    def login(self):
        # Login system, wait for verification to complete
        # await asyncio.sleep(2)  #
        time.sleep(2)
        # Loop non-blocking wait, return when _authed=True is detected, otherwise wait for timeout to return
        return self._authed

    def split_datas(self) -> None:
        """Handle data sharding"""
        buf = self.data_buffer
        temp = []
        length = len(buf)
        # self.log("Receiving data length:",self._authed,length)
        # If 37 bytes are received, it means an unauthorized connection
        if not self._authed and length >= 37:
            self._authed = False
            # Copy data to a temporary array
            for _ in range(length):
                temp.append(buf.pop(0))

            # Create a message array
            msg = [0] * 37
            for i in range(length):
                msg[i] = temp[i]

            # Process 01 instruction
            if msg[4] == 0x01:
                msg[4] = 0x04
                # Extract random number
                ran = [0] * 16
                for i in range(21, 37):
                    ran[i - 21] = msg[i]

                # Encryption processing
                cry_ran = Crypto.decrypt(ran, self._code)
                for i in range(21, 37):
                    msg[i] = cry_ran[i - 21]

                self._send_data(msg)

            # Process 05 instruction
            elif msg[4] == 0x05:
                if msg[21] == 0x01:
                    self.log("Connection successful")
                    self._authed = True
                    # self.after_connect()
                elif msg[21] == 0x00:
                    self._authed = False
                    self.log("Connection failed")
                    self.handle_disconnection()
            else:
                # If neither is 01 or 05, it is a failed instruction
                self.log(f"Received unknown instruction: {hex(msg[4])}")
                self._authed = False
                self.handle_disconnection()

        else:
            if self._authed:
                super().split_datas()
