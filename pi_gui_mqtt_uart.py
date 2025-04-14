import serial
import time
import threading
from paho.mqtt.client import Client
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import socket

# Wi-Fi credentials (you can load from a config file instead)
WIFI_SSID = "WSJ-Q528 1488"
WIFI_PASS = "qwerty1100"

# UART setup (adjust port as needed)
UART_PORT = "/dev/ttyAMA0"
UART_BAUD = 115200

# MQTT setup
MQTT_TOPIC = "pico/temperature"
MQTT_BROKER = "localhost"

# GUI setup
root = ttk.Window(themename="cyborg")
root.title("Pico Temperature Monitor")
temp_label = ttk.Label(root, text="Waiting for data...", font=("Arial", 20))
temp_label.pack(padx=20, pady=40)

# MQTT handling
def on_message(client, userdata, msg):
    temp = msg.payload.decode()
    temp_label.config(text=f"Temperature: {temp}°C")

mqtt_client = Client()
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER)
mqtt_client.subscribe(MQTT_TOPIC)

def mqtt_loop():
    mqtt_client.loop_forever()

threading.Thread(target=mqtt_loop, daemon=True).start()

# UART send credentials
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def send_wifi_credentials():
    try:
        with serial.Serial(UART_PORT, UART_BAUD, timeout=1) as ser:
            print("[Pi] Waiting for handshake from Pico...")
            while True:
                line = ser.readline()
                if line:
                    decoded = line.decode().strip()
                    print(f"[Pi] Received: {decoded}")
                    if decoded == "HELLO_PI":
                        print("[Pi] Handshake received. Sending acknowledgment...")
                        ser.write(b"HELLO_PICO\n")
                        time.sleep(0.5)
                        ser.write((WIFI_SSID + "\n").encode())
                        time.sleep(0.5)
                        ser.write((WIFI_PASS + "\n").encode())
                        time.sleep(0.5)
                        ip = get_ip()
                        ser.write((ip + "\n").encode())
                        print("[Pi] Wi-Fi credentials sent.")
                        break
    except Exception as e:
        print(f"[ERROR] {e}")


threading.Thread(target=send_wifi_credentials, daemon=True).start()

# Run GUI
root.mainloop()

"""
Device Handshake Flow
Sub: HELLO_PI
Base: HELLO
Sub: WIFI/BT/NRF...
Base: {Credentials}
Sub: File type (


"""
