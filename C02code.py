from mq135cpy import MQ135

import time
import board


# setup
temperature = 21.0
humidity = 25.0

mq135 = MQ135(board.GP26)  # analog PIN A0

# loop
while True:
    rzero = mq135.get_rzero()
    corrected_rzero = mq135.get_corrected_rzero(temperature, humidity)
    resistance = mq135.get_resistance()
    ppm = mq135.get_ppm()
    corrected_ppm = mq135.get_corrected_ppm(temperature, humidity)

    print("MQ135 RZero: " + str(rzero) + "\t Corrected RZero: " + str(corrected_rzero) +
            "\t Resistance: " + str(resistance) + "\t PPM: " + str(ppm) +
            "\t Corrected PPM: " + str(corrected_ppm) + "ppm")
    time.sleep(0.3)