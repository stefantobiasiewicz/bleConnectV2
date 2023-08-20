import logging
import time

from flask import Flask, jsonify, render_template, request
from flask_sse import sse
from pubsub import pub as bus

import global_cache
from ble_devices import DeviceEntity
from topics import TOPIC_S_SCAN_FOR_NEW, TOPIC_D_SCAN_FOR_NEW_RESPONSE, TOPIC_S_ADD_DEVICE, TOPIC_D_ADD_DEVICE_RESPONSE, \
    TOPIC_D_SM_SOIL_MEASURE_ADVERTISEMENT

app = Flask(__name__)
app.register_blueprint(sse, url_prefix='/stream')

logger = logging.getLogger(__name__)

def debug_soil_advetise(address: str, soil_moisture, battery):
    print(f"Debug soil moisture advertisemet message")
    print(f"[address: '{address}'")
    print(f"soil_moisture: {soil_moisture}%")
    print(f"battery: {battery}%]")

bus.subscribe(debug_soil_advetise, TOPIC_D_SM_SOIL_MEASURE_ADVERTISEMENT)


@app.route('/bleconnect/stats', methods=['GET'])
def get_bleconnect_stats():
    stats_json = global_cache.global_cache_to_json()
    return jsonify(stats_json)

# Lista nowych urządzeń
new_devices = []

@app.route('/bleconnect/getAll', methods=['GET'])
def get_all_devices():
    return jsonify(devices)

@app.route('/bleconnect/getNews', methods=['GET'])
def get_new_devices():
    return jsonify(new_devices)

@app.route('/bleconnect/getAdd', methods=['POST'])
def add_device():
    address = request.json.get("address")
    # Dodaj nowe urządzenie na podstawie adresu
    new_device = {"name": "New Device", "address": address, "device_type": "Unknown"}
    devices.append(new_device)
    return jsonify({"message": "Device added successfully"})

@app.route('/bleconnect/soil/connect', methods=['POST'])
def connect_to_device():
    address = request.json.get("address")
    # Logika do połączenia z urządzeniem na podstawie adresu
    return jsonify({"message": f"Connected to device with address {address}"})

@app.route('/bleconnect/soil/calibrate', methods=['POST'])
def calibrate_device():
    command = request.json.get("command")
    # Logika do kalibracji urządzenia na podstawie komendy
    return jsonify({"message": f"Calibrated device with command: {command}"})

@app.route('/bleconnect/soil/disconnect', methods=['POST'])
def disconnect_device():
    address = request.json.get("address")
    # Logika do rozłączenia urządzenia na podstawie adresu
    return jsonify({"message": f"Disconnected from device with address {address}"})

