import socket
from pathlib import Path

PROJECT_PATH = Path(__file__).parent.absolute()

def get_local_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return ip

def get_content_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read().strip()
    
    return content

def create_credentials_ino(certs_path, ino_path, wifi_ssid, wifi_passwd, hostip):
    mqtt_ca_cert = get_content_file(f"{certs_path}/ca.crt")
    client_cert = get_content_file(f"{certs_path}/esp32.crt")
    client_key = get_content_file(f"{certs_path}/esp32.key")

    credentials_content = f"""#define WIFI_SSID "{wifi_ssid}"
#define WIFI_PASSWD "{wifi_passwd}"
#define HOSTNAME_IP "{hostip}"

const char* MQTT_CA_CERT = R"EOF({mqtt_ca_cert})EOF";

const char* MQTT_CLIENT_CERT = R"EOF({client_cert})EOF";

const char* MQTT_CLIENT_KEY = R"EOF({client_key})EOF";
"""

    with open(ino_path, "w", encoding="utf-8") as f:
        f.write(credentials_content)

def config_subscribers_certs(mqtt_certs_dir,subsconfig_file_path,hostip,username,passwd,port=8883):
    
    subs_config = f"""# Configurações Gerais
MQTT_BROKER_IP = "{hostip}"
MQTT_BROKER_PORT = {port}
MQTT_CA_CERT = "{mqtt_certs_dir}/ca.crt"
USERNAME = "{username}"
PASSWD = "{passwd}"

# Configurações Individuais
# --------- firebase ---------
FIREBASE_CLIENT_CERT = "{mqtt_certs_dir}/firebase.crt"
FIREBASE_CLIENT_KEY = "{mqtt_certs_dir}/firebase.key"

# --------- dashboard --------
DASHBOARD_CLIENT_CERT = "{mqtt_certs_dir}/dashboard.crt"
DASHBOARD_CLIENT_KEY = "{mqtt_certs_dir}/dashboard.key"

# --------- sqlite -----------
SQLITE_CLIENT_CERT = "{mqtt_certs_dir}/sqlite.crt"
SQLITE_CLIENT_KEY = "{mqtt_certs_dir}/sqlite.key"
"""
    with open(subsconfig_file_path, "w") as f:
        f.write(subs_config)