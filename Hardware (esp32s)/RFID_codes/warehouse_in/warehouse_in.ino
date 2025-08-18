#include <WiFi.h>
#include <SPI.h>
#include <MFRC522.h>

// WiFi credentials
const char* ssid = "COMPUTER LAB 2.4";
const char* password = "IIPDELHI@1234";

// Server details
const char* server_ip = "192.168.1.108";
const uint16_t server_port = 5003;
WiFiClient client;

// RFID pins
#define RFID_SS_PIN    5
#define RFID_RST_PIN   22

// LED pins
#define LED_RED_PIN     25
#define LED_GREEN_PIN   26
#define LED_BLUE_PIN    27

MFRC522 mfrc522(RFID_SS_PIN, RFID_RST_PIN);
MFRC522::MIFARE_Key key;

// Data to write to Block 9 (must be 16 chars)
String block9_string = "IN              "; 

// Variables
String lastCardUID = "";
unsigned long lastCardTime = 0;
const unsigned long CARD_COOLDOWN = 3000;

// For periodic TCP sending
String lastUIDToSend = "-";
String lastBlock8ToSend = "-";
String lastBlock9ToSend = "-";
unsigned long lastSendTime = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("=== Simple RFID Reader-Writer ===");

  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_BLUE_PIN, OUTPUT);

  // Test LED
  setColor(255, 0, 0); delay(300);
  setColor(0, 255, 0); delay(300);
  setColor(0, 0, 255); delay(300);
  setColor(0, 0, 0);

  SPI.begin();
  mfrc522.PCD_Init();

  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF;

  WiFi.begin(ssid, password);
  setColor(0, 0, 255); // blue while connecting
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  connectToServer();

  Serial.println("System ready - place card near reader");
  setColor(0, 255, 0); // green for ready
}

void connectToServer() {
  Serial.println("Connecting to server...");
  if (client.connect(server_ip, server_port)) {
    Serial.println("TCP connected");

  } else {
    Serial.println("TCP connect failed");
    setColor(255, 0, 0); // red for fail
  }
}

void loop() {
  // --- CARD CHECK ---
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    String cardUID = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      if (mfrc522.uid.uidByte[i] < 0x10) cardUID += "0";
      cardUID += String(mfrc522.uid.uidByte[i], HEX);
    }
    cardUID.toUpperCase();

    // Cooldown check
    if (cardUID == lastCardUID && (millis() - lastCardTime) < CARD_COOLDOWN) {
      mfrc522.PICC_HaltA();
      mfrc522.PCD_StopCrypto1();
      return;
    }

    Serial.println("\n--- Card Detected ---");
    Serial.println("UID: " + cardUID);

    lastCardUID = cardUID;
    lastCardTime = millis();

    setColor(255, 255, 0); // yellow while processing

    String block8_data = "";
    String block9_data = "";

    if (writeBlock8(block8_data) && writeBlock9(block9_data)) {
      Serial.println("SUCCESS!");

      lastUIDToSend = cardUID;
      lastBlock8ToSend = block8_data;
      lastBlock9ToSend = block9_data;

      for (int i = 0; i < 3; i++) {
        setColor(0, 255, 0);
        delay(150);
        setColor(0, 0, 0);
        delay(150);
      }
    } else {
      Serial.println("FAILED!");
      for (int i = 0; i < 3; i++) {
        setColor(255, 0, 0);
        delay(150);
        setColor(0, 0, 0);
        delay(150);
      }
    }

    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
    setColor(0, 255, 0); // ready again
    delay(200);
  }

  // --- TCP RECONNECT ---
  if (WiFi.status() == WL_CONNECTED && !client.connected()) {
    static unsigned long lastReconnect = 0;
    if (millis() - lastReconnect > 5000) {
      lastReconnect = millis();
      connectToServer();
    }
  }

  // --- PERIODIC SEND ---
  if (client.connected() && millis() - lastSendTime >= 1000) {
    lastSendTime = millis();
    String packet = lastUIDToSend + "," + lastBlock8ToSend + "," + lastBlock9ToSend;
    client.println(packet);
    Serial.println("Sent: " + packet);

    // Reset to "-" so next tick sends dashes if no new card
    lastUIDToSend = "-";
    lastBlock8ToSend = "-";
    lastBlock9ToSend = "-";
  }

  delay(50);
}

// --- Helper functions ---

bool writeBlock8(String &data) {
  if (mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, 8, &key, &(mfrc522.uid)) != MFRC522::STATUS_OK) {
    Serial.println("Block 8 auth failed");
    return false;
  }

  byte writeBuffer[16];
  uint32_t timestamp = millis() / 1000;
  uint32_t cardID = random(1000, 9999);

  writeBuffer[0] = cardID & 0xFF;
  writeBuffer[1] = (cardID >> 8) & 0xFF;
  writeBuffer[2] = (cardID >> 16) & 0xFF;
  writeBuffer[3] = (cardID >> 24) & 0xFF;
  for (int i = 4; i < 16; i++) writeBuffer[i] = 0;

  if (mfrc522.MIFARE_Write(8, writeBuffer, 16) != MFRC522::STATUS_OK) {
    Serial.println("Block 8 write failed");
    return false;
  }

  data = "CardID:" + String(cardID);
  Serial.println("Block 8 written: " + data);
  return true;
}

bool writeBlock9(String &data) {
  if (mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, 9, &key, &(mfrc522.uid)) != MFRC522::STATUS_OK) {
    Serial.println("Block 9 auth failed");
    return false;
  }

  byte writeBuffer[16];
  String writeString = block9_string;
  while (writeString.length() < 16) writeString += " ";
  if (writeString.length() > 16) writeString = writeString.substring(0, 16);

  for (int i = 0; i < 16; i++) {
    writeBuffer[i] = writeString.charAt(i);
  }

  if (mfrc522.MIFARE_Write(9, writeBuffer, 16) != MFRC522::STATUS_OK) {
    Serial.println("Block 9 write failed");
    return false;
  }

  data = writeString;
  Serial.println("Block 9 written: " + writeString);
  return true;
}

void setColor(int red, int green, int blue) {
  analogWrite(LED_RED_PIN, 255 - red);
  analogWrite(LED_GREEN_PIN, 255 - green);
  analogWrite(LED_BLUE_PIN, 255 - blue);
}
