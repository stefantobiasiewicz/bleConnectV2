import asyncio
import logging
from enum import Enum

from bleak import BleakClient, BleakGATTCharacteristic, BleakScanner
from pubsub import pub as bus

from topics import TOPIC_D_DISCONNECT_RESPONSE

logger = logging.getLogger(__name__)

ble_loop = asyncio.new_event_loop()


class DeviceType(str, Enum):
    WD = "WATER-DISPENSER"
    SM = "SOIL-SENSOR"
    TEST = "TEST"


class DeviceEntity:
    def __init__(self, name: str, address: str, type: str):
        self.name: str = name
        self.address: str = address
        self.type: DeviceType = DeviceType(type)


class BleDevice:
    def __init__(self, entity: DeviceEntity):
        self.client = BleakClient(address_or_ble_device=entity.address,
                                 disconnected_callback=self.disconnect_callback)
        self.entity : DeviceEntity = entity

    @property
    def is_connected(self):
        return self.client.is_connected

    def connect(self):
        if not self.is_connected:
            future = asyncio.run_coroutine_threadsafe(self.client.connect(), ble_loop)
            future.result()

    def connect_async(self):
        if not self.is_connected:
            future = asyncio.run_coroutine_threadsafe(self.client.connect(), ble_loop)

    def disconnect(self):
        future = asyncio.run_coroutine_threadsafe(self.client.disconnect(), ble_loop)
        future.result()

    def disconnect_callback(self, client: BleakClient):
        bus.sendMessage(topicName=TOPIC_D_DISCONNECT_RESPONSE, data={"address" : client.address})

    def write_gatt_char(self, char_specifier, data, response=False):
        asyncio.run_coroutine_threadsafe(self.client.write_gatt_char(char_specifier, data, response), ble_loop)

    def check_if_ready(self):
        if self.is_connected is False:
            raise Exception("deivce not conected")
        pass


SERWICE_WATER_DISPENSER_UUID = "12345678-1234-5678-1234-56789abcdef1"

CHARACTERISTIC_IMPULS_SET_UUID = "12345678-1234-5678-1234-56789abcdef2"
CHARACTERISTIC_RUN_UUID = "12345678-1234-5678-1234-56789abcdef3"
CHARACTERISTIC_IDENTIFY_UUID = "12345678-1234-5678-1234-56789abcdef4"
CHARACTERISTIC_ON_OFF_UUID = "12345678-1234-5678-1234-56789abcdef5"


class WaterDispenser(BleDevice):
    def wd_set_impuls(self, impuls: int):
        logger.info(f"wd_set_impuls - Input: impuls={impuls}")

        self.check_if_ready()

        if 0 <= impuls <= 0xFFFF:
            data_bytes = impuls.to_bytes(2, byteorder='little')
            asyncio.run_coroutine_threadsafe(
                self.client.write_gatt_char(char_specifier=CHARACTERISTIC_IMPULS_SET_UUID, data=data_bytes,
                                            response=True), ble_loop)
        else:
            raise ValueError("Invalid data value. Value must be between 0 and 65535.")

    def wd_run_on(self):
        logger.info("wd_run_on")

        self.check_if_ready()

        asyncio.run_coroutine_threadsafe(
            self.client.write_gatt_char(char_specifier=CHARACTERISTIC_RUN_UUID, data=b'\x01', response=True), ble_loop)

    def wd_run_off(self):
        logger.info("wd_run_off")

        self.check_if_ready()

        asyncio.run_coroutine_threadsafe(
            self.client.write_gatt_char(char_specifier=CHARACTERISTIC_RUN_UUID, data=b'\x00', response=True),
            ble_loop)

    def wd_identify_on(self):
        logger.info("wd_identify_on")

        self.check_if_ready()

        asyncio.run_coroutine_threadsafe(
            self.client.write_gatt_char(char_specifier=CHARACTERISTIC_IDENTIFY_UUID, data=b'\x01',
                                        response=True), ble_loop)

    def wd_identify_off(self):

        logger.info("wd_identify_off")

        self.check_if_ready()

        asyncio.run_coroutine_threadsafe(
            self.client.write_gatt_char(char_specifier=CHARACTERISTIC_IDENTIFY_UUID, data=b'\x00',
                                        response=True), ble_loop)

    def wd_on(self):
        logger.info("wd_on")

        self.check_if_ready()

        asyncio.run_coroutine_threadsafe(
            self.client.write_gatt_char(char_specifier=CHARACTERISTIC_ON_OFF_UUID, data=b'\x01',
                                        response=True), ble_loop)

    def wd_off(self):
        logger.info("wd_off")

        self.check_if_ready()

        asyncio.run_coroutine_threadsafe(
            self.client.write_gatt_char(char_specifier=CHARACTERISTIC_ON_OFF_UUID, data=b'\x00',
                                        response=True), ble_loop)


