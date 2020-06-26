#!/usr/bin/env python3

import os
import json
from bme280 import BME280
import time
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


# Keep running.
try:
    while True:
        i = i+1
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

        # New canvas to draw on.

        # message = "temp = " + str(temperature) + "\n" + \
        #     "press = " + str(pressure) + "\n" + "hum = " + \
        #     str(humidity) + "\n" + "CPU = " + str(cputempdisp) + \
        #     "\n" + "Comp Temp: {:05.2f} *C".format(comp_temp)'

        API_ENDPOINT = URL

        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        data = {
            "currentPoint": i2,
            "currentRawTemp": str(temperature),
            "currentHumidity": str(humidity),
            "currentPressure": str(pressure),
            "currentCpuTemp": str(cpu_temp),
            "currentAdjustedTemp": str(comp_temp),
            "currentLight": str(light),
            "currentco2": str(co2),
            "currentno2": str(no2),
            "currentnh3": str(nh3),
            "currentTime": str(current_time)
        }

        if (i % 1000 == 0):
            print("\n \n -------------------------- \n -------------------------- \n -------------------------- \n -------------------------- \n ")
            i2 = i2+1
            print("SENDING TO DB!")
            print("\n \n -------------------------- \n -------------------------- \n -------------------------- \n -------------------------- \n ")

            r = requests.post(url=API_ENDPOINT, json=data)
            res = json.loads(r.text)
            res = json.dumps(res)
            print(r)

            # RESPONSE CODE
            message = "POST #: " + str(i2) + "\n" + \
                "Status Code: " + "\n" + str(r)
            size_x, size_y = draw.textsize(message)

            # draw
            x = (WIDTH - size_x) / 2
            y = (HEIGHT / 2) - (size_y / 2)
            draw.rectangle((0, 0, 160, 80), back_colour)
            draw.text((x, y), message, fill=text_colour)
            disp.display(img)
            i = 0
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

        else:
            message = "Calibrating Sensor: " + str(i/10) + "%"
            size_x, size_y = draw.textsize(message)
            # Calculate text position
            x = (WIDTH - size_x) / 2
            y = (HEIGHT / 2) - (size_y / 2)
            # Draw background rectangle and write text.
            draw.rectangle((0, 0, 160, 80), back_colour)
            draw.text((x, y), message, fill=text_colour)
            disp.display(img)
        print(chr(27) + "[2J")
        print("TEST # = " + str(i/10) + "\n temp = " + str(temperature) + "\n humidity = " + str(humidity) + "\n pressure = " + str(pressure) + "\n CPU TEMP = " + str(cpu_temp) +
              "\n cmp temp = " + str(comp_temp) + "\n light = " + str(light) + "\n co = " + str(co2) + "\n no2 = " + str(no2) + "\n nh3 = " + str(nh3)) + "\n" + "-----------------------------------------"


# Turn off backlight on control-c
except KeyboardInterrupt:
    disp.set_backlight(0)
