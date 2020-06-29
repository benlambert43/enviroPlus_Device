#!/usr/bin/env python3

import os
import psutil
import json
import math
from bme280 import BME280
import time
import datetime
from datetime import date
import logging
from PIL import Image, ImageDraw, ImageFont
import ST7735
import requests
import socket
try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from enviroplus import gas

NODEJSPORT = 4000
FREQUENCY = 60


try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)


logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


# Create LCD class instance.
disp = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=10000000
)

# Initialize display.


def get_cpu_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp = f.read()
        temp = int(temp) / 1000.0
    return temp


# Tuning factor for compensation. Decrease this number to adjust the
# temperature down, and increase to adjust up
factor = 2
cpu_temps = [get_cpu_temperature()] * 5


# Width and height to calculate text position.
WIDTH = disp.width
HEIGHT = disp.height


disp.begin()

img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)

# Text settings.
font_size = 25
text_colour = (9, 174, 111)
back_colour = (0, 0, 0)


# GET Request to check if server is live:
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
print("Hostname: " + hostname)
print("IP Address: " + ip_address)
URL = "http://" + "localhost" + ":" + str(4000) + "/envirodata"
print("NodeJS URL: " + URL)
r = requests.get(url=URL)
print("Server responded with " + str(r))

i = 0.0
i2 = 0

message = "Starting Service.\n" + "Hostname: " + \
    hostname + "\n"

size_x, size_y = draw.textsize(message)

# Calculate text position
x = (WIDTH - size_x) / 2
y = (HEIGHT / 2) - (size_y / 2)

# Draw background rectangle and write text.
draw.rectangle((0, 0, 160, 80), back_colour)
draw.text((x, y), message, fill=text_colour)
disp.display(img)
time.sleep(1.0)


# Initializing Average Value Arrays
# currentRawTemp: temperature
# currentHumidity: humidity
# currentPressure: pressure
# currentCpuTemp: cpu_temp
# currentAdjustedTemp: comp_temp
# currentLight: light
# currentco2: co2
# currentno2: no2
# currentnh3: nh3
temperatureArr = []
humidityArr = []
pressureArr = []
cpuTemperatureArr = []
adjTempArr = []
lightArr = []
co2Arr = []
no2Arr = []
nh3Arr = []

# Clearing Database:
print("CLEARING DATABASE")
deleteURL = "http://10.0.0.91:4000/envirodata/DELETEALL/" + str(date.today())
d = requests.delete(url=deleteURL)
print(d)

backupURL = "http://10.0.0.91:4000/envirodata/save/"


