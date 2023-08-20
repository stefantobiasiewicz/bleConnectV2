import json

# Global Cache
mqtt_restart_in_session = 0
time_of_restart = ""
actual_unique_id = -1
time_of_start_service = ""

def global_cache_to_json():
    global_data = {
        "mqtt_restart_in_session": mqtt_restart_in_session,
        "actual_unique_id": actual_unique_id,
        "time_of_restart": time_of_restart,
        "time_of_start_service": time_of_start_service
        # Dodaj inne dane globalne do słownika
    }

    return global_data