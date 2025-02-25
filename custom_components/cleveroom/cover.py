"""
Cleveroom cover platform.
For more detailed information, please refer to: https://www.cleveroom.com
"""
import asyncio
import logging
from typing import cast

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry  # Import ConfigEntry
from homeassistant.helpers import floor_registry as fr
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from . import DOMAIN, KLWIOTClient, ENTITY_REGISTRY, device_registry_area_update, DeviceType, is_cover, \
    generate_object_id

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(  # Changed to async_setup_entry
        hass: HomeAssistant,
        entry: ConfigEntry,  # Added entry: ConfigEntry
        async_add_entities: AddEntitiesCallback,
) -> None:
    gateway_data = hass.data[DOMAIN][entry.entry_id]  # Access data from entry
    devices = gateway_data["devices"]
    gateway_id = gateway_data["gateway_id"]
    auto_area = gateway_data["auto_area"]
    client = hass.data[DOMAIN][entry.entry_id]["client"]

    floor_registry = fr.async_get(hass)
    area_registry = ar.async_get(hass)
    device_registry = dr.async_get(hass)
    covers = []
    for device in devices:
        try:
            if is_cover(device):
                if auto_area == 1:
                    await device_registry_area_update(
                        floor_registry, area_registry, device_registry, entry, device)
                cover = CleveroomCover(hass, device, client, gateway_id)
                covers.append(cover)
                ENTITY_REGISTRY.setdefault(entry.entry_id, {})
                ENTITY_REGISTRY[entry.entry_id][cover.unique_id] = cover
        except Exception as e:
            _LOGGER.warning(
                f"Device data is incomplete, skip: {device.get('oid', 'unknow')}, error message: {e}")

    async_add_entities(covers)

    def async_device_discovered(device, is_new):
        if is_new:
            try:
                if is_cover(device):
                    _LOGGER.info(f"add cover new devices: {device['oid']}")
                    if auto_area == 1:
                        asyncio.run_coroutine_threadsafe(
                            device_registry_area_update(
                                floor_registry, area_registry, device_registry, entry, device),
                            hass.loop)
                    cover = CleveroomCover(hass, device, client, gateway_id)
                    asyncio.run_coroutine_threadsafe(
                        async_add_entities_wrapper(hass, async_add_entities, [cover], True), hass.loop)
                    ENTITY_REGISTRY.setdefault(entry.entry_id, {})
                    ENTITY_REGISTRY[entry.entry_id][cover.unique_id] = cover
            except KeyError as e:
                _LOGGER.warning(f"Device data is incomplete, skip: {device.get('oid', 'unknow')}, error message: {e}")

    async def async_add_entities_wrapper(hass: HomeAssistant,
                                         async_add_entities: AddEntitiesCallback,
                                         entities: list,
                                         update_before_add: bool = False):
        async_add_entities(entities, update_before_add)

    client.on("on_device_change", async_device_discovered)


class CleveroomCover(CoverEntity):

    def __init__(self, hass, device, client, gateway_id):
        self.hass = hass
        self._device = device
        self._oid = device["oid"]
        self._client = cast(KLWIOTClient, client)

        detail = device["detail"]
        fName = detail.get("fName", "")
        rName = detail.get("rName", "")
        dName = detail.get("dName", "")

        self._full_name = f"{fName} {rName} {dName}".strip()

        self._object_id = generate_object_id(gateway_id, self._oid)
        self.entity_id = f"cover.{self._object_id}"

        self._name = self._full_name
        self._is_on = False
        self._scale = 0
        self._current_cover_position = 0

        self.init_or_update_entity_state(device)

        self._error_message = None
        # 设置支持的功能
        self._attr_supported_features = (
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.SET_POSITION
                | CoverEntityFeature.STOP
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._oid)},
            name=self._full_name,
            manufacturer="Cleveroom",
            model="Generic"

        )

    def init_or_update_entity_state(self, device):

        self._device = device

        self._is_on = device["detail"].get("on", self._is_on)
        self._scale = device["detail"].get("scale", self._scale)
        self._current_cover_position = self._scale * 10  # transform to 0-100

    @property
    def unique_id(self) -> str:
        return self._oid

    @property
    def name(self) -> str:
        return self._name

    # @property
    # def is_closed(self) -> bool | None:
    #     return self._scale == 0

    @property
    def current_cover_position(self) -> int | None:
        """cover postion 0-100."""
        return self._current_cover_position

    @property
    def extra_state_attributes(self):
        if self._error_message:
            return {"error_message": self._error_message}
        return None

    async def async_open_cover(self, **kwargs):
        _LOGGER.debug(f"open cover: {self._oid}")
        self._client.controller.control("ShadeOpen", [{"oid": self._oid}])
        self._scale = 10
        self._current_cover_position = 100
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs):
        _LOGGER.debug(f"close cover: {self._oid}")
        self._client.controller.control("ShadeClose", [{"oid": self._oid}])
        self._scale = 0
        self._current_cover_position = 0
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs):
        if "position" in kwargs:
            position = kwargs["position"]
            _LOGGER.debug(f"set cover position: {self._oid}, position: {position}")
            self._client.controller.control("SetShadeScale", [{"oid": self._oid, "value": position}])
            scale = int(position / 10)
            self._scale = scale
            self._current_cover_position = position
            self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs):
        _LOGGER.debug(f"stop cover: {self._oid}")
        self._client.controller.control("ShadePause", [{"oid": self._oid}])
        self.async_write_ha_state()

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
                _LOGGER.warning(f"Entity {self._oid}{self.name} "
                                f"not yet registered, skipping async_write_ha_state")
        except Exception as e:
            _LOGGER.error(f"Failed to update entity {self._oid}{self.name}: {e}")

    @property
    def current_cover_position(self):
        return self._current_cover_position

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._attr_supported_features

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        return None

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        return None

    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        return self._current_cover_position == 0
