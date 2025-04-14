import time
import board
import busio
import wifi
import socketpool
import microcontroller
import adafruit_minimqtt.adafruit_minimqtt as MQTT

uart = busio.UART(board.GP0, board.GP1, baudrate=115200, timeout=1)

# Step 1: Handshake with Pi
def establish_handshake():
    print("[Pico] Starting handshake loop...")
    while True:
        print("[Pico] Sending HELLO_PI")
        uart.write(b"HELLO_PI\n")
        time_start = time.monotonic()

        # Wait up to 2 seconds for response
        while time.monotonic() - time_start < 2:
            line = uart.readline()
            if line:
                try:
                    decoded = line.decode().strip()
                    print(f"[Pico] Received: {decoded}")
                    if decoded == "HELLO_PICO":
                        print("[Pico] Handshake complete.")
                        return
                except UnicodeDecodeError:
                    continue
        time.sleep(1)

establish_handshake()

# Step 2: Receive SSID and password
def wait_for_line(prompt):
    while True:
        line = uart.readline()
        if line:
            try:
                decoded = line.decode("utf-8").strip()
                print(f"[Pico] {prompt}: {decoded}")
                return decoded
            except UnicodeDecodeError:
                continue
        time.sleep(0.2)

ssid = wait_for_line("SSID")
password = wait_for_line("Password")
broker = wait_for_line("Broker IP")

# Step 3: Connect to Wi-Fi
try:
    wifi.radio.connect(ssid, password)
    print("[Pico] Connected to Wi-Fi!")
except Exception as e:
    print(f"[Pico] Wi-Fi connection failed: {e}")
    while True:
        pass

# Step 4: MQTT Setup and Temperature Publishing
#broker = "raspberrypi.local"
topic = "pico/temperature"

pool = socketpool.SocketPool(wifi.radio)
mqtt_client = MQTT.MQTT(
    broker=broker,
    port=1883,
    socket_pool=pool,
    client_id="pico2w"
)
#2
print("[Pico] Trying raw TCP to MQTT broker...")

try:
    s = pool.socket()
    s.connect((broker, 1883))
    print("[Pico] TCP connection successful.")
    s.close()
except Exception as e:
    print("[Pico] TCP connection failed:", e)

try:
    mqtt_client.connect()
    print("[Pico] Connected to MQTT broker.")
except Exception as e:
    print(f"[Pico] MQTT connection failed: {e}")
    while True:
        pass



while True:
    temperature = microcontroller.cpu.temperature
    mqtt_client.publish(topic, f"{temperature:.2f}")
    print(f"[Pico] Sent temperature: {temperature:.2f}°C")
    time.sleep(10)
