import asyncio
import json
import os

import librosa

from bleak import BLEDevice, AdvertisementData, BleakScanner
from pubsub import pub as bus

import global_cache
from ble_devices import BleDevice, search_and_return_new_device, DeviceEntity, create_ble_device, DeviceType, \
    SOIL_SENSOR_SERVICE_UUID
from global_cache import actual_unique_id
from topics import TOPIC_S_CONNECT_ALL, TOPIC_S_CONNECT, TOPIC_S_SCAN_FOR_NEW, TOPIC_D_SCAN_FOR_NEW_RESPONSE, \
    TOPIC_S_ADD_DEVICE, TOPIC_D_ADD_DEVICE_RESPONSE, TOPIC_D_SM_SOIL_MEASURE_ADVERTISEMENT

DEVICES: dict[str, BleDevice] = {}

# ************************* EVENT HANDLERS *************************
def connect_all():
    print(f'connecting all devices')
    for device in DEVICES.values():
        device.connect()


bus.subscribe(connect_all, TOPIC_S_CONNECT_ALL)


def connect(address: str):
    print(f'connecting device: {address}')
    if address in DEVICES.keys():
        DEVICES[address].connect()
    else:
        print(f"can't find device with addres: {address}")


bus.subscribe(connect, TOPIC_S_CONNECT)

ADDRESS_CACHE: dict[str, DeviceType] = {}

def scan_for_new():
    devices = search_and_return_new_device()
    for device in devices:
        ADDRESS_CACHE[device.get("address")] = device.get("type")

        if device.get('address') in DEVICES.keys():
            devices.remove(device)

    bus.sendMessage(topicName=TOPIC_D_SCAN_FOR_NEW_RESPONSE, devs=devices)


bus.subscribe(scan_for_new, TOPIC_S_SCAN_FOR_NEW)

def add_new(address: str):
    type = ADDRESS_CACHE[address]

    entity = DeviceEntity(address=address, name="nowe urzadzenie", type=type)
    DEVICES[address] = create_ble_device(entity)

    save_devices()

    bus.sendMessage(topicName=TOPIC_D_ADD_DEVICE_RESPONSE, dev=entity)


bus.subscribe(add_new, TOPIC_S_ADD_DEVICE)


cached_id = -1;

# ************************* ACTIVE SCANNIG *************************
async def scan_detection_callback(device: BLEDevice, data: AdvertisementData):
    if SOIL_SENSOR_SERVICE_UUID in device.metadata.get('uuids'): # and device.address in DEVICES.keys().__dict__:
        print(f"Soil sensor read: {device.name} - {device.address}")

        if(105 not in data.manufacturer_data.keys()):
            print("Soil sensor advetisement packet without data.")
            return

        byte_array = data.manufacturer_data[105]

        soil_moisture = ((byte_array[1] << 8) | byte_array[0]) / 10
        battery = ((byte_array[3] << 8) | byte_array[2]) / 10
        if (len(byte_array) > 4):
            unique_id = ((byte_array[5] << 8) | byte_array[4])

            global cached_id
            if (cached_id == unique_id):
                print(f"Soil sensor advetisement unique_id: {unique_id} is the same as cached_id: {cached_id} - doubled data.")
                return

            cached_id = unique_id

            global_cache.actual_unique_id = cached_id

            bus.sendMessage(topicName=TOPIC_D_SM_SOIL_MEASURE_ADVERTISEMENT, address=device.address,
                            soil_moisture=soil_moisture, battery=battery)
        else:
            print("data from V2.0.1 sensor saving")
            bus.sendMessage(topicName=TOPIC_D_SM_SOIL_MEASURE_ADVERTISEMENT, address=device.address,
                            soil_moisture=soil_moisture, battery=battery)

    return None


async def ble_scan_coroutine():
    scanner = BleakScanner(service_uuids=[SOIL_SENSOR_SERVICE_UUID], detection_callback=scan_detection_callback)

    while True:
        await scanner.start()
        await asyncio.sleep(10.0)
        await scanner.stop()




# ************************* DB source *************************

file_path = ''

def init_devices(folder_path):
    global file_path
    file_path = os.path.join(folder_path, 'devices.json')

    if os.path.exists(file_path):
        load_devices()
    else:
        save_devices()

def load_devices():
    with open(file_path, 'r') as file:
        data = json.load(file)
        for device in data:
            DEVICES[device.get('address')] = create_ble_device(DeviceEntity(**device))

def save_devices():
    data = [device.entity.__dict__ for device in DEVICES.values()]
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def add_device(device: DeviceEntity):
    if is_address_unique(device.address):
        DEVICES.append(create_ble_device(device))
        save_devices()
        return device
    else:
        raise ValueError('Address must be unique')

def get_devices():
    return DEVICES

def is_address_unique(address):
    for device in DEVICES.values():
        if device.entity.address == address:
            return False
    return True