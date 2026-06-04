# Assignment2MQTTServer
Segundo trabalho da disciplina de **Tópicos em Redes de Computadores I**

## Descrição
Este trabalho apresenta um sistema IoT implementando um **Broker MQTT** utilizando o `mosquitto`, um **ESP32** como `publisher` publicando dados do sensor **RTC3231** e clients para armazenamento e visualização dos dados (`stremlit interface`,`firebase`,`sqlite`).

## Organização de Pastas e Arquivos
O Projeto possui três principais pastas sendo elas:

- **esp32_rtcds3231**: Contém os arquivos do firmware e das credenciais de conexão do esp32.

- **subscriber**: Contém os arquivos de configuração dos subscribers incluindo também as credenciais de conexão de cada subscriber.

Além disso, para configuração do mosquitto é utilizado o arquivo `mosquitto_tls_conf.py`. Uma vez executado ele utilizará funções encontradas em `mosquitto_utils.py` para alterar os arquivos contendo as credenciais de conexão de cada cliente.

## Modo de Uso
### Configurando mosquitto e certificados

Execute o arquivo `mosquitto_tls_conf.py` para gerar os certificados e o arquivo de configuração do mosquitto. Para isso rode o seguinte comando no terminal.

```bash
python3 mosquitto_tls_conf.py
```

### Carregando Firmware
Pela **Arduino IDE** abra o arquivo `esp32_rtcds3231/esp32_rtcds3231.ino`, configure a placa e a porta de saída e carregue o firmware para a placa.

O seguinte circuito está sendo utilizado:

![Circuito do Projeto](https://i0.wp.com/randomnerdtutorials.com/wp-content/uploads/2024/12/esp32-ds3231-wiring.png?w=912&quality=100&strip=all&ssl=1)

O pino `SQW` do módulo não foi utilizado, logo pode ser ignorado para este projeto.

### Iniciar Broker MQTT
Execute o arquivo `.init_mosquitto.sh` no terminal da seguinte maneira:

```bash
./init_mosquitto.sh
```

### Executando Subscribers
Cada subscriber será executado de uma maneira diferente. Segue abaixo os comandos para executar cada um:

 - **Firebase:**
 ```bash
 python3 subscriber/subscriber_firebase.py
 ```

 - **Sqlite:**
 ```bash
 python3 subscriber/subscriber_sqlite.py
 ```

 - **Stremlit dashboard:**
 ```bash
 streamlit run subscriber/subscriber_interface.py
 ```

# Observações Finais
Para correção de problemas de conexão, analize o conteúdo dos arquivos `conCredentials.h` e `subsconfig.py`, verifique também se os arquivos `mosquitto_tls_conf.py` e `mosquitto_utils.py` estão configurando corretamente o broker e os certificados de acesso.

Verifique também a rede de conexão em que seus dispositivos estão conectados, se necessário a troca atualize as constantes `WIFI_SSID` e `WIFI_PASSWD` no arquivo `mosquitto_tls_utils.py`.

# Referências
[Como utilizar sensor RTC3231 com ESP32](https://randomnerdtutorials.com/esp32-ds3231-real-time-clock-arduino/)