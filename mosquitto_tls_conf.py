import os
import subprocess
from mosquitto_utils import PROJECT_PATH,get_local_ip,create_credentials_ino,config_subscribers_certs

FIRMWARE_DIR = os.path.join(PROJECT_PATH,"esp32_rtcds3231")             # Diretório do firmware do esp32
ESP32_CREDENTIALS_FILE = os.path.join(FIRMWARE_DIR,"conCredentials.h")  # Arquivo de credenciais de conexões do ESP32 
SUBSCRIBERS_DIR = os.path.join(PROJECT_PATH,"subscriber")               # Diretório com a configuração dos subscribers
SUBSCRIBERS_CONFIG_FILE = os.path.join(SUBSCRIBERS_DIR,"subsconfig.py") # Arquivo de configuração dos subscribers
BASE_DIR = os.path.expanduser("~/mqtt_secure")                          # Diretório base onde todos os arquivos serão criados
CERTS_DIR = os.path.join(BASE_DIR,"certs")                              # Pasta para armazenar certificados TLS
PASSWD_FILE = os.path.join(BASE_DIR,"passwd")                           # Arquivo que armazenará usuário e senha
os.makedirs(CERTS_DIR,exist_ok=True)                                    # Cria a pasta de certificados (se não existir)
WIFI_SSID = "DigitalNet - Javascript"                                   # WiFi SSID
WIFI_PASSWD = "bloco404"                                                # WiFi PASSWD
HOST_IP = get_local_ip()                                                # Endereço IP do Host

# Função auxiliar para executar comandos do sistema
def run(cmd):
    subprocess.run(cmd,shell=True,check=True)

# Função auxiliar para criar arquivo de configuração
def create_mosquitto_config(config_path,certs_dir=CERTS_DIR,passwd_file=PASSWD_FILE):
    # Conteúdo do arquivo de configuração
    config = f"""
    listener 8883

    cafile {certs_dir}/ca.crt
    certfile {certs_dir}/server.crt
    keyfile {certs_dir}/server.key
    require_certificate true

    allow_anonymous false
    password_file {passwd_file}

    log_type error
    """

    # Cria arquivo de configuração
    with open(config_path,"w") as f:
        f.write(config)

def config_client_mtls_certificates(file_name,cn):
    # Gera chave privada do cliente (ESP32)
    run(f"openssl genrsa -out {CERTS_DIR}/{file_name}.key 2048")

    # Cria CSR do cliente
    run(f"""openssl req -new \
        -key {CERTS_DIR}/{file_name}.key \
        -out {CERTS_DIR}/{file_name}.csr \
        -subj "/CN={cn}" """)

    # Assina certificado do cliente usando a CA
    run(f"""openssl x509 -req \
        -in {CERTS_DIR}/{file_name}.csr \
        -CA {CERTS_DIR}/ca.crt \
        -CAkey {CERTS_DIR}/ca.key \
        -CAcreateserial \
        -out {CERTS_DIR}/{file_name}.crt \
        -days 365 \
        -sha256""")

def main():
    # ====================================== TLS ==========================================
    # Gera chave privada da Autoridade Certificadora (CA)
    run(f"openssl genrsa -out {CERTS_DIR}/ca.key 2048")

    # Gera certificado da CA (autoassinado)
    run(f"""openssl req -x509 -new -nodes -key {CERTS_DIR}/ca.key -sha256 -days 365 \
        -out {CERTS_DIR}/ca.crt -subj "/CN=MQTT-CA" """)

    # Gera chave privada do servidor (Mosquitto)
    run(f"openssl genrsa -out {CERTS_DIR}/server.key 2048")

    # Cria requisição de certificados (CSR)
    run(f"""openssl req -new -key {CERTS_DIR}/server.key -out {CERTS_DIR}/server.csr \
        -subj "/CN={HOST_IP}" """)

    # Arquivo de extensões para adicionar SAN
    server_ext = os.path.join(CERTS_DIR, "server.ext")

    with open(server_ext, "w") as f:
        f.write(f"subjectAltName=IP:{HOST_IP}\n")

    # Assina o certificado do servidor com a CA
    run(f"""openssl x509 -req \
        -in {CERTS_DIR}/server.csr \
        -CA {CERTS_DIR}/ca.crt \
        -CAkey {CERTS_DIR}/ca.key \
        -CAcreateserial \
        -out {CERTS_DIR}/server.crt \
        -days 365 \
        -sha256 \
        -extfile {server_ext}""")

    # ====================================== CLIENTE ==========================================
    config_client_mtls_certificates("esp32", "esp32")
    config_client_mtls_certificates("sqlite", "sqlite_subscriber")
    config_client_mtls_certificates("firebase", "firebase_subscriber")
    config_client_mtls_certificates("dashboard", "dashboard_subscriber")

    # ======================================  MQTT  ==========================================
    print("Criando usuário MQTT...")

    # Cria usuário e senha (arquivo criptografado)
    if os.path.exists(PASSWD_FILE):
        run(f"mosquitto_passwd -b {PASSWD_FILE} aluno 1234")
    else:
        run(f"mosquitto_passwd -b -c {PASSWD_FILE} aluno 1234")
    
    # Caminho do arquivo de configuração
    config_path = os.path.join(BASE_DIR,"mosquitto.conf")

    # Gerando arquivo de configuração
    create_mosquitto_config(config_path)

    # Gerando arquivo de credenciais para o ESP32
    create_credentials_ino(CERTS_DIR,ESP32_CREDENTIALS_FILE,WIFI_SSID,WIFI_PASSWD,HOST_IP)

    # Gerando arquivo de configruações dos subscribers
    config_subscribers_certs(CERTS_DIR,SUBSCRIBERS_CONFIG_FILE,HOST_IP,"aluno","1234")

    print(f"Configuração criada em: {config_path}")

if __name__ == "__main__":
    main()