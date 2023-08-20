import asyncio
import logging
import os
import time
from datetime import datetime
from threading import Thread
from typing import Optional

from bleak import BleakScanner, AdvertisementData, BLEDevice

import device_handler
import global_cache
from ble_devices import ble_loop, SOIL_SENSOR_SERVICE_UUID
from db import init_db
from mqtt import init_mqtt
from rest import app

DB_PATH = os.environ.get("DB_PATH")
# DB_PATH = '/Users/stefantobiasiewicz/Documents/Programing/Python/bleConnection/test'
# DB_PATH = os.environ.get("DB_PATH")


DB_PATH = '/Users/stefantobiasiewicz/Documents/Programing/Python/bleConnectV2/test'

if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)

    device_handler.init_devices(DB_PATH)

    init_db()
    init_mqtt()
    global_cache.time_of_start_service = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # special thread for bleak
    def bleak_thread(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()


    tread = Thread(target=bleak_thread, args=(ble_loop,))
    tread.daemon = True
    tread.start()

    def scanner_thread():
        while True:
            asyncio.run(device_handler.ble_scan_coroutine())


    tread_scanner = Thread(target=scanner_thread)
    tread_scanner.daemon = True
    tread_scanner.start()

    # bus.sendMessage(topicName=topics.TOPIC_S_CONNECT_ALL)

    app.run(host="0.0.0.0", port=8000, debug=False)
