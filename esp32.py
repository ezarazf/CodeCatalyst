import machine
import time
import network
import dht
import urequests
import ssd1306
import gc

# WiFi Credentials
WIFI_SSID = "PUSTAKA_106b"
WIFI_PASSWORD = "bacalah!"

# API Endpoint
API_URL = "http://192.168.19.122:5000/data"  # Flask Server
UBIDOTS_URL = "https://industrial.api.ubidots.com/api/v1.6/devices/esp32/"

# Ubidots Token
UBIDOTS_TOKEN = "BBUS-s2xFKHYayKUNEEjWdbFrUxoiTjGdaU"
ubidot_headers = {"Content-Type": "application/json", "X-Auth-Token": UBIDOTS_TOKEN}

# Initialize Sensors & Display
pir_sensor = machine.Pin(4, machine.Pin.IN)  # PIR Motion Sensor
sensor = dht.DHT11(machine.Pin(15))  # DHT11 Sensor
i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))  # OLED Display
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Global Variables
motion_detected = False
last_temp, last_hum = None, None  # To prevent unnecessary updates

# WiFi Connection Function (Auto-reconnect)
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    oled.fill(0)
    oled.text("Connecting WiFi", 0, 0)
    oled.show()

    timeout = 10  # Wait up to 10 seconds
    while not wlan.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1

    if wlan.isconnected():
        oled.fill(0)
        oled.text("WiFi Connected!", 0, 0)
        oled.show()
        print("WiFi Connected:", wlan.ifconfig())
    else:
        oled.fill(0)
        oled.text("WiFi Failed!", 0, 0)
        oled.show()
        print("WiFi Connection Failed! Restarting ESP32...")
        time.sleep(2)
        machine.reset()  # Restart ESP32 if WiFi fails

# Ensure WiFi is connected before starting
connect_wifi()

# PIR Interrupt Handler (Instant Motion Detection)
def motion_callback(pin):
    global motion_detected
    motion_detected = True

pir_sensor.irq(trigger=machine.Pin.IRQ_RISING, handler=motion_callback)

# Function to Check & Reconnect WiFi
def check_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("WiFi Disconnected! Reconnecting...")
        connect_wifi()

# Function to Send Data with Retry Logic
def send_data(temp, hum, motion):
    data = {"temperature": temp, "humidity": hum, "motion": motion}
    headers = {"Content-Type": "application/json"}

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = urequests.post(API_URL, json=data, headers=headers, timeout=5)
            print(f"API Response: {response.status_code}")
            response.close()
            break  # Exit loop if successful
        except Exception as e:
            print(f"API Error (Attempt {attempt+1}): {e}")
            time.sleep(2)  # Wait before retrying

    for attempt in range(3):  # Retry Ubidots request
        try:
            response = urequests.post(UBIDOTS_URL, json=data, headers=ubidot_headers, timeout=5)
            print(f"Ubidots Response: {response.status_code}")
            response.close()
            break
        except Exception as e:
            print(f"Ubidots Error (Attempt {attempt+1}): {e}")
            time.sleep(2)

# Function to Update OLED
def update_oled(temp, hum, motion):
    oled.fill(0)
    oled.text(f"Temp: {temp}C", 0, 0)
    oled.text(f"Hum: {hum}%", 0, 10)
    oled.text(f"Motion: {'Yes' if motion else 'No'}", 0, 20)
    oled.show()

# Main Loop (Fast Detection)
while True:
    try:
        check_wifi()  # Ensure WiFi is connected
        gc.collect()  # Free memory
        
        if motion_detected:  # Only update when motion is detected
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()

            # Only update OLED if values change (reduces flickering)
            if temp != last_temp or hum != last_hum or motion_detected:
                update_oled(temp, hum, motion_detected)
                last_temp, last_hum = temp, hum  # Save last values

            print(f"Temp: {temp}C, Hum: {hum}%, Motion Detected!")

            # Send data
            send_data(temp, hum, 1)
            
            # Reset motion state
            motion_detected = False

    except Exception as e:
        print(f"General Error: {e}")

    time.sleep(0.01)  # Ultra-fast detection (100ms loop)
