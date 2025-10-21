#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// --- KONFIGURASI WIFI & MQTT ---
const char* ssid = "tutus"; // Ganti dengan nama Wi-Fi Anda
const char* password = "abcd123woi"; // Ganti dengan password Wi-Fi Anda
// PENTING: Ganti dengan alamat IP WiFi komputer Anda saat ini!
const char* mqtt_server = "192.168.227.232"; 

WiFiClient espClient;
PubSubClient client(espClient);

// --- PIN DEFINITIONS ---
#define MOTOR_NAIK 16
#define MOTOR_TURUN 5
#define LED_INDIKATOR 4
#define LIMIT_BAWAH 2 // Sesuai penyesuaian terakhir
#define LIMIT_ATAS 0  // Sesuai penyesuaian terakhir

// --- STATE MACHINE ---
enum Fase { STANDBY, TURUN, NAIK, KEMBALI };
Fase fase = STANDBY;
bool isRunning = false;

// FUNGSI UNTUK MENGIRIM STATUS KE SERVER
void publishStatus(const char* status) {
  Serial.print("Publishing status: ");
  Serial.println(status);
  client.publish("robot/status", status);
}

// FUNGSI UNTUK MENERIMA PERINTAH DARI SERVER
void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) { message += (char)payload[i]; }
  Serial.printf("Message received on topic %s: %s\n", topic, message.c_str());

  if (strcmp(topic, "robot/command") == 0) {
    if (message == "start" && !isRunning) {
      Serial.println("START command received!");
      isRunning = true;
      fase = TURUN;
    } 
    // vvv --- PERUBAHAN ADA DI SINI --- vvv
    // Menambahkan logika untuk mengerti perintah "naik" dari backend
    else if (message == "naik") {
      Serial.println("NAIK command received!");
      isRunning = true;
      fase = NAIK;
    } 
    // ^^^ --- AKHIR PERUBAHAN --- ^^^
    else if (message == "stop") { // 'stop' hanya untuk darurat
      Serial.println("HARD STOP command received!");
      isRunning = false;
      fase = STANDBY;
    } else if (message == "return") { // Perintah untuk kembali ke awal
      Serial.println("RETURN command received!");
      isRunning = true;
      fase = KEMBALI;
    }
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(MOTOR_NAIK, OUTPUT);
  pinMode(MOTOR_TURUN, OUTPUT);
  pinMode(LED_INDIKATOR, OUTPUT);
  pinMode(LIMIT_BAWAH, INPUT_PULLUP);
  pinMode(LIMIT_ATAS, INPUT_PULLUP);

  digitalWrite(MOTOR_NAIK, LOW);
  digitalWrite(MOTOR_TURUN, LOW);
  digitalWrite(LED_INDIKATOR, LOW);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi Connected.");
  
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("RobotPembersihClient")) {
      Serial.println("connected");
      client.subscribe("robot/command");
      publishStatus("STANDBY");
    } else {
      Serial.printf("failed, rc=%d. Retrying in 5s\n", client.state());
      delay(5000);
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

    switch (fase) {
      case TURUN:
        digitalWrite(MOTOR_NAIK, LOW);
        digitalWrite(MOTOR_TURUN, HIGH);
        if (limitBawahTertekan) {
          digitalWrite(MOTOR_TURUN, LOW);
          isRunning = false;
          fase = STANDBY;
          publishStatus("REACHED_BOTTOM"); 
        }
        break;

      case NAIK:
        digitalWrite(MOTOR_TURUN, LOW);
        digitalWrite(MOTOR_NAIK, HIGH);
        if (limitAtasTertekan) {
          digitalWrite(MOTOR_NAIK, LOW);
          isRunning = false;
          fase = STANDBY;
          publishStatus("SELESAI");
        }
        break;
      
      case KEMBALI:
        digitalWrite(MOTOR_TURUN, LOW);
        digitalWrite(MOTOR_NAIK, HIGH);
        if (limitAtasTertekan) {
          digitalWrite(MOTOR_NAIK, LOW);
          isRunning = false;
          fase = STANDBY;
          publishStatus("STANDBY"); 
        }
        break;
      
      case STANDBY:
        digitalWrite(MOTOR_NAIK, LOW);
        digitalWrite(MOTOR_TURUN, LOW);
        break;
    }
  } else {
      digitalWrite(MOTOR_NAIK, LOW);
      digitalWrite(MOTOR_TURUN, LOW);
  }

  digitalWrite(LED_INDIKATOR, isRunning ? (millis() / 500) % 2 : LOW);
}

