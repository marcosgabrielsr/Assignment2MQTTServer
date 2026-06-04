import os
import sys
import requests
import datetime
import paho.mqtt.client as mqtt

from subsconfig import (
    MQTT_BROKER_IP,
    MQTT_BROKER_PORT,
    MQTT_CA_CERT,
    USERNAME,
    PASSWD,
    FIREBASE_CLIENT_CERT,
    FIREBASE_CLIENT_KEY
)

# --- TÓPICOS ---
TOPICS = ["esp32/rtc_datetime", "esp32/rtc_temp"]

# Substitua pelo URL do seu Firebase Realtime Database
FIREBASE_URL = "https://trabalho-1-fund-redes-default-rtdb.firebaseio.com/"

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[Firebase] Conectado ao Broker com TLS.")
        for t in TOPICS:
            client.subscribe(t)
    else:
        print(f"[Firebase] Falha na conexão. Código: {rc}")

def on_message(client, userdata, msg):
    arrival_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    value = msg.payload.decode("utf-8")
    topic = msg.topic.replace("esp32/", "").replace("/", "_")
    
    # Estrutura JSON organizada por data e tipo
    payload = {
        "timestamp": arrival_time,
        "topic": topic,
        "value": value,
        "received_at": datetime.datetime.now().isoformat()
    }
    
    try:
        # Push via REST API
        path = f"/rtc_data/{datetime.datetime.now().strftime('%Y-%m-%d')}.json"
        resp = requests.patch(f"{FIREBASE_URL}{path}", json=payload)
        if resp.status_code == 200:
            print(f"[Firebase] Enviado para {topic}: {value}")
        else:
            print(f"[Firebase] Erro REST: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"[Firebase] Exceção: {e}")

def main():
    if not os.path.exists(MQTT_CA_CERT):
        print("ERRO: Certificado CA não encontrado.")
        sys.exit(1)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.tls_set(ca_certs=MQTT_CA_CERT,certfile=FIREBASE_CLIENT_CERT,keyfile=FIREBASE_CLIENT_KEY)
    client.username_pw_set(USERNAME, PASSWD)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER_IP, MQTT_BROKER_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[Firebase] Encerrando...")
        client.disconnect()

if __name__ == "__main__":
    main()