#!/usr/bin/python3
# Git Repository: https://github.com/ras434/noisyPi

import os
import signal
import subprocess
import time
import datetime
import sys

# Paho MQTT - See https://pypi.org/project/paho-mqtt/
# Instalation:
# pip install paho-mqtt
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
from config import *

colors = ["whitenoise", "pinknoise", "brownnoise"]  # color list must match input_list choices in Home Assistant
color_state = colors[len(colors) - 1]  # Set default color to last entry in _colors

state_topic = "noisypi/state"
command_topic = "noisypi/state/command"
availability_topic = "noisypi/availability"
volume_state_topic = "noisypi/volume"
volume_command_topic = "noisypi/volume/command"
color_state_topic = "noisypi/color"
color_command_topic = "noisypi/color/command"

subscribe_topics = [
    (state_topic, mqtt_qos),
    (command_topic, mqtt_qos),
    (availability_topic, mqtt_qos),
    (volume_state_topic, mqtt_qos),
    (volume_command_topic, mqtt_qos),
    (color_state_topic, mqtt_qos),
    (color_command_topic, mqtt_qos),
]

mqtt_connected = False

play_process = None


def publish_update():
    pub(state_topic, get_state())
    # time.sleep(0.5)
    pub(volume_state_topic, get_volume())
    # time.sleep(0.5)
    pub(color_state_topic, get_color())
    # time.sleep(0.5)


def get_state():
    if is_play_running():
        return "on"
    else:
        return "off"


def get_date_time():
    _date = datetime.datetime.now()
    _time = _date.strftime("%X")
    _date = _date.strftime("%x")
    return f"{_date} {_time} - "


def log(msg):
    print(f"{get_date_time()}{msg}")


def is_number(number):
    return type(number) == int or type(number) == float


def is_in_volume_range(number):
    if not is_number(number):
        return False
    else:
        if volumeMin <= int(number) <= volumeMax:
            return True
        else:
            return False


def is_play_running():
    if play_process is None:
        return False
    try:
        #call = subprocess.check_output("pidof 'play'", shell=True)
        # noinspection PyUnresolvedReferences
        return play_process.poll() is None
    except subprocess.CalledProcessError:
        return False


def set_noise(state, color=color_state):
    global play_process
    if state == "on":
        if not is_play_running():
            play_process = subprocess.Popen(f"play -n synth {color} > /dev/null 2>&1", stdout=subprocess.DEVNULL,
                                            shell=True, preexec_fn=os.setsid)
            # ret = os.system(f"nohup play -n synth {color} >/dev/null 2>&1  &")  # Plays in BG with no output
            log(f"setNoise({state})")
    else:
        if play_process is not None:
            pid = play_process.pid
            play_process = None
            try:
                log("os.killpg...")
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except Exception as e:
                print(e)
                pass
        kill_all_leftover_play_processes()
        log(f"setNoise({state})")
    publish_update()


def kill_all_leftover_play_processes():
    global play_process
    try:
        log("pkill...")
        # subprocess.Popen("ps -e | grep play | awk '{print $1}' | xargs kill", shell=True, preexec_fn=os.setsid)
        subprocess.Popen("pkill play", shell=True)
        play_process = None
    except Exception as e:
        print(e)
        pass


def set_color(color):
    log(f"set_color({color})")
    global color_state
    if is_play_running() and color != color_state:
        set_noise("off")
        # time.sleep(0.5) # TODO
        set_noise("on", color)
        # time.sleep(0.5) # TODO
    color_state = color
    pub(color_state_topic, get_color())


def get_color():
    return color_state
    # if is_play_running():
    #     return_color = os.popen("ps -e -f | grep -m1 synth | awk '{print $11}'").read()
    #     if return_color in colors:
    #         return return_color


def set_volume(volume):
    log(f"setVolume({volume})")
    if not get_volume() == volume:
        ret = os.system(f"amixer sset '{audioDevice}' {volume}% -q")
    pub(volume_state_topic, get_volume())


def get_volume():
    return int(os.popen("amixer | grep % | awk '{print $4}' | sed 's/\[//; s/\]//; s/\%//'").read())


def pub(topic, payload):
    if type(payload) == str:
        payload = payload.rstrip()  # remove CRLF, if exists
    log(f"Publishing to topic: [{topic}] payload: [{payload}]")
    # time.sleep(1)
    publish.single(topic=topic, payload=payload, qos=mqtt_qos, retain=mqtt_retain, hostname=mqtt_hostname,
                   auth=mqtt_credentials)


