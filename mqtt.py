import json
import os
import time
from threading import Thread

from pubsub import pub as bus
from datetime import datetime

import global_cache
from topics import TOPIC_D_SM_SOIL_MEASURE_ADVERTISEMENT
import paho.mqtt.client as mqtt

mqtt_client: mqtt.Client = None

mqtt_heartbeat_topic = "bleconnect/heartbeat"
mqtt_status_topic = "bleconnect/status"

# Flaga do śledzenia stanu MQTT
heartbeat_received = False

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")
    print(f"Mqtt status: {client.is_connected()}")

    client.subscribe(mqtt_heartbeat_topic)
    client.on_message = on_message

def on_message(client, userdata, message):
    global heartbeat_received
    if message.topic == mqtt_heartbeat_topic:
        print("Received heartbeat message")
        heartbeat_received = True

def connet_client():
    global mqtt_client
    try:
        if mqtt_client is not None:
            mqtt_client.disconnect()

        mqtt_user = os.environ.get("MQTT_USER")
        mqtt_password = os.environ.get("MQTT_PASSWORD")
        mqtt_host = os.environ.get("MQTT_HOST")
        mqtt_port = int(os.environ.get("MQTT_PORT", 1883))

        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(mqtt_user, mqtt_password)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(mqtt_host, mqtt_port)
        mqtt_client.loop_start()

        global_cache.mqtt_restart_in_session += 1
        global_cache.time_of_restart = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    except Exception as e:
        print(f"Failed to initialize MQTT: {e}")

def init_mqtt():
    def heartbeat_thread():
        while True:
            global mqtt_client
            if mqtt_client is None or mqtt_client.is_connected() is False:
                print("MQTT not connected initialization again.")
                connet_client()

            global heartbeat_received
            heartbeat_received = False
            print("Sending heartbeat message")
            mqtt_client.publish(mqtt_heartbeat_topic, "heartbeat")

            # Czekaj na odpowiedź "heartbeat" przez maksymalnie 30 sekund
            timeout = 0
            while not heartbeat_received and timeout < 5:
                time.sleep(1)
                timeout += 1

            if timeout >= 5:
                print("No heartbeat response, initializing MQTT...")
                connet_client()

            mqtt_client.publish(mqtt_status_topic, json.dumps(global_cache.global_cache_to_json()), retain=True)
            time.sleep(60)


    mqtt_alive_thread = Thread(target=heartbeat_thread)
    mqtt_alive_thread.daemon = True
    mqtt_alive_thread.start()


def mqtt_populate(address: str, soil_moisture, battery):
    global mqtt_client
    if mqtt_client is None or mqtt_client.is_connected() is False:
        print("MQTT not connected initialization again.")
        connet_client()


    print("populating measurements on mqtt")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "address": address,
        "soil_moisture": soil_moisture,
        "battery": battery,
        "timestamp": current_time
    }

    message = json.dumps(data)

    topic = 'bleconnect/' + address  # Using the address as the topic
    mqtt_client.publish(topic, message)

bus.subscribe(mqtt_populate, TOPIC_D_SM_SOIL_MEASURE_ADVERTISEMENT)