"""
Platform for alarm control panel integration.
For more detailed information, please refer to: https://www.cleveroom.com
"""
import asyncio
from typing import cast

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity, AlarmControlPanelState)
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelEntityFeature, CodeFormat)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import translation
from homeassistant.helpers.entity import DeviceInfo

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

import logging

from . import (DOMAIN, KLWIOTClient, ENTITY_REGISTRY,
               get_translation, is_alarm_control_panel, generate_object_id)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    gateway_data = hass.data[DOMAIN][entry.entry_id]
    devices = gateway_data["devices"]
    client = gateway_data["client"]
    gateway_id = gateway_data["gateway_id"]
    securitys = []

    for device in devices:
        try:
            if is_alarm_control_panel(device):
                security = CleveroomAlarmControlPanel(hass, device, client, entry, gateway_id)
                securitys.append(security)
                ENTITY_REGISTRY.setdefault(entry.entry_id, {})
                ENTITY_REGISTRY[entry.entry_id][security.unique_id] = security
        except Exception as e:
            _LOGGER.warning(f"Device data is incomplete, skip: {device.get('oid', 'unknow')}, error message: {e}")

    async_add_entities(securitys)

    def async_device_discovered(device, is_new):
        if is_new:
            try:
                if is_alarm_control_panel(device):
                    _LOGGER.info(f"add alarm panel new devices: {device['oid']}")
                    security = CleveroomAlarmControlPanel(hass, device, client, entry, gateway_id)
                    asyncio.run_coroutine_threadsafe(
                        async_add_entities_wrapper(hass, async_add_entities, [security], True), hass.loop)
                    ENTITY_REGISTRY.setdefault(entry.entry_id, {})
                    ENTITY_REGISTRY[entry.entry_id][security.unique_id] = security
            except KeyError as e:
                _LOGGER.warning(f"Device data is incomplete, skip: {device.get('oid', 'unknow')}, error message: {e}")

    async def async_add_entities_wrapper(hass, async_add_entities, entities,
                                         update_before_add = False):
        async_add_entities(entities, update_before_add)

    client.on("on_device_change", async_device_discovered)


class CleveroomAlarmControlPanel(AlarmControlPanelEntity):
    """Representation of a KLWIOT Alarm Control Panel."""

    def __init__(self, hass, device, client, entry, gateway_id) -> None:
        """Initialize the alarm control panel."""
        self._client = client
        self._entry = entry
        self.hass = hass
        self._device = device

        self._oid = device["oid"]
        self._client = cast(KLWIOTClient, client)

        self._attr_alarm_state = AlarmControlPanelState.DISARMED  # Initial state using _attr_alarm_state
        self._attr_name = get_translation(hass, "security_system_title", "Cleveroom Security System")
        self._name = self._attr_name
        self._attr_code_format = None  # Assuming numeric code
        self._attr_code_arm_required = False  # Code IS required for arming

        self._object_id = generate_object_id(gateway_id, self._oid)  # generate object_id
        self.entity_id = f"alarm_control_panel.{self._object_id}"  # generate entity_id

        self._attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_AWAY
        )

        self.init_or_update_entity_state(device)  #
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._oid)},
            name=self._name,
            manufacturer="Cleveroom",
            model="Generic",
        )

    def init_or_update_entity_state(self, device):
        self._device = device
        detail = device["detail"]

        self._attr_name = detail.get("coverName", "")
        state = detail.get("cover")

        if state == 2 or state == 0:
            self._attr_alarm_state = AlarmControlPanelState.ARMED_AWAY
        elif state == 1:
            self._attr_alarm_state = AlarmControlPanelState.DISARMED

    @property
    def unique_id(self) -> str:
        return self._oid

    @property
    def code_format(self) -> CodeFormat | None:
        return self._attr_code_format

    @property
    def code_arm_required(self) -> bool:
        return self._attr_code_arm_required

    @property
    def alarm_state(self):
        """Return the state of the alarm control panel."""
        return self._attr_alarm_state

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        _LOGGER.info("Send arm away command")
        try:
            self._client.controller.control("SetSecurity", [{"oid": self._oid, "value": 2}])
            self._attr_alarm_state = AlarmControlPanelState.ARMED_AWAY
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(f"error: {e}")

    async def async_alarm_arm_home(self, code=None) -> None:
        """Send arm home command."""
        _LOGGER.info("Send arm home command")
        await self.async_alarm_arm_away(code)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        _LOGGER.info("Send disarm command")
        try:
            self._client.controller.control("SetSecurity", [{"oid": self._oid, "value": 1}])
            self._attr_alarm_state = AlarmControlPanelState.DISARMED
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(f"error: {e}")

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        """Send trigger command."""
        _LOGGER.info("Send trigger command")
        try:
            self._client.controller.control("SetSecurity", [{"oid": self._oid, "value": 2}])
            self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(f"error: {e}")

    async def async_update(self):
        try:
            device = self._client.devicebucket.get_device_from_database(self._oid)
            if device is None:
                _LOGGER.error(f"Device not found: {self._oid}")
                return
            self.init_or_update_entity_state(device)
            if self.entity_id:
                self.async_write_ha_state()
            else:
                _LOGGER.warning(f"Entity {self._oid}{self.name} not yet registered, skipping async_write_ha_state")
        except Exception as e:
            _LOGGER.error(f"Failed to update entity {self._oid}{self.name}: {e}")
