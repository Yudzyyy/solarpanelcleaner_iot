#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// --- KONFIGURASI WIFI & MQTT ---
const char* ssid = "tutus"; 
const char* password = "abcd123woi"; 
const char* mqtt_server = "192.168.84.232"; 

const unsigned long DURATION_PER_PHASE = 33000; 
const unsigned long BACKOFF_DURATION = 500;  

WiFiClient espClient;
PubSubClient client(espClient);

// --- PIN DEFINITIONS ---
#define MOTOR_NAIK 16      
#define MOTOR_TURUN 5      
#define LED_INDIKATOR 4    // LED dan Pompa pakai pin yang sama
#define POMPA_AIR 4        // ✅ SAMA dengan LED_INDIKATOR (karena hardware memang sama)
#define LIMIT_BAWAH 2      
#define LIMIT_ATAS 0       

// --- STATE MACHINE & TIMERS ---
enum Fase { STANDBY, TURUN, NAIK, BACKOFF_ATAS, KEMBALI };
Fase fase = STANDBY;
bool isRunning = false;
bool isManualStop = false;
unsigned long movementStartTime = 0;
unsigned long lastProgressUpdate = 0;
unsigned long turunStartTime = 0;
unsigned long backoffStartTime = 0;

unsigned long previousReconnectAttempt = 0;

