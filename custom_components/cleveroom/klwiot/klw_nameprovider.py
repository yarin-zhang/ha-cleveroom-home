# -*- coding: utf-8 -*-
from .klw_i18n import get_meta_string, get_local_string


def getKLWFloor(language):
    return get_meta_string("floors", language)


def getKLWRoom(language):
    return get_meta_string("rooms", language)


def getKLWDevice(language):
    return get_meta_string("devices", language)


def getKLWScene(language):
    return get_meta_string("scenes", language)


def getKLWSensor(language):
    return get_meta_string("sensors", language)


def getKLWDryDevice(language):
    return get_meta_string("dries", language)


def get_default_floor_name(fid: int, lang: str):
    """Get default floor name"""
    klw_floors = getKLWFloor(lang)
    floor = next((v for v in klw_floors if v['id'] == fid), None)
    return floor['name'] if floor else None


def get_default_room_name(rid: int, lang: str):
    """Get default room name"""
    klw_rooms = getKLWRoom(lang)
    room = next((v for v in klw_rooms if v['id'] == rid), None)
    return room['name'] if room else None


def get_default_device_name(oid: int, lang: str):
    """Get default device name"""
    klw_devices = getKLWDevice(lang)
    device = next((v for v in klw_devices if v['id'] == oid), None)
    return device['name'] if device else None


def get_default_scene_name(did: int, lang: str):
    """Get default scene name"""
    klw_scenes = getKLWScene(lang)
    scene = next((v for v in klw_scenes if v['id'] == did), None)
    return scene['name'] if scene else None


def get_default_sensor_name(did: int, lang: str):
    """Get default sensor name"""
    klw_sensors = getKLWSensor(lang)
    sensor = next((v for v in klw_sensors if v['id'] == did), None)
    return sensor['name'] if sensor else None


def get_default_dry_name(did: str, lang: str):
    """Get default dry contact name"""
    klw_drys = getKLWDryDevice(lang)
    dry = next((v for v in klw_drys if v['id'] == did), None)
    return dry['name'] if dry else None


def get_i18n_string(key: str, lang: str):
    return get_local_string(key, lang)
