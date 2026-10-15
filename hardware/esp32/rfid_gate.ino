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

  MH MQ-3 Alcohol Sensor -> ESP32 Pin Connections:
  -------------------------------------------------
  1. VCC (5V)   -> ESP32 VIN / 5V (Note: MQ heater coil requires 5V)
  2. GND        -> ESP32 GND
  3. AO         -> ESP32 GPIO 34 (Analog ADC1 Input, safe for 3.3V ADC)
  4. DO (Opt.)  -> ESP32 GPIO 35 (Optional Digital Threshold input)

  Indicators (Optional):
  ----------------------
  Green LED     -> GPIO 2  (Access Granted)
  Red LED       -> GPIO 4  (Access Denied / Alcohol Alert)
  Buzzer        -> GPIO 15 (Audio Feedback / Sobriety Alarm)
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

// Server Configuration
// PC Wi-Fi IP (as seen in browser 10.116.48.120:5000) with Mobile Hotspot fallback
const char* SERVER_URL_WIFI    = "http://10.116.48.120:5000";
const char* SERVER_URL_HOTSPOT = "http://192.168.137.1:5000";
String currentServerUrl        = SERVER_URL_WIFI;

const char* DEVICE_ID          = "GATE01";
const char* DEVICE_API_KEY     = "dev_gate01_secret";
const char* GATE_DIRECTION     = "EXIT"; // "EXIT" for Outbound Fleet Dispatch
const char* FIRMWARE_VER       = "v1.3.0";

// Pin Definitions
#define RST_PIN             22
#define SS_PIN              5
#define LED_GREEN           2
#define LED_RED             4
#define BUZZER_PIN          15

// Alcohol Sensor (MH-Series MQ-3)
#define MQ3_AO_PIN          34    // ADC1 Pin (Analog Input)
#define MQ3_DO_PIN          35    // Digital Comparator Input (Active LOW on LM393 module)
const int ALCOHOL_THRESHOLD = 600; // Calibrated ADC threshold for intoxication (> 600)

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

  // Initialize MQ-3 Alcohol Sensor (Analog + Digital)
  pinMode(MQ3_AO_PIN, INPUT);
  pinMode(MQ3_DO_PIN, INPUT_PULLUP);
  int baselineAlc = analogRead(MQ3_AO_PIN);
  int baselineDigital = digitalRead(MQ3_DO_PIN);
  Serial.print("[HARDWARE] MQ-3 Alcohol Sensor AO: ");
  Serial.print(baselineAlc);
  Serial.print(" | DO: ");
  Serial.println(baselineDigital);
  Serial.println(baselineAlc > ALCOHOL_THRESHOLD ? " (WARNING: Check Threshold/Warmup)" : " (Sensor Ready)");

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

  // 2.5. Continuous Real-time Alcohol Monitoring (triggers while modal is open)
  checkRealtimeAlcoholSensor();

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

  // 1. Read Driver Sobriety from MQ-3 Alcohol Sensor (multi-sample average for stability)
  long alcSum = 0;
  for (int i = 0; i < 5; i++) {
    alcSum += analogRead(MQ3_AO_PIN);
    delay(10);
  }
  int alcoholVal = alcSum / 5;
  bool isAlcoholDetected = (alcoholVal > ALCOHOL_THRESHOLD);

  Serial.println("-------------------------------------------------------");
  Serial.print("[SOBRIETY TEST] MQ-3 Alcohol ADC: ");
  Serial.print(alcoholVal);
  Serial.print(" | Threshold: ");
  Serial.println(ALCOHOL_THRESHOLD);

  if (isAlcoholDetected) {
    Serial.println("⚠️ [CRITICAL ALERT] ALCOHOL DETECTED! DRIVER IS INTOXICATED!");
    signalAlcoholAlert();
  } else {
    Serial.println("✅ [SOBRIETY OK] Driver sober. Processing RFID authorization...");
  }
  Serial.println("-------------------------------------------------------");

  HTTPClient http;
  String url = currentServerUrl + "/api/rfid/scan";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Id", DEVICE_ID);
  http.addHeader("X-Api-Key", DEVICE_API_KEY);

  String eventId = String(DEVICE_ID) + "-" + String(millis()) + "-" + uid;
  String payload = "{";
  payload += "\"uid\":\"" + uid + "\",";
  payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  payload += "\"direction\":\"" + String(GATE_DIRECTION) + "\",";
  payload += "\"event_id\":\"" + eventId + "\",";
  payload += "\"alcohol_detected\":" + String(isAlcoholDetected ? "true" : "false") + ",";
  payload += "\"alcohol_value\":" + String(alcoholVal);
  payload += "}";

  Serial.println("[HTTP POST] Sending scan data to: " + url);
  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("[SERVER RESPONSE] HTTP " + String(httpCode) + ": ");
    Serial.println(response);

    if (httpCode == 200 && !isAlcoholDetected) {
      Serial.println("[RESULT] ACCESS GRANTED / GATE OPENED!");
      signalGranted();
    } else {
      Serial.println("[RESULT] ACCESS DENIED / GATE LOCKED!");
      if (!isAlcoholDetected) {
        signalDenied();
      }
    }
  } else {
    Serial.println("[HTTP ERROR] Failed to reach server: " + http.errorToString(httpCode));
    // Try fallback URL if Wi-Fi URL failed
    if (currentServerUrl == SERVER_URL_WIFI) {
      currentServerUrl = SERVER_URL_HOTSPOT;
      Serial.println("[FAILOVER] Switched to fallback URL: " + currentServerUrl);
    }
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
  String url = currentServerUrl + "/api/device/heartbeat";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Id", DEVICE_ID);
  http.addHeader("X-Api-Key", DEVICE_API_KEY);

  int currentGas = analogRead(MQ3_AO_PIN);
  String payload = "{\"device_id\":\"" + String(DEVICE_ID) + "\",\"api_key\":\"" + String(DEVICE_API_KEY) + "\",\"firmware_version\":\"" + String(FIRMWARE_VER) + "\",\"alcohol_value\":" + String(currentGas) + "}";
  int httpCode = http.POST(payload);
  if (httpCode == 200) {
    Serial.println("[HEARTBEAT] OK (Status: ONLINE)");
  } else if (httpCode < 0) {
    if (currentServerUrl == SERVER_URL_WIFI) {
      currentServerUrl = SERVER_URL_HOTSPOT;
    } else {
      currentServerUrl = SERVER_URL_WIFI;
    }
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

// Fast SOS Alarm for Drunk Driver Detection
void signalAlcoholAlert() {
  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_RED, HIGH);
    digitalWrite(BUZZER_PIN, HIGH);
    delay(100);
    digitalWrite(LED_RED, LOW);
    digitalWrite(BUZZER_PIN, LOW);
    delay(80);
  }
}

