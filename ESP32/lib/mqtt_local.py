# mqtt_local.py Local configuration for mqtt_as demo programs.
from sys import platform, implementation
from mqtt_as import config
import ujson

f = open("settings.json")
configs = ujson.loads(f.read())
f.close()

#  config['server'] = '192.168.0.10'  # Change to suit

SPOT = "HOME"
SERVER= "FIO"
USER = "ADMIN"

config['server'] = configs["MQTT_SERVER"][SERVER]["URL"]
config['port'] = configs["MQTT_SERVER"][SERVER]["PORT"]

""" config['user'] = configs["MQTTS_USER"][USER]["USER"]
config['password'] = configs["MQTTS_USER"][USER]["PASS"] """

# Not needed if you're only using ESP8266
config['ssid'] =  configs[SPOT]["SSID"]
config['wifi_pw'] = configs[SPOT]["PASS"]


# For demos ensure same calling convention for LED's on all platforms.
# ESP8266 Feather Huzzah reference board has active low LED's on pins 0 and 2.
# ESP32 is assumed to have user supplied active low LED's on same pins.
# Call with blue_led(True) to light

if platform == 'esp8266' or platform == 'esp32':
    from machine import Pin
    def ledfunc(pin, active=0):
        pin = pin
        def func(v):
            pin(not v)  # Active low on ESP8266
        return pin if active else func
    wifi_led = ledfunc(Pin(14, Pin.OUT, value = 0))  # Red LED for WiFi fail/not ready yet
    blue_led = ledfunc(Pin(2, Pin.OUT, value = 1))  # Message received
    # Example of active high LED on UM Feather S3
    # blue_led = ledfunc(Pin(13, Pin.OUT, value = 0), 1)  # Message received ESP32-S3
elif platform == 'pyboard':
    from pyb import LED
    def ledfunc(led, init):
        led = led
        led.on() if init else led.off()
        def func(v):
            led.on() if v else led.off()
        return func
    wifi_led = ledfunc(LED(1), 1)
    blue_led = ledfunc(LED(3), 0)
elif platform == 'rp2':
    from machine import Pin
    def ledfunc(pin):
        pin = pin
        def func(v):
            pin(v)
        return func
    wifi_led = lambda _ : None  # Only one LED
    LED = 'LED' if 'Pico W' in implementation._machine else 25
    blue_led = ledfunc(Pin(LED, Pin.OUT, value = 0))  # Message received
else:  # Assume no LEDs
    wifi_led = lambda _ : None
    blue_led = wifi_led