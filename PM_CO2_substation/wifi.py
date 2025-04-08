import time
import board
import wifi
import socketpool
import adafruit_requests

SSID = "Pixel_8775" # The hotspot of my phone, change it to the wifi ssid we will use
PASSWORD = "82076232"
print("Connecting to Wi‑Fi...")
wifi.radio.connect(SSID, PASSWORD)
print("Connected with IP:", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, None)

# Server URL on my laptop. Replace with your laptop’s IP address.
server_url = "http://10.189.164.106:5000/sensor"

# Dummy data counter
dummy_value = 0

while True:
    dummy_value += 1  # increase dummy data each loop
    url = server_url + "?dummy=" + str(dummy_value)
    print("Sending dummy data:", dummy_value)
    try:
        response = requests.get(url)
        print("Server response:", response.text)
        response.close()
    except Exception as e:
        print("Error sending data:", e)
    time.sleep(2)
