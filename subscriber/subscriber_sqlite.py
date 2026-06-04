import sqlite3
import paho.mqtt.client as mqtt
import datetime
import os
import sys

from subsconfig import (
    MQTT_BROKER_IP,
    MQTT_BROKER_PORT,
    MQTT_CA_CERT,
    USERNAME,
    PASSWD,
    SQLITE_CLIENT_CERT,
    SQLITE_CLIENT_KEY
)

# --- CONFIGURAÇÃO ---
DB_NAME = "rtc_data.db"

# --- TÓPICOS ---
TOPICS = ["esp32/rtc_datetime", "esp32/rtc_temp"]

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arrival_timestamp TEXT NOT NULL,
            topic TEXT NOT NULL,
            value TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[SQLite] Conectado ao Broker com TLS.")
        for t in TOPICS:
            client.subscribe(t)
    else:
        print(f"[SQLite] Falha na conexão. Código: {rc}")

def on_message(client, userdata, msg):
    arrival_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    value = msg.payload.decode("utf-8")
    topic = msg.topic
    print(f"[SQLite] Recebido em {topic}: {value}")
    
    cursor = userdata["cursor"]
    cursor.execute("INSERT INTO sensor_readings (arrival_timestamp, topic, value) VALUES (?, ?, ?)",
                   (arrival_time, topic, value))
    userdata["conn"].commit()

def main():
    if not os.path.exists(MQTT_CA_CERT):
        print("ERRO: Certificado CA não encontrado. Execute o passo do Apêndice.")
        sys.exit(1)

    conn = init_db()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.user_data_set({"conn": conn, "cursor": conn.cursor()})
    
    client.tls_set(ca_certs=MQTT_CA_CERT,certfile=SQLITE_CLIENT_CERT,keyfile=SQLITE_CLIENT_KEY)
    client.username_pw_set(USERNAME, PASSWD)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER_IP, MQTT_BROKER_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[SQLite] Encerrando...")
        conn.close()
        client.disconnect()

if __name__ == "__main__":
    main()