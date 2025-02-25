"""
Cleveroom integration for Home Assistant - Binary Sensor
For more detailed information, please refer to: https://www.cleveroom.com
"""
import asyncio
import logging
from typing import cast

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.const import (
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry  # Import ConfigEntry
from . import DOMAIN, ENTITY_REGISTRY, KLWIOTClient, DeviceType, device_registry_area_update, is_binary_sensor, \
    generate_object_id
from homeassistant.helpers import floor_registry as fr
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(  # Changed to async_setup_entry
        hass: HomeAssistant,
        entry: ConfigEntry,  # Added entry: ConfigEntry
        async_add_entities: AddEntitiesCallback,
) -> None:
    gateway_data = hass.data[DOMAIN][entry.entry_id]  # Access data from entry
    devices = gateway_data["devices"]
    client = gateway_data["client"]
    gateway_id = gateway_data["gateway_id"]
    auto_area = gateway_data["auto_area"]
    floor_registry = fr.async_get(hass)
    area_registry = ar.async_get(hass)
    device_registry = dr.async_get(hass)
    binary_sensors = []
    for device in devices:
        try:
            if is_binary_sensor(device):
                if auto_area == 1:
                    await device_registry_area_update(floor_registry, area_registry, device_registry, entry, device)
                sensor = CleveroomBinarySensor(hass, device, client, gateway_id)
                binary_sensors.append(sensor)
                ENTITY_REGISTRY.setdefault(entry.entry_id, {})
                ENTITY_REGISTRY[entry.entry_id][sensor.unique_id] = sensor
        except Exception as e:
            _LOGGER.warning(
                f"Device data is incomplete, skip: {device.get('oid', 'unknow')}, error message: {e}")

    async_add_entities(binary_sensors)

    def async_device_discovered(device, is_new):
        if is_new:
            try:
                if is_binary_sensor(device):
                    _LOGGER.info(f"add binary sensor new devices: {device['oid']}")
                    if auto_area == 1:
                        asyncio.run_coroutine_threadsafe(
                            device_registry_area_update(floor_registry, area_registry, device_registry, entry, device),
                            hass.loop)
                    sensor = CleveroomBinarySensor(hass, device, client, gateway_id)
                    asyncio.run_coroutine_threadsafe(
                        async_add_entities_wrapper(hass, async_add_entities, [sensor], True), hass.loop)
                    ENTITY_REGISTRY.setdefault(entry.entry_id, {})
                    ENTITY_REGISTRY[entry.entry_id][sensor.unique_id] = sensor
            except KeyError as e:
                _LOGGER.warning(f"Device data is incomplete, skip: {device.get('oid', 'unknow')}, error message: {e}")

    async def async_add_entities_wrapper(hass: HomeAssistant, async_add_entities: AddEntitiesCallback, entities: list,
                                         update_before_add: bool = False):
        async_add_entities(entities, update_before_add)

    client.on("on_device_change", async_device_discovered)


class CleveroomBinarySensor(BinarySensorEntity):

    def __init__(self, hass, device, client, gateway_id):
        self.hass = hass
        self._device = device
        self._client = cast(KLWIOTClient, client)
        self._oid = device["oid"]
        detail = device["detail"]
        fName = detail.get("fName", "")
        rName = detail.get("rName", "")
        dName = detail.get("dName", "")

        self._full_name = f"{fName} {rName} {dName}".strip()

        self._name = self._full_name
        self._value = None
        self._did = device["detail"]["did"]

        self._object_id = generate_object_id(gateway_id, self._oid)
        self.entity_id = f"binary_sensor.{self._object_id}"

        self.init_or_update_entity_state(device)

        if self._did == 194:
            self._attr_device_class = BinarySensorDeviceClass.DOOR
        elif self._did == 195:
            self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY
        elif self._did == 196:
            self._attr_device_class = BinarySensorDeviceClass.SMOKE
        elif self._did == 197:
            self._attr_device_class = BinarySensorDeviceClass.GAS
        else:
            self._attr_device_class = None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._oid)},
            name=self._full_name,
            manufacturer="Cleveroom",
            model="Generic"
        )

    def init_or_update_entity_state(self, device):
        self._device = device
        detail = device["detail"]
        self._value = detail["value"]

    @property
    def unique_id(self) -> str:
        return self._oid

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_on(self) -> bool:
        return self._value == 1

    @property
    def device_class(self) -> str:
        return self._attr_device_class

    @property
    def device_info(self) -> DeviceInfo:
        return self._attr_device_info

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