void publishMessage(const char* topic, const char* payload) {
  Serial.printf("Publishing to %s: %s\n", topic, payload);
  client.publish(topic, payload);
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) { message += (char)payload[i]; }
  Serial.printf("Message received on topic %s: %s\n", topic, message.c_str());

  if (strcmp(topic, "robot/command") == 0) {
    if (message == "start" && !isRunning) {
      Serial.println("START command received!");
      isRunning = true;
      fase = TURUN;
      movementStartTime = millis();
      turunStartTime = 0;
      isManualStop = false;
      publishMessage("robot/status", "TURUN");
    } 
    else if (message == "naik" && !isRunning) {
      Serial.println("NAIK command received!");
      isRunning = true;
      fase = NAIK;
      movementStartTime = millis();
      isManualStop = false;
      publishMessage("robot/status", "NAIK");
    } 
    else if (message == "return") {
      Serial.println("RETURN command received!");
      isRunning = true;
      fase = KEMBALI;
      movementStartTime = millis();
      isManualStop = true;
      publishMessage("robot/status", "KEMBALI");
    }
  }
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  pinMode(MOTOR_NAIK, OUTPUT);
  pinMode(MOTOR_TURUN, OUTPUT);
  pinMode(POMPA_AIR, OUTPUT);  // LED dan Pompa sama, cukup set 1x
  pinMode(LIMIT_BAWAH, INPUT_PULLUP);
  pinMode(LIMIT_ATAS, INPUT_PULLUP);

  digitalWrite(MOTOR_NAIK, LOW);
  digitalWrite(MOTOR_TURUN, LOW);
  digitalWrite(POMPA_AIR, LOW);

  setup_wifi();
  
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void reconnect() {
  if (millis() - previousReconnectAttempt > 5000) {
    previousReconnectAttempt = millis();
    Serial.print("Attempting MQTT connection...");
    if (client.connect("RobotPembersihClient")) {
      Serial.println("connected");
      client.subscribe("robot/command");
      publishMessage("robot/status", "STANDBY");
    } else {
      Serial.printf("failed, rc=%d. Will retry in 5s\n", client.state());
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect(); 
  }
  client.loop(); 

  if (isRunning) {
    bool limitBawahTertekan = (digitalRead(LIMIT_BAWAH) == LOW);
    bool limitAtasTertekan  = (digitalRead(LIMIT_ATAS) == LOW);
    unsigned long currentTime = millis();
    char progressPayload[10];

    // Kirim progress update setiap 500ms
    if (currentTime - lastProgressUpdate > 500) {
      unsigned long elapsedTime = currentTime - movementStartTime;
      int progress = 0;
      
      if (fase == TURUN) {
        progress = map(elapsedTime, 0, DURATION_PER_PHASE, 0, 50);
        if (progress > 50) progress = 50;
        sprintf(progressPayload, "P:%d", progress);
        publishMessage("robot/status", progressPayload);
      } else if (fase == NAIK) {
        progress = map(elapsedTime, 0, DURATION_PER_PHASE, 50, 100);
        if (progress > 100) progress = 100;
        sprintf(progressPayload, "P:%d", progress);
        publishMessage("robot/status", progressPayload);
      }
      
      lastProgressUpdate = currentTime;
    }

    switch (fase) {
      case TURUN:
        // Set timer TURUN sekali saja
        if (turunStartTime == 0) {
          turunStartTime = currentTime;
          Serial.println("🚀 FASE TURUN MULAI - Timer pompa+LED di-set");
        }
        
        digitalWrite(MOTOR_NAIK, LOW);
        digitalWrite(MOTOR_TURUN, HIGH);
        
        // ✅ LED & POMPA NYALA 7 DETIK BARENG (karena pin sama)
        if (currentTime - turunStartTime <= 7000) {
          digitalWrite(POMPA_AIR, HIGH);  // LED dan Pompa nyala bareng
          
          // ✅ PERUBAHAN: Print cuma 1x per detik (throttling)
          static unsigned long lastDebugPrint = 0;
          if (currentTime - lastDebugPrint >= 1000) {
            Serial.printf("💧 Pompa + LED: ON (%lu/7000 ms)\n", currentTime - turunStartTime);
            lastDebugPrint = currentTime;
          }
        } else {
          digitalWrite(POMPA_AIR, LOW);   // LED dan Pompa mati bareng
          static bool matiLogged = false;
          if (!matiLogged) {
            Serial.println("🛑 Pompa + LED: OFF - 7 detik selesai");
            matiLogged = true;
          }
        }
        
        if (limitBawahTertekan) {
          Serial.println("⬇️ LIMIT BAWAH TERTEKAN");
          digitalWrite(MOTOR_TURUN, LOW);
          digitalWrite(POMPA_AIR, LOW);
          publishMessage("robot/status", "P:50");
          publishMessage("robot/status", "REACHED_BOTTOM");
          
          delay(500);
          
          fase = NAIK;
          movementStartTime = millis();
          turunStartTime = 0;  // Reset untuk siklus berikutnya
          publishMessage("robot/status", "NAIK");
        }
        break;

      case NAIK:
        digitalWrite(POMPA_AIR, LOW);  // Mati
        digitalWrite(MOTOR_TURUN, LOW);
        digitalWrite(MOTOR_NAIK, HIGH);
        
        if (limitAtasTertekan) {
          Serial.println("⬆️ LIMIT ATAS TERTEKAN");
          digitalWrite(MOTOR_NAIK, LOW);
          fase = BACKOFF_ATAS;
          backoffStartTime = millis();
          publishMessage("robot/status", "P:100");
        }
        break;
      
      case BACKOFF_ATAS:
        digitalWrite(MOTOR_NAIK, LOW);
        digitalWrite(MOTOR_TURUN, HIGH);
        digitalWrite(POMPA_AIR, LOW);  // Mati
        
        if (currentTime - backoffStartTime > BACKOFF_DURATION) {
          digitalWrite(MOTOR_TURUN, LOW);
          digitalWrite(POMPA_AIR, LOW);
          isRunning = false;
          fase = STANDBY;
          
          if (isManualStop) {
            Serial.println("🛑 Stop manual - sending STANDBY");
            publishMessage("robot/status", "STANDBY");
            isManualStop = false;
          } else {
            Serial.println("✅ Normal completion - sending SELESAI");
            publishMessage("robot/status", "SELESAI");
          }
        }
        break;
      
      case KEMBALI:
        digitalWrite(POMPA_AIR, LOW);  // Mati
        digitalWrite(MOTOR_TURUN, LOW);
        digitalWrite(MOTOR_NAIK, HIGH);
        
        if (limitAtasTertekan) {
          digitalWrite(MOTOR_NAIK, LOW);
          fase = BACKOFF_ATAS;
          backoffStartTime = millis();
        }
        break;
      
      case STANDBY:
        digitalWrite(POMPA_AIR, LOW);  // Mati
        break;
    }
  } else {
      digitalWrite(MOTOR_NAIK, LOW);
      digitalWrite(MOTOR_TURUN, LOW);
      digitalWrite(POMPA_AIR, LOW);
  }
}