// Continuous Real-Time Alcohol Monitoring
unsigned long lastAlcoholAlertTime = 0;
unsigned long lastSobrietySyncTime  = 0;
bool isRealtimeAlertSent = false;

void checkRealtimeAlcoholSensor() {
  int alcoholAnalog = analogRead(MQ3_AO_PIN);
  bool isAlcoholDetected = (alcoholAnalog > ALCOHOL_THRESHOLD);

  if (isAlcoholDetected) {
    // Hardware Buzzer Alarm
    signalAlcoholAlert();

    // Broadcast automatic alert to server ONCE per event
    if (!isRealtimeAlertSent) {
      isRealtimeAlertSent = true;
      lastAlcoholAlertTime = millis();
      sendAlcoholAlertToServer(alcoholAnalog);
    }
  } else {
    isRealtimeAlertSent = false;
  }

  // Continuously sync live sensor reading to Flask server (/api/device/sobriety_reading)
  unsigned long syncInterval = isAlcoholDetected ? 1000 : 1500;
  if (millis() - lastSobrietySyncTime >= syncInterval) {
    lastSobrietySyncTime = millis();
    sendSobrietyReadingToServer(alcoholAnalog, isAlcoholDetected);
  }
}

void sendSobrietyReadingToServer(int alcoholVal, bool isAlcohol) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = currentServerUrl + "/api/device/sobriety_reading";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Id", DEVICE_ID);
  http.addHeader("X-Api-Key", DEVICE_API_KEY);

  String payload = "{\"device_id\":\"" + String(DEVICE_ID) + "\",\"alcohol_detected\":" + String(isAlcohol ? "true" : "false") + ",\"alcohol_value\":" + String(alcoholVal) + "}";
  http.POST(payload);
  http.end();
}

void sendAlcoholAlertToServer(int alcoholVal) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = currentServerUrl + "/api/device/alcohol_alert";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Id", DEVICE_ID);
  http.addHeader("X-Api-Key", DEVICE_API_KEY);

  String payload = "{\"device_id\":\"" + String(DEVICE_ID) + "\",\"alcohol_detected\":true,\"alcohol_value\":" + String(alcoholVal) + "}";
  Serial.println("\n🚨 [LIVE ALARM] MQ-3 sensor alarm triggered! Broadcasting to server: " + url);
  int httpCode = http.POST(payload);
  if (httpCode > 0) {
    String response = http.getString();
    Serial.println("[SERVER ACK] Alcohol Trigger Accepted: " + response);
  } else {
    Serial.println("[SERVER ERROR] Alert failed: " + http.errorToString(httpCode));
    // Failover
    if (currentServerUrl == SERVER_URL_WIFI) {
      currentServerUrl = SERVER_URL_HOTSPOT;
    } else {
      currentServerUrl = SERVER_URL_WIFI;
    }
  }
  http.end();
}
