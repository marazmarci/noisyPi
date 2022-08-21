mqtt_hostname = "ha"  # DNS or IP address of your MQTT server/broker (i.e. Mosquitto)
mqtt_port = 1883
mqtt_credentials = {
    "username": "mqtt",
    "password": "mqtt1234",
}
mqtt_client_name = "noisyPi"
mqtt_keepalive = 60
mqtt_qos = 1
mqtt_retain = True
mqtt_publish_interval = 300  # 300 seconds (5 minutes) publish state update interval

audioDevice = "Headphone"  # Audio device to use on Raspberry Pi - Default = "Headphone"
volumeMax = 95
volumeMin = 50
