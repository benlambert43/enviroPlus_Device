#!/usr/bin/env python3

import ST7735
from PIL import Image, ImageDraw, ImageFont
import logging
import time
from bme280 import BME280
import os
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
disp.begin()


def get_cpu_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp = f.read()
        temp = int(temp) / 1000.0
    return temp


# Tuning factor for compensation. Decrease this number to adjust the
# temperature down, and increase to adjust up
factor = 0.95
cpu_temps = [get_cpu_temperature()] * 5


# Width and height to calculate text position.
WIDTH = disp.width
HEIGHT = disp.height


# Keep running.
try:
    while True:
        cpu_temp = get_cpu_temperature()
        # Smooth out with some averaging to decrease jitter
        cpu_temps = cpu_temps[1:] + [cpu_temp]
        avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
        raw_temp = bme280.get_temperature()
        comp_temp = raw_temp - ((avg_cpu_temp - raw_temp) / factor)
        # logging.info("Compensated temperature: {:05.2f} *C".format(comp_temp))
        time.sleep(1.0)

        cputempdisp = get_cpu_temperature()
        temperature = bme280.get_temperature()
        pressure = bme280.get_pressure()
        humidity = bme280.get_humidity()
        # New canvas to draw on.
        img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Text settings.
        font_size = 25
        text_colour = (255, 255, 255)
        back_colour = (0, 170, 170)

        message = "temp = " + str(temperature) + "\n" + \
            "press = " + str(pressure) + "\n" + "hum = " + \
            str(humidity) + "\n" + "CPU = " + str(cputempdisp) + \
            "\n" + "Comp Temp: {:05.2f} *C".format(comp_temp)
        size_x, size_y = draw.textsize(message)

        # Calculate text position
        x = (WIDTH - size_x) / 2
        y = (HEIGHT / 2) - (size_y / 2)

        # Draw background rectangle and write text.
        draw.rectangle((0, 0, 160, 80), back_colour)
        draw.text((x, y), message, fill=text_colour)
        disp.display(img)
        time.sleep(10.0)


# Turn off backlight on control-c
except KeyboardInterrupt:
    disp.set_backlight(0)
