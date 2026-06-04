//====================================================== Including libraries ======================================================
#include <RTClib.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include "conCredentials.h"

//========================================================== Defining Macros ====================================================== 
#define MSG_DELAY 10000

//================================================== Defining Variables and Objects ===============================================
// --- WiFi & MQTT Configuration ---
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWD;
const char* mqtt_server = HOSTNAME_IP;
const char* mqtt_ca_cert = MQTT_CA_CERT;
const char* mqtt_client_cert = MQTT_CLIENT_CERT;
const char* mqtt_client_key = MQTT_CLIENT_KEY;

WiFiClientSecure espClient;
PubSubClient client(espClient);

// --- Topics ---
const char* time_topic = "esp32/rtc_datetime";
const char* temp_topic = "esp32/rtc_temp";
// --- RTC Module Configuration ---
RTC_DS3231 rtc;
char daysOfTheWeek[7][4] PROGMEM = {"Sun","Mon","Tue","Wed","Thu","Fri","Sat"};
char bufferRTC[35];
float temp = 0;
// --- Control Variables ---
unsigned long lastMsg = 0;

//======================================================= Defining Functions ======================================================
// --- WiFi & MQTT Functions ---
void setupWifi() {
  delay(10);
  Serial.print("Connecting to ");
  Serial.print(ssid);
  WiFi.begin(ssid,password);
  
  while(WiFi.status() != WL_CONNECTED)  {
    delay(500);
    Serial.print(".");
  }

  Serial.print("\nWiFi Connected!\nIP address: ");
  Serial.println(WiFi.localIP());
  Serial.println("");

  Serial.print("Waiting time sincronization");
  configTime(0, 0, "pool.ntp.org", "time.google.com");
  while(time(nullptr) < 1000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nTime sincronized!");
}

void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messageTemp;

  for(int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messageTemp += (char)message[i];
  }
  Serial.println();
}

void reconnect() {
  // Loop until we're reconnected
  while(!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if(client.connect("ESP32Client","aluno","1234")) {
      Serial.println("connected");
      client.subscribe(time_topic);
      client.subscribe(temp_topic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

// --- RTC Message Format ---
char* stringRTCDateTime(DateTime dt, char* buffer) {
  // O buffer deve ter pelo menos 30 bytes: 
  // "Segunda-feira, 2026-05-02 10:30:32" + null terminator
  
  snprintf(buffer, 35, "%s,%04d-%02d-%02d %02d:%02d:%02d",
           daysOfTheWeek[dt.dayOfTheWeek()],
           dt.year(),
           dt.month(),
           dt.day(),
           dt.hour(),
           dt.minute(),
           dt.second());

  return buffer;
}

//=================================================================================================================================

void setup() {
  // Starting serial monitor
  Serial.begin(115200);

  // Checking connection
  if(!rtc.begin()) {
    Serial.println("Coudnl't find RTC");
    Serial.flush();
    while(1) delay(10);
  }

  // Checking if RTC lost power
  if(rtc.lostPower()) {
    Serial.println("RTC lost power, let's set the time!");
    rtc.adjust(DateTime(F(__DATE__),F(__TIME__)));
  }

  // Reset the time for today
  // rtc.adjust(DateTime(F(__DATE__),F(__TIME__)));

  // Connecting to WiFi
  setupWifi();
  // Client Secure Configuration
  espClient.setCACert(mqtt_ca_cert);
  espClient.setCertificate(mqtt_client_cert);
  espClient.setPrivateKey(mqtt_client_key);
  client.setServer(mqtt_server,8883);
  client.setCallback(callback);
}

void loop() {
  if(!client.connected()) {
    reconnect();
  }
  client.loop();

  long now = millis();
  if(now - lastMsg > MSG_DELAY) {
    lastMsg = now;

    // Get the current time from the RTC
    DateTime rtcNow = rtc.now();
    
    // Converting an Str to const char* and publish
    const char* dtString = stringRTCDateTime(rtcNow,bufferRTC);
    client.publish(time_topic, dtString);
    
    // Get the current temperature from the RTC
    temp = rtc.getTemperature();

    // Converting temp to string and publish
    char tempString[8];
    dtostrf(temp, 1, 2, tempString);
    client.publish(temp_topic, tempString);
  }
}