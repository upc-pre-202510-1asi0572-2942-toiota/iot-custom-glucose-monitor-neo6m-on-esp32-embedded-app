import time
import network
import urequests
from machine import Pin, ADC

# ----------- CONFIGURACIÓN BLYNK -----------

BLYNK_AUTH = "zDuTwhyWD7FuoT58DQXcYrOI0UYvPr4Q"  # Tu Token real
BLYNK_VPIN_GLUCOSE = "V0"
BLYNK_VPIN_TEMP = "V1"

# ----------- CONFIGURACIÓN WI-FI -----------

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando a WiFi...')
        wlan.connect(ssid, password)
        timeout = 15
        while not wlan.isconnected() and timeout > 0:
            print("⌛ Esperando conexión...")
            time.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        print('✅ Conectado a WiFi con IP:', wlan.ifconfig()[0])
    else:
        print('❌ No se pudo conectar a WiFi')

# ----------- ENVÍO A BLYNK -----------

def send_to_blynk(pin, value):
    url = f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH}&{pin}={value}"
    try:
        r = urequests.get(url)
        print(f"📡 Enviado a Blynk ({pin}): {value}")
        r.close()
    except Exception as e:
        print(f"⚠️ Error al enviar a Blynk ({pin}): {e}")

# ----------- CLASE MONITOR -----------

class DiabetesMonitor:
    def __init__(self):
        # Sensor (simulado en pin 36/VP)
        self.glucose_sensor = ADC(Pin(36))
        self.glucose_sensor.atten(ADC.ATTN_11DB)

        # LEDs de alerta
        self.glucose_led = Pin(2, Pin.OUT)  # LED integrado
        self.temp_led = Pin(4, Pin.OUT)

        # Rangos clínicos
        self.GLUCOSE_NORMAL = (70, 180)
        self.TEMP_NORMAL = (35.5, 37.8)

        # Conversión analógica a valor clínico
        self.glucose_factor = 250.0 / 4095
        self.temp_factor = 10.0 / 4095

    def read_sensors(self):
        val = self.glucose_sensor.read()
        glucose = 50 + val * self.glucose_factor
        temp = 35 + val * self.temp_factor
        return glucose, temp

    def check_levels(self, glucose, temp):
        if glucose < self.GLUCOSE_NORMAL[0]:
            g_status = "HIPOGLUCEMIA"
            self.glucose_led.on()
        elif glucose > self.GLUCOSE_NORMAL[1]:
            g_status = "HIPERGLUCEMIA"
            self.glucose_led.on()
        else:
            g_status = "NORMAL"
            self.glucose_led.off()

        if temp < self.TEMP_NORMAL[0]:
            t_status = "HIPOTERMIA"
            self.temp_led.on()
        elif temp > self.TEMP_NORMAL[1]:
            t_status = "FIEBRE"
            self.temp_led.on()
        else:
            t_status = "NORMAL"
            self.temp_led.off()

        return g_status, t_status

    def run(self, interval=5):
        print("🩺 Monitor de Diabetes Iniciado")
        try:
            while True:
                glucose, temp = self.read_sensors()
                g_status, t_status = self.check_levels(glucose, temp)

                print("\n--------------------------------------")
                print(f"Glucosa:     {glucose:.1f} mg/dL - {g_status}")
                print(f"Temperatura: {temp:.1f} °C - {t_status}")
                print("--------------------------------------")

                send_to_blynk(BLYNK_VPIN_GLUCOSE, round(glucose, 1))
                send_to_blynk(BLYNK_VPIN_TEMP, round(temp, 1))

                time.sleep(interval)

        except KeyboardInterrupt:
            print("🛑 Monitor detenido")
            self.glucose_led.off()
            self.temp_led.off()

# ----------- INICIO -----------

# ⚠️ Reemplaza estas credenciales con las de tu red WiFi real (2.4 GHz)
connect_wifi("Wokwi-GUEST", "")

monitor = DiabetesMonitor()
monitor.run(interval=5)
