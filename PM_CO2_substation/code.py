# References:
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Circuit python to connect to PM2.5 sensor via I2C and to connect to an MQ-135 sensor with ADC.
This code is intended to be run on a Raspberry Pi Pico 2W running CircuitPython 
Data read in from the sensor will be sent over BLE to a Raspberry Pi 5.
"""

# pylint: disable=unused-import
import time
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C


reset_pin = None


# Create library object
#use 'slow' 100KHz frequency!
i2c = busio.I2C(board.GP5, board.GP4, frequency=100000) #SCL, SDA

# Connect to a PM2.5 sensor over I2C
pm25 = PM25_I2C(i2c, reset_pin)

print("Found PM2.5 sensor, reading data...")

while True:
    time.sleep(1)

    try:
        aqdata = pm25.read()
        # print(aqdata)
    except RuntimeError:
        print("Unable to read from sensor, retrying...")
        continue

    print()
    print("Concentration Units (standard)")
    print("---------------------------------------")
    print(
        "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
        % (aqdata["pm10 standard"], aqdata["pm25 standard"], aqdata["pm100 standard"])
    )
    print("Concentration Units (environmental)")
    print("---------------------------------------")
    print(
        "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
        % (aqdata["pm10 env"], aqdata["pm25 env"], aqdata["pm100 env"])
    )
    print("---------------------------------------")
    print("Particles > 0.3um / 0.1L air:", aqdata["particles 03um"])
    print("Particles > 0.5um / 0.1L air:", aqdata["particles 05um"])
    print("Particles > 1.0um / 0.1L air:", aqdata["particles 10um"])
    print("Particles > 2.5um / 0.1L air:", aqdata["particles 25um"])
    print("Particles > 5.0um / 0.1L air:", aqdata["particles 50um"])
    print("Particles > 10 um / 0.1L air:", aqdata["particles 100um"])
    print("---------------------------------------")