# GATT Service UUID
SOIL_SENSOR_SERVICE_UUID = "0000aaaa-0000-1000-8000-00805f9b34fb"

# Characteristic UUIDs
SOIL_SENSOR_CALIBRATION_UUID = "0000aaaa-0001-1000-8000-00805f9b34fb"
SOIL_SENSOR_TIME_INTERVAL_UUID = "0000aaaa-0002-1000-8000-00805f9b34fb"
SOIL_SENSOR_SOIL_MOISTURE_UUID = "0000aaaa-0003-1000-8000-00805f9b34fb"
SOIL_SENSOR_BATTERY_LEVEL_UUID = "0000aaaa-0004-1000-8000-00805f9b34fb"

CAL_START = 0x01
CAL_LOW = 0x02
CAL_HIGH = 0x04
CAL_END = 0x08


class SoilSensor(BleDevice):
    def connect(self):
        BleDevice.connect(self)
        self.set_notify(SOIL_SENSOR_SOIL_MOISTURE_UUID)

    def set_notify(self,
                   char_specifier: str):
        future = asyncio.run_coroutine_threadsafe(
            self.client.start_notify(char_specifier=char_specifier, callback=self.callback), ble_loop)

    def callback(self, sender: BleakGATTCharacteristic, data: bytearray):
        print(f"{sender}: {int.from_bytes(data, byteorder='little')}")

    def set_calibration(self, command: int):
        logger.info(f"set_calibration - Input: command={command}")

        self.check_if_ready()

        if command in [CAL_START, CAL_LOW, CAL_HIGH, CAL_END]:
            data_bytes = command.to_bytes(1, byteorder='little')
            asyncio.run_coroutine_threadsafe(
                self.client.write_gatt_char(char_specifier=SOIL_SENSOR_CALIBRATION_UUID, data=data_bytes,
                                            response=True), ble_loop)
        else:
            raise ValueError("Invalid calibration command.")

    def set_time_interval(self, interval: int):
        logger.info(f"set_time_interval - Input: interval={interval}")

        self.check_if_ready()

        if 0 <= interval <= 0xFFFF:
            data_bytes = interval.to_bytes(2, byteorder='little')
            asyncio.run_coroutine_threadsafe(
                self.client.write_gatt_char(char_specifier=SOIL_SENSOR_TIME_INTERVAL_UUID, data=data_bytes,
                                            response=True), ble_loop)
        else:
            raise ValueError("Invalid time interval. Value must be between 0 and 65535.")

    def read_soil_moisture(self):
        logger.info("read_soil_moisture")

        self.check_if_ready()

        asyncio.run_coroutine_threadsafe(
            self.client.read_gatt_char(char_specifier=SOIL_SENSOR_SOIL_MOISTURE_UUID), ble_loop)

    def read_battery_level(self):
        logger.info("read_battery_level")

        self.check_if_ready()

        future = asyncio.run_coroutine_threadsafe(
            self.client.read_gatt_char(char_specifier=SOIL_SENSOR_BATTERY_LEVEL_UUID), ble_loop)
        return future.result()

def create_ble_device(entity: DeviceEntity):
    if entity.type is DeviceType.WD:
        return WaterDispenser(entity=entity)
    elif entity.type is DeviceType.SM:
        return SoilSensor(entity=entity)


async def discover():
    return await BleakScanner().discover(timeout=10)

def search_and_return_new_device():
    future = asyncio.run_coroutine_threadsafe(discover(), ble_loop)
    devices_local = future.result()

    found_devices = []
    for device in devices_local:
        if SERWICE_WATER_DISPENSER_UUID in device.metadata.get('uuids'):
            print(f"Device found: {device.name} - {device.address}")
            found_devices.append({"address" : device.address, "name" : device.name, "type" : DeviceType.WD})
        elif SOIL_SENSOR_SERVICE_UUID in device.metadata.get('uuids'):
            print(f"Device found: {device.name} - {device.address}")
            found_devices.append({"address": device.address, "name": device.name, "type": DeviceType.SM})

    return found_devices