import os
import threading
from datetime import datetime

import pandas as pd
import paho.mqtt.client as mqtt
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from subsconfig import (
    MQTT_BROKER_IP,
    MQTT_BROKER_PORT,
    MQTT_CA_CERT,
    USERNAME,
    PASSWD,
    DASHBOARD_CLIENT_CERT,
    DASHBOARD_CLIENT_KEY
)

# =====================================================
# CONFIGURAÇÃO
# =====================================================

TOPICS = [
    "esp32/rtc_datetime",
    "esp32/rtc_temp"
]

MAX_SAMPLES = 500

# =====================================================
# ESTADO GLOBAL
# =====================================================

def init_session_state():

    if "mqtt_started" not in st.session_state:
        st.session_state.mqtt_started = False

    if "rtc_datetime" not in st.session_state:
        st.session_state.rtc_datetime = "--"

    if "current_temp" not in st.session_state:
        st.session_state.current_temp = None

    if "sync_error" not in st.session_state:
        st.session_state.sync_error = None

    if "temperature_history" not in st.session_state:
        st.session_state.temperature_history = pd.DataFrame(
            columns=[
                "timestamp",
                "temperature"
            ]
        )

# =====================================================
# MQTT CALLBACKS
# =====================================================

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[Dashboard] Conectado ao broker MQTT")

        for topic in TOPICS:
            client.subscribe(topic)
            print(f"[Dashboard] Inscrito em {topic}")
    else:
        print(f"[Dashboard] Falha na conexão MQTT: {rc}")


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")

    # ---------------------------------------------
    # RTC
    # ---------------------------------------------

    if msg.topic == "esp32/rtc_datetime":
        st.session_state.rtc_datetime = payload

        try:
            rtc_time = datetime.strptime(payload,"%Y-%m-%d %H:%M:%S")
            pc_time = datetime.now()

            error_seconds = abs((pc_time - rtc_time).total_seconds())
            st.session_state.sync_error = round(error_seconds,3)

        except Exception:
            pass

    # ---------------------------------------------
    # Temperatura
    # ---------------------------------------------

    elif msg.topic == "esp32/rtc_temp":
        try:
            temp = float(payload)
            st.session_state.current_temp = temp
            new_row = pd.DataFrame([
                {
                    "timestamp": datetime.now(),
                    "temperature": temp
                }
            ])

            st.session_state.temperature_history = pd.concat(
                [st.session_state.temperature_history,new_row],
                ignore_index=True
            )

            if len(st.session_state.temperature_history) > MAX_SAMPLES:
                st.session_state.temperature_history = (
                    st.session_state.temperature_history
                    .tail(MAX_SAMPLES)
                    .reset_index(drop=True)
                )

        except ValueError:
            print(f"[Dashboard] Temperatura inválida: {payload}")

# =====================================================
# MQTT WORKER
# =====================================================

def mqtt_worker():
    if not os.path.exists(MQTT_CA_CERT):
        print("ERRO: Certificado CA não encontrado.")
        return

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.tls_set(ca_certs=MQTT_CA_CERT,certfile=DASHBOARD_CLIENT_CERT,keyfile=DASHBOARD_CLIENT_KEY)
    client.username_pw_set(USERNAME,PASSWD)

    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[Dashboard] Conectando em {MQTT_BROKER_IP}:{MQTT_BROKER_PORT}")

    client.connect(MQTT_BROKER_IP,MQTT_BROKER_PORT,60)
    client.loop_forever()

# =====================================================
# INICIALIZA MQTT
# =====================================================

def start_mqtt():
    if not st.session_state.mqtt_started:
        mqtt_thread = threading.Thread(target=mqtt_worker,daemon=True)
        mqtt_thread.start()
        st.session_state.mqtt_started = True

# =====================================================
# INTERFACE
# =====================================================

def main():
    st.set_page_config(page_title="Monitoramento RTC DS3231",page_icon="📡",layout="wide")
    st_autorefresh(interval=1000,key="dashboard_refresh")

    st.title("📡 Monitoramento RTC DS3231")
    st.markdown("Monitoramento em tempo real dos dados enviados pelo ESP32.")

    # =================================================
    # HORÁRIOS
    # =================================================

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Horário Local",datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    with col2:
        st.metric("Horário RTC",st.session_state.rtc_datetime)

    with col3:
        if st.session_state.sync_error is not None:
            st.metric("Erro RTC-PC",f"{st.session_state.sync_error:.3f} s")

        else:
            st.metric("Erro RTC-PC","--")

    # =================================================
    # TEMPERATURA
    # =================================================

    st.divider()
    if st.session_state.current_temp is not None:
        st.metric("🌡️ Temperatura Atual",f"{st.session_state.current_temp:.2f} °C")

    else:
        st.metric("🌡️ Temperatura Atual","-- °C")

    # =================================================
    # GRÁFICO
    # =================================================
    
    st.divider()
    st.subheader("Temperatura × Tempo")
    df = st.session_state.temperature_history.copy()

    if not df.empty:

        df["timestamp"] = pd.to_datetime(
            df["timestamp"]
        )

        chart_df = df.set_index(
            "timestamp"
        )

        st.line_chart(
            chart_df["temperature"],
            use_container_width=True
        )

        with st.expander("Visualizar histórico completo"):
            st.dataframe(
                df.sort_values("timestamp",ascending=False),
                use_container_width=True
            )

    else:
        st.info("Aguardando dados de temperatura...")

if __name__ == "__main__":
    init_session_state()
    start_mqtt()
    main()