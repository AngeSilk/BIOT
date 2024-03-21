from mqtt_as import MQTTClient
from mqtt_local import config, configs
import uasyncio as asyncio
import dht, machine
from machine import Pin
import ujson as json
import btree

WiFi = ["HOME", "FIO", "JC"]
wifi_flag = 0

# Configuración de los pines
DHT_PIN = 22
LED_PIN = 16
RELAY_PIN = 5
MOISTURE_SOIL = 32
#POWER_PIN = 34
#LIGHT_PIN = 33

ID_Dispositivo = "[AS]"+"{}".format(config['client_id'].decode('utf-8'))
SENSORES_TOPIC = "sensores_remotos/" + ID_Dispositivo

# Configuración de los parámetros iniciales
class Parameters():
    setpoint = 25.5
    period = 2.0
    mode = "automatico"
    rele = 1 #Inicia apagado (Logica Inversa)

param = Parameters()

#Variables sensadas
class Variables():
    temperatura = 0.0
    humedad = 0.0

var = Variables()

#Configuracion de los dispositivos
sensor = dht.DHT11(Pin(DHT_PIN))
relay = Pin(RELAY_PIN, Pin.OUT)
led = Pin(LED_PIN, Pin.OUT)
#led2 = Pin(LIGHT_PIN, Pin.OUT)
#bat = Pin(POWER_PIN, Pin.IN)

def update():
    relay.value(param.rele)
    led.on()

def update_db(topic=0, dato=0):

    try:

        if topic == 0 and dato == 0:

            f = open("mydb", "w+b")

            #Abrir base de datos
            db = btree.open(f)
            print("Creando base de datos")

            db[b"setpoint"] = b"{}".format(str(param.setpoint))
            db[b"periodo"] = b"{}".format(str(param.period))
            db[b"modo"] = b"{}".format(str(param.mode))
            db[b"rele"] = b"{}".format(str(param.rele))

        else:
            f = open("mydb", "r+b")

            #Abrir base de datos
            db = btree.open(f)
            print("Actualizando base de datos")
            dato = db[b"{}".format(topic)] = b"{}".format(dato)
            print(dato) #Debug

        db.flush()
        db.close()
        f.close()
        read_db()
    except OSError:
        print("Error al abrir el archivo")

def read_db():

    print("Ejecutando read db") #Debug

    #Abrir archivo binario
    try:
        f = open("mydb", "r+b")

        #Abrir base de datos
        db = btree.open(f)
        print("Se abrio la base de datos")

        param.setpoint = float(db[b"setpoint"])
        param.period = float(db[b"periodo"])
        param.mode = db[b"modo"].decode('utf-8')
        param.rele = int(db[b"rele"])

        print("Parametros actualizados") #Debug

        db.close()
        f.close()

    except OSError:
        print("No existe el archivo, creando...") #Debug
        update_db()

def sub_cb(topic, msg, retained):

    print('Topic = {} -> Valor = {}'.format(topic.decode(), msg.decode()))

    dato = msg.decode()
    topic = topic.decode().split('/')[2]

    if topic == "destello":
        asyncio.create_task(flash_led())
    if topic == "modo":
        update_db(topic,dato)
    if topic == "periodo":
        update_db(topic,dato)
    if topic == "setpoint":
        update_db(topic,dato)
    if param.mode == "manual" and topic == "rele":
        relay_control(dato)


async def wifi_han(state):
    if state:
        print('Wifi ', 'Conectado')
    else:
        print('Wifi ', 'Desonectado')
        SPOT = WiFi[wifi_flag+1]
        print("Probando con: ", SPOT)
        config['ssid'] =  configs[SPOT]["SSID"]
        config['wifi_pw'] = configs[SPOT]["PASS"]

    await asyncio.sleep(2)

# If you connect with clean_session True, must re-subscribe (MQTT spec 3.1.2.4)
async def conn_han(client):

    await client.subscribe(SENSORES_TOPIC + "/destello", 1)
    await client.subscribe(SENSORES_TOPIC + "/rele", 1)
    await client.subscribe(SENSORES_TOPIC + "/modo", 1)
    await client.subscribe(SENSORES_TOPIC + "/setpoint", 1)
    await client.subscribe(SENSORES_TOPIC + "/periodo", 1)

# Función para destellar el LED
async def flash_led():
    print("Inicio del destello") #Debug
    for n in range(10):
        led.on()
        await asyncio.sleep(0.5)
        led.off()
        await asyncio.sleep(0.5)
    print("Fin de destello") #Debug
    led.on()

def relay_control(value):
    value = int(value)
    if value == 1:
        print("Rele Activado") #Debug
        relay.value(0)
    if value == 0:
        print("Rele Desactivado") #debug
        relay.value(1)

#Lectura del sensor cada 1 seg
async def read_sensor():
    while True:
        try:
            sensor.measure()
            var.temperatura=sensor.temperature()
            var.humedad=sensor.humidity()
            print("Midio el sensor: Temp={} Hum={}".format(var.temperatura, var.humedad)) #Debug
            if param.mode == "automatico":
                relay_control(var.temperatura > param.setpoint)
            await asyncio.sleep(10)  # Give sense time
        except OSError as e:
            print("Problemas con el sensor") #Debug

async def main(client):

    await client.connect()
    await asyncio.sleep(2)  # Give broker time

    while True:
        try:
            datos = {"temperatura": var.temperatura, "humedad": var.humedad, "setpoint": param.setpoint, "periodo": param.period, "modo": param.mode}
            print(ID_Dispositivo)
            await client.publish(SENSORES_TOPIC, json.dumps(datos), qos = 1)
            await asyncio.sleep(param.period)
        except OSError as e:
            print("Ocurrio un herror") #Debug
        print("Publicacion exitosa") #Debug


# Define configuration
config['subs_cb'] = sub_cb
config['connect_coro'] = conn_han
config['wifi_coro'] = wifi_han
config['ssl'] = True

# Set up client
MQTTClient.DEBUG = True  # Optional
client = MQTTClient(config)

#Leer y actualizar parametros desde la base de datos
read_db()

#Actuar en base al ultimo parametro guardado
update()

#Funcion para medir sensor
asyncio.create_task(read_sensor())

try:
    asyncio.run(main(client))
finally:
    client.close()
    asyncio.new_event_loop()