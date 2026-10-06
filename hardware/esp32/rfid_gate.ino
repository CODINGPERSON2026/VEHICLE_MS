/*
 ============================================================================
  SMART RFID + ANPR VEHICLE GATE MANAGEMENT SYSTEM
  ESP32-WROOM-32 + RC522 RFID GATE CONTROLLER FIRMWARE
 ============================================================================
 
  RC522 Module -> ESP32-WROOM-32 Pin Connections:
  ------------------------------------------------
  1. VCC (3.3V) -> ESP32 3V3  (WARNING: DO NOT CONNECT TO 5V/VIN!)
  2. RST        -> ESP32 GPIO 22 (D22)
  3. GND        -> ESP32 GND
  4. IRQ        -> Not Connected (Leave Empty)
  5. MISO       -> ESP32 GPIO 19 (D19)
  6. MOSI       -> ESP32 GPIO 23 (D23)
  7. SCK        -> ESP32 GPIO 18 (D18)
  8. SDA (SS)   -> ESP32 GPIO 5  (D5)

  Indicators (Optional):
  ----------------------
  Green LED     -> GPIO 2  (Access Granted)
  Red LED       -> GPIO 4  (Access Denied)
  Buzzer        -> GPIO 15 (Audio Feedback)
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>

// ============================================================================
// 1. NETWORK & SERVER CONFIGURATION
// ============================================================================
const char* WIFI_SSID       = "afan";
const char* WIFI_PASSWORD   = "12345678";

// Server Configuration (PC Hotspot IP: 192.168.137.1)
const char* SERVER_URL      = "http://192.168.137.1:5000";
const char* DEVICE_ID       = "GATE01";
const char* DEVICE_API_KEY  = "dev_gate01_secret";
const char* GATE_DIRECTION  = "EXIT"; // "EXIT" for Outbound Fleet Dispatch
const char* FIRMWARE_VER    = "v1.1.0";

// Pin Definitions
#define RST_PIN             22
#define SS_PIN              5
#define LED_GREEN           2
#define LED_RED             4
#define BUZZER_PIN          15

// Timing Settings
const unsigned long SCAN_COOLDOWN_MS      = 2500;  // 2.5s cooldown
const unsigned long HEARTBEAT_INTERVAL_MS = 15000; // 15s heartbeat

// Hardware Instances
MFRC522 rfid(SS_PIN, RST_PIN);

// State Variables
unsigned long lastScanTime = 0;
String lastScannedUID = "";
unsigned long lastHeartbeatTime = 0;

// ============================================================================
// SETUP FUNCTION
// ============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=======================================================");
  Serial.println("   SMART VEHICLE GATE - ESP32 RFID RC522 CONTROLLER   ");
  Serial.println("=======================================================");

  // Initialize Indicators
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, HIGH); // Red ON during startup

  // Initialize SPI Bus & RC522 Reader
  SPI.begin(18, 19, 23, 5); // SCK, MISO, MOSI, SS
  rfid.PCD_Init();
  delay(150);

  // Set Antenna Gain to MAXIMUM for highest sensitivity
  rfid.PCD_SetAntennaGain(rfid.RxGain_max);

  // Hardware Diagnostic Check
  byte ver = rfid.PCD_ReadRegister(rfid.VersionReg);
  Serial.print("[HARDWARE] RC522 Chip Version Reg: 0x");
  Serial.println(ver, HEX);

  if (ver == 0x00 || ver == 0xFF) {
    Serial.println("\n[ERROR] RC522 READER NOT DETECTED!");
    Serial.println(">> PLEASE CHECK YOUR SPI WIRING:");
    Serial.println("   - RC522 3.3V -> ESP32 3V3");
    Serial.println("   - RC522 GND  -> ESP32 GND");
    Serial.println("   - RC522 RST  -> ESP32 GPIO 22");
    Serial.println("   - RC522 SDA  -> ESP32 GPIO 5");
    Serial.println("   - RC522 SCK  -> ESP32 GPIO 18");
    Serial.println("   - RC522 MOSI -> ESP32 GPIO 23");
    Serial.println("   - RC522 MISO -> ESP32 GPIO 19\n");
    // Rapid beep to warn user of wiring issue
    digitalWrite(BUZZER_PIN, HIGH); delay(200); digitalWrite(BUZZER_PIN, LOW);
  } else {
    Serial.println("[OK] RC522 Reader detected and ready!");
    // Short confirmation beep
    digitalWrite(BUZZER_PIN, HIGH); delay(60); digitalWrite(BUZZER_PIN, LOW);
  }

  // Connect to Wi-Fi
  connectWiFi();
  digitalWrite(LED_RED, LOW);
  
  Serial.println("\n[SYSTEM READY] Present your 13.56MHz RFID card to the reader now...");
}

// ============================================================================
// MAIN LOOP
// ============================================================================
void loop() {
  // 1. Maintain Wi-Fi Connection
  if (WiFi.status() != WL_CONNECTED) {
    digitalWrite(LED_RED, HIGH);
    connectWiFi();
    digitalWrite(LED_RED, LOW);
  }

  // 2. Periodic Heartbeat to Server
  if (millis() - lastHeartbeatTime >= HEARTBEAT_INTERVAL_MS) {
    sendHeartbeat();
    lastHeartbeatTime = millis();
  }

  // 3. Check for RFID Card Presence
  if (!rfid.PICC_IsNewCardPresent()) {
    return;
  }
  if (!rfid.PICC_ReadCardSerial()) {
    return;
  }

  // 4. Format UID as Clean Hex String (e.g. "52932A5C")
  String currentUID = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) currentUID += "0";
    currentUID += String(rfid.uid.uidByte[i], HEX);
  }
  currentUID.toUpperCase();

  // 5. Cooldown Filter to Prevent Duplicate Rapid Re-scans
  if (currentUID == lastScannedUID && (millis() - lastScanTime < SCAN_COOLDOWN_MS)) {
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
    return;
  }

  lastScannedUID = currentUID;
  lastScanTime = millis();

  Serial.println("\n>>> [RFID DETECTED] UID: " + currentUID);
  sendScanEvent(currentUID);

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}

// ============================================================================
// WI-FI CONNECTION
// ============================================================================
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("[WIFI] Connecting to SSID: ");
  Serial.println(WIFI_SSID);

  WiFi.disconnect(true);
  delay(100);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(400);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI OK] Connected! ESP32 IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n[WIFI ERROR] Connection timeout. Retrying...");
  }
}

// ============================================================================
// SEND SCAN TO FLASK SERVER
// ============================================================================
void sendScanEvent(String uid) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[ERROR] Cannot send scan: Wi-Fi offline.");
    signalDenied();
    return;
  }

  HTTPClient http;
  String url = String(SERVER_URL) + "/api/rfid/scan";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Id", DEVICE_ID);
  http.addHeader("X-Api-Key", DEVICE_API_KEY);

  String eventId = String(DEVICE_ID) + "-" + String(millis()) + "-" + uid;
  String payload = "{";
  payload += "\"uid\":\"" + uid + "\",";
  payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  payload += "\"direction\":\"" + String(GATE_DIRECTION) + "\",";
  payload += "\"event_id\":\"" + eventId + "\"";
  payload += "}";

  Serial.println("[HTTP POST] Sending tag " + uid + " to: " + url);
  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("[SERVER RESPONSE] HTTP " + String(httpCode) + ": ");
    Serial.println(response);

    if (httpCode == 200) {
      Serial.println("[RESULT] ACCESS GRANTED / GATE OPENED!");
      signalGranted();
    } else {
      Serial.println("[RESULT] ACCESS DENIED!");
      signalDenied();
    }
  } else {
    Serial.println("[HTTP ERROR] Failed to reach server: " + http.errorToString(httpCode));
    signalDenied();
  }

  http.end();
}

// ============================================================================
// HEARTBEAT
// ============================================================================
void sendHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = String(SERVER_URL) + "/api/device/heartbeat";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Id", DEVICE_ID);
  http.addHeader("X-Api-Key", DEVICE_API_KEY);

  String payload = "{\"device_id\":\"" + String(DEVICE_ID) + "\",\"api_key\":\"" + String(DEVICE_API_KEY) + "\",\"firmware_version\":\"" + String(FIRMWARE_VER) + "\"}";
  int httpCode = http.POST(payload);
  if (httpCode == 200) {
    Serial.println("[HEARTBEAT] OK (Status: ONLINE)");
  }
  http.end();
}

// ============================================================================
// AUDIO & LED SIGNALS
// ============================================================================
void signalGranted() {
  digitalWrite(LED_GREEN, HIGH);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(120);
  digitalWrite(BUZZER_PIN, LOW);
  delay(80);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(120);
  digitalWrite(BUZZER_PIN, LOW);
  delay(1500);
  digitalWrite(LED_GREEN, LOW);
}

void signalDenied() {
  digitalWrite(LED_RED, HIGH);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(500);
  digitalWrite(BUZZER_PIN, LOW);
  delay(1000);
  digitalWrite(LED_RED, LOW);
}