def do_disconnect():
    print(f"\n{get_date_time()}do_disconnect()")
    pub(availability_topic, "offline")
    # mqttc.loop_stop()
    mqttc.disconnect()
    print(f"\n{get_date_time()}Disconnected from {mqtt_hostname}.")


def mqtt_on_connect(_mqtt, userdata, flags, rc):
    global mqtt_connected
    log(f"Connected to {mqtt_hostname} with result code {rc}.")
    if rc == 0:
        mqtt_connected = True
        log(f"Connected OK > Returned code={rc}")
        log(f"Subscribing to: \n{get_date_time()}{subscribe_topics}.")
        mqttc.subscribe(subscribe_topics)
    else:
        log(f"Bad connection > Returned code={rc}")
        do_disconnect()


def mqtt_on_disconnect(_mqtt, userdata, rc):
    global mqtt_connected
    log(f"on_disconnect(client: {mqtt_client_name}, userdata: {userdata}, rc: {rc})")
    mqtt_connected = False
    # mqttc.connected_flag=False


def mqtt_on_message(_mqtt, userdata, msg):
    payload = str(msg.payload.decode('utf-8')).rstrip()
    log(f"on_message({msg.topic} {payload})")
    if payload in ('on', 'off') and msg.topic == command_topic:
        set_noise(payload)
    if payload in colors and msg.topic == color_command_topic:
        set_color(payload)
    if msg.topic == volume_command_topic:
        try:
            number = int(payload)
            if is_in_volume_range(number):
                set_volume(number)
        except Exception as e:
            print(e)
            pass


def mqtt_on_publish(_mqtt, userdata, rc):
    log(f"mqtt_on_publish(client: {mqtt_client_name}, userdata: {userdata}, rc: {rc})")


def mqtt_on_subscribe(_mqtt, userdata, mid, granted_qos):
    log(f"mqtt_on_subscribe(client: {mqtt_client_name}, userdata: {userdata}, rc: {mid}, granted_qos: {granted_qos})")


def mqtt_on_unsubscribe(_mqtt, userdata, mid, granted_qos):
    log(f"mqtt_on_unsubscribe(client: {mqtt_client_name}, userdata: {userdata}, rc: {mid}, granted_qos: {granted_qos})")


def mqtt_log(_mqtt, userdata, level, buf):
    log(f"mqtt_log: {buf}")


def full_justify(text, length, fill):
    r = length - len(text)
    return "[ " + text + " ]" + fill * r


kill_all_leftover_play_processes()

mqttc = mqtt.Client(mqtt_client_name, clean_session=True)
mqttc.enable_logger()
mqttc.on_connect = mqtt_on_connect
mqttc.on_disconnect = mqtt_on_disconnect
mqttc.on_message = mqtt_on_message
mqttc.on_publish = mqtt_on_publish
mqttc.on_subscribe = mqtt_on_subscribe
mqttc.on_unsubscribe = mqtt_on_unsubscribe
# mqttc.on_log = mqtt_log  # Uncomment line to enable MQTT logging

mqttc.username_pw_set(mqtt_credentials["username"], mqtt_credentials["password"])

mqttc.connect(mqtt_hostname, port=mqtt_port, keepalive=mqtt_keepalive)  # If MQTT not available, generates "ConnectionRefusedError"
mqttc.will_set(topic=availability_topic, payload="offline", qos=mqtt_qos, retain=mqtt_retain)

try:
    mqttc.loop_start()
    # time.sleep(1)
    time.sleep(0.1)
    while not mqtt_connected:
        sys.stdout.write(".")
        time.sleep(0.1)
    print()

except Exception as e:
    print(f"\n{get_date_time()}Error: {e}")
    do_disconnect()

# time.sleep(3)
pub(availability_topic, "online")

try:
    while mqtt_connected:
        time.sleep(1)
except Exception as e:
    print(f"\n{get_date_time()}Exit from sleep loop.")
    print(f"\n{get_date_time()}mqtt_connected = {mqtt_connected}")
    print(f"\n{get_date_time()}Error: {e}")
    kill_all_leftover_play_processes()
    do_disconnect()
    raise e

except KeyboardInterrupt as e:
    print(f"\n{get_date_time()}Aborting. (KeyboardInterrupt)")
    kill_all_leftover_play_processes()
    do_disconnect()
    print("\n\nGood bye.\n")
    raise e