# Keep running.
try:
    while True:
        i = i+1.0
        cpu_temp = get_cpu_temperature()
        # Smooth out with some averaging to decrease jitter
        cpu_temps = cpu_temps[1:] + [cpu_temp]
        avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
        raw_temp = bme280.get_temperature()
        time.sleep(0.5)
        comp_temp = raw_temp - ((avg_cpu_temp - raw_temp) / factor)
        time.sleep(0.5)

        # logging.info("Compensated temperature: {:05.2f} *C".format(comp_temp))

        cputempdisp = get_cpu_temperature()
        temperature = bme280.get_temperature()
        pressure = bme280.get_pressure()
        humidity = bme280.get_humidity()
        light = ltr559.get_lux()

        # CO2 (Reducing)
        gas_sensor = gas.read_all()
        co2 = gas_sensor.reducing / 1000

        # NO2 (Oxidising)
        no2 = gas_sensor.oxidising / 1000

        # NH3 (Ammonia)
        nh3 = gas_sensor.nh3 / 1000

        # Add to averaging arrays
        temperatureArr.append(temperature)
        humidityArr.append(humidity)
        pressureArr.append(pressure)
        cpuTemperatureArr.append(cpu_temp)
        adjTempArr.append(comp_temp)
        lightArr.append(light)
        co2Arr.append(co2)
        no2Arr.append(no2)
        nh3Arr.append(nh3)

        temperatureBalanced = sum(temperatureArr) / len(temperatureArr)
        humidityBalanced = sum(humidityArr) / len(humidityArr)
        pressureBalanced = sum(pressureArr) / len(pressureArr)
        cpuTemperatureBalanced = sum(
            cpuTemperatureArr) / len(cpuTemperatureArr)
        adjTempBalanced = sum(adjTempArr) / len(adjTempArr)
        lightBalanced = sum(lightArr) / len(lightArr)
        co2Balanced = sum(co2Arr) / len(co2Arr)
        no2Balanced = sum(no2Arr) / len(no2Arr)
        nh3Balanced = sum(nh3Arr) / len(nh3Arr)

        # Date
        today = date.today()

        # message = "temp = " + str(temperature) + "\n" + \
        #     "press = " + str(pressure) + "\n" + "hum = " + \
        #     str(humidity) + "\n" + "CPU = " + str(cputempdisp) + \
        #     "\n" + "Comp Temp: {:05.2f} *C".format(comp_temp)'

        API_ENDPOINT = URL

        t = time.localtime()
        today = date.today()
        current_time = time.strftime("%H:%M:%S", t)
        data = {
            "currentPoint": i2,
            "currentRawTemp": str(temperatureBalanced),
            "currentHumidity": str(humidityBalanced),
            "currentPressure": str(pressureBalanced),
            "currentCpuTemp": str(cpuTemperatureBalanced),
            "currentAdjustedTemp": str(adjTempBalanced),
            "currentLight": str(lightBalanced),
            "currentco2": str(co2Balanced),
            "currentno2": str(no2Balanced),
            "currentnh3": str(nh3Balanced),
            "currentTime": str(current_time),
            "currentDate": str(today)
        }

        # Reset the database every day.
        # Time will be 17 seconds.
        ResetHour = 23
        now = datetime.datetime.now()
        resetTimeFloor = now.replace(
            hour=ResetHour, minute=58, second=42, microsecond=0)
        resetTimeCeil = now.replace(
            hour=ResetHour, minute=59, second=59, microsecond=0)

        # Send the current average to the database, reset the averaging arrays.
        if (i % FREQUENCY == 0):

            i2 = i2+1

            r = requests.post(url=API_ENDPOINT, json=data)
            res = json.loads(r.text)
            res = json.dumps(res)
            time.sleep(2)

            saveURL = backupURL + str(today)
            saveRes = requests.get(url=saveURL)
            print("Saving...")
            print(saveRes)
            time.sleep(2)

            # RESPONSE CODE
            message = "POST #: " + str(i2) + "\n" + \
                "Status Code: " + "\n" + str(r)
            size_x, size_y = draw.textsize(message)
            print(message)

            # draw
            x = (WIDTH - size_x) / 2
            y = (HEIGHT / 2) - (size_y / 2)
            draw.rectangle((0, 0, 160, 80), back_colour)
            draw.text((x, y), message, fill=text_colour)
            disp.display(img)
            i = 0.0
            time.sleep(2.5)

            # DATA SENT:
            message = "Timestamp " + str(i2) + ":" + "\n" + str(current_time)
            size_x, size_y = draw.textsize(message)

            # draw
            x = (WIDTH - size_x) / 2
            y = (HEIGHT / 2) - (size_y / 2)
            draw.rectangle((0, 0, 160, 80), back_colour)
            draw.text((x, y), message, fill=text_colour)
            disp.display(img)
            time.sleep(2.05)
            print(message)

            del temperatureArr[:]
            del humidityArr[:]
            del pressureArr[:]
            del cpuTemperatureArr[:]
            del adjTempArr[:]
            del lightArr[:]
            del co2Arr[:]
            del no2Arr[:]
            del nh3Arr[:]

            if (now <= resetTimeCeil and now >= resetTimeFloor):
                print("\n \n \n \n -------------------------- \n ")
                print("SENDING RESET SIGNAL")
                print("\n \n -------------------------- \n ")
                deleteURL = "http://10.0.0.91:4000/envirodata/DELETEALL/" + \
                    str(today)
                d = requests.delete(url=deleteURL)
                i2 = 0
                i = 0
                continue

        else:
            message = "Status: " + str(int(math.floor(i/FREQUENCY * 100))) + "%" + "\n" + "CPU USAGE | RAM USAGE: " + "\n" + str(
                psutil.cpu_percent()) + "%      | " + str(psutil.virtual_memory().percent) + "%"
            print(message)
            size_x, size_y = draw.textsize(message)
            # Calculate text position
            x = (WIDTH - size_x) / 2
            y = (HEIGHT / 2) - (size_y / 2)
            # Draw background rectangle and write text.
            draw.rectangle((0, 0, 160, 80), back_colour)
            draw.text((x, y), message, fill=text_colour)
            disp.display(img)
        # print(chr(27) + "[2J")
        # print(str(today) + " " + str(current_time))
        # print("TEST # = " + str(i/10) + "\n temp = " + str(temperature) + "\n humidity = " + str(humidity) + "\n pressure = " + str(pressure) + "\n CPU TEMP = " + str(cpu_temp) +
        #      "\n cmp temp = " + str(comp_temp) + "\n light = " + str(light) + "\n co = " + str(co2) + "\n no2 = " + str(no2) + "\n nh3 = " + str(nh3)) + "\n" + "-----------------------------------------"


# Turn off backlight on control-c
except KeyboardInterrupt:
    disp.set_backlight(0)
