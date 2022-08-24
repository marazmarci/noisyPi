# noisyPi
Raspberry Pi noise generator integration with Home Assistant using MQTT.

![Maintenance](https://img.shields.io/maintenance/yes/2022?style=plastic)
[![GitHub stars](https://img.shields.io/github/stars/marazmarci/noisyPi?style=plastic)](https://github.com/marazmarci/noisyPi/stargazers)

---
# Requirements
+ Raspberry Pi
  + Speaker (connected to Raspberry Pi)
  + Python3 >= v3.7.3 (https://www.python.org/)
  + SoX - Sound eXchange (http://sox.sourceforge.net/)
  + paho-mqtt >= v1.5.1 (https://pypi.org/project/paho-mqtt/)
  + start `/home/pi/noisyPi/noisyPi.py` on boot via `/etc/rc.local`
+ Home Assistant (https://www.home-assistant.io/)
  + MQTT Broker (Mosquitto)
  + MQTT account (to authenticate with NoisyPi)
  + NoisyPi entities in `configuration.yaml` file
    + `switch.noisypi` - turn on/off
    + `number.noisypi_volume` - set volume
    + `input_select.noisypi_noise_color` - select noise color [whitenoise, pinknoise, brownnoise]
  + Automations
    + Noise color publish & subscribe MQTT

---
# Installation

## Steps


1. [Install Python3](https://github.com/marazmarci/noisyPi#1--install-python3)
2. [Install SoX - Sound eXchange](https://github.com/marazmarci/noisyPi#2-install-sox---sound-exchange)
3. [Install paho-mqtt](https://github.com/marazmarci/noisyPi#3-install-paho-mqtt)
4. [Edit /etc/rc.local](https://github.com/marazmarci/noisyPi#4-edit-etcrclocal)
5. [Clone noisyPi.py](https://github.com/marazmarci/noisyPi#5-clone-the-noisypi-repository)
6. [Setup Home Assistant](https://github.com/marazmarci/noisyPi#6-setup-home-assistant)
7. [Add noisyPi card to Home Assistant](https://github.com/marazmarci/noisyPi#7-add-noisypi-card-to-home-assistant)
8. [Reboot Your Raspberry Pi](https://github.com/marazmarci/noisyPi#8-reboot-your-raspberry-pi)

## 1. ![Python3](https://docs.python.org/3/_static/py.png) Install Python3
From the Raspberry Pi:
```sh
  sudo apt update
  sudo apt install python3
```

## 2. Install SoX - Sound eXchange
From the Raspberry Pi:

```sh
  apt-get install sox
```

## 3. Install paho-mqtt
From the Raspberry Pi:

```sh
  pip install paho-mqtt
```

## 4. Edit `/etc/rc.local`
From the Raspberry Pi:

Using nano or vi edit `/etc/rc.local`.

**nano example:**

```sh
  sudo nano /etc/rc.local
```

Paste the following lines to the end of the file:

```sh
  # Run noisyPi setup
  amixer sset 'Headphone' 95%
  python3 /home/pi/noisyPi/noisyPi.py
  exit 0
```

**CTRL+X** to exit, then **Y** to save, and **Enter** to confirm.

## 5. Clone the noisyPi repository
From the Raspberry Pi:

```sh
  cd
  git clone https://github.com/marazmarci/noisyPi.git
```

## 6. Setup Home Assistant
From Home Assistant `configuration.yaml` file, add the following entries:

```yaml
mqtt:
  switch:
    - name: noisyPi
      icon: mdi:speaker
      state_topic: "noisypi/state"
      command_topic: "noisypi/state/command"
      availability_topic: "noisypi/availability"
      payload_on: on
      payload_off: off
      state_on: on
      state_off: off
      qos: 1
  number:
    - name: NoisyPi volume
      icon: mdi:volume-high
      state_topic: "noisypi/volume"
      command_topic: "noisypi/volume/command"
      availability_topic: "noisypi/availability"
      min: 50
      max: 100
      step: 1
      qos: 1


input_select:
  noisypi_noise_color:
    name: NoisyPi Noise Color
    options:
      - whitenoise
      - pinknoise
      - brownnoise
    initial: brownnoise
    icon: mdi:palette
```
From **Configuration > Automations**, add the following 2 new automations:

<br>

`NoisyPi Color (pub)`:
```yaml
alias: NoisyPi Color (pub)
description: NoisyPi Color Selection Changed
trigger:
  - platform: state
    entity_id: input_select.noisypi_noise_color
condition: []
action:
  - service: mqtt.publish
    data:
      topic: cmnd/noisypi/COLOR
      retain: true
      qos: 1
      payload: '{{ states(''input_select.noisypi_noise_color'') }}'
mode: single
```

<br>

`NoisyPi Color (sub)`:
```yaml
alias: NoisyPi Color (sub)
description: Set NoisyPi Color Value
trigger:
  - platform: mqtt
    topic: stat/noisypi/COLOR
condition: []
action:
  - service: input_select.set_value
    target:
      entity_id: input_select.noisypi_color
    data:
      value: '{{ trigger.payload }}'
mode: single
```



## 7. Add noisyPi Card to Home Assistant
From Home Assistant:
In your Lovelace UI, edit your preferred dashboard and add the noisyPi elements:
![card](./images/noisyPi_HA_card.png)


## 8. Reboot Your Raspberry Pi:
From Raspberry Pi:

```sh
sudo reboot
```

Once your Pi completes the reboot, it should automatically start `noisyPi.py`.
