"""
Encryption utility class
"""

import hashlib
import base64
import hmac
from typing import Union, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class Crypto:
    """
    Encryption utility class, implemented using the cryptography library
    """

    @staticmethod
    def encryption(data: bytes, key: bytes) -> bytes:
        """
        AES-128-ECB encryption

        Args:
            data: The data to be encrypted
            key: 16-byte key

        Returns:
            bytes: Encrypted data
        """
        try:
            # Ensure the key length is 16 bytes
            if len(key) != 16:
                key = key.ljust(16, b'\0')[:16]

            # Create the encryptor
            cipher = Cipher(
                algorithms.AES(key),
                modes.ECB(),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()

            # Encrypt the data
            return encryptor.update(data) + encryptor.finalize()

        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")

    @staticmethod
    def decrypt(ran: Union[bytes, bytearray, list], app_secret: str) -> bytes:
        """
        Decrypt data

        Args:
            ran: The data to be decrypted
            app_secret: Key string

        Returns:
            bytes: Decrypted data
        """
        try:
            # Convert input data to bytes
            data = bytes(ran)
            keydata = app_secret.encode('utf-8')

            # Create a 16-byte key
            key = keydata.ljust(16, b'\0')[:16]

            # Create the decryptor
            cipher = Cipher(
                algorithms.AES(key),
                modes.ECB(),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Decrypt the data
            return decryptor.update(data) + decryptor.finalize()

        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")

    @staticmethod
    def hmac_sha256_base64(data: Union[str, bytes], key: Union[str, bytes]) -> str:
        """
        HMAC-SHA256 encryption and convert to Base64

        Args:
            data: The data to be encrypted
            key: Key

        Returns:
            str: Base64 encoded encryption result
        """
        try:
            # Ensure data and key are both bytes type
            if isinstance(data, str):
                data = data.encode('utf-8')
            if isinstance(key, str):
                key = key.encode('utf-8')

            # Create HMAC object and calculate
            h = hmac.new(key, data, hashlib.sha256)
            return base64.b64encode(h.digest()).decode('utf-8')

        except Exception as e:
            raise Exception(f"HMAC-SHA256 failed: {str(e)}")

    @staticmethod
    def md5(data: Union[str, bytes]) -> str:
        """
        Calculate MD5 value (32-bit uppercase)

        Args:
            data: The data to be calculated

        Returns:
            str: 32-bit uppercase MD5 value
        """
        try:
            # Ensure data is bytes type
            if isinstance(data, str):
                data = data.encode('utf-8')

            # Calculate MD5
            md5_hash = hashlib.md5()
            md5_hash.update(data)
            return md5_hash.hexdigest().upper()

        except Exception as e:
            raise Exception(f"MD5 calculation failed: {str(e)}")

    @staticmethod
    def md5_16(data: Union[str, bytes]) -> str:
        """
        Calculate 16-bit MD5 value (uppercase)

        Args:
            data: The data to be calculated

        Returns:
            str: 16-bit uppercase MD5 value
        """
        try:
            # Calculate the full MD5, then take the middle 16 bits
            full_md5 = Crypto.md5(data)
            return full_md5[8:24]

        except Exception as e:
            raise Exception(f"MD5-16 calculation failed: {str(e)}")
