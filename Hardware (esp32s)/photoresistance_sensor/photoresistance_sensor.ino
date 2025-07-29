#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// === OLED Setup ===
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// === LDR Analog Pin ===
#define LDR_PIN 34  // Analog-capable GPIO

// === Wi-Fi Credentials ===
const char* ssid = "COMPUTER LAB 2.4";
const char* password = "IIPDELHI@1234";

// === Server (PC) Details ===
const char* host = "192.168.1.108";  // PC IP
const uint16_t port = 5002;          // Listening port

WiFiClient client;

void connectToWiFi() {
  Serial.print("📶 Connecting to WiFi ");
  WiFi.begin(ssid, password);
  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 20) {
    delay(500);
    Serial.print(".");
    retry++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ WiFi failed. Restarting...");
    ESP.restart();
  }
}

void connectToServer() {
  Serial.print("🌐 Connecting to server... ");
  if (client.connect(host, port)) {
    Serial.println("✅ Connected!");
  } else {
    Serial.println("❌ Failed to connect.");
  }
}

void setup() {
  Serial.begin(115200);

  // OLED Init
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("❌ OLED init failed");
    while (true);
  }

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("Initializing...");
  display.display();

  // WiFi Connect
  connectToWiFi();
  connectToServer();
}

void loop() {
  int ldrValue = analogRead(LDR_PIN);  // 0–4095 range
  float voltage = ldrValue * (3.3 / 4095.0); // Optional

  // === Display on OLED ===
  display.clearDisplay();
  display.setCursor(0, 0);
  display.print("LDR Value: ");
  display.println(ldrValue);
  display.print("Voltage: ");
  display.println(voltage, 2);
  display.setCursor(0, 48);
  display.print("Sending to PC...");
  display.display();

  // === Send to PC via TCP ===
  if (client.connected()) {
    String dataStr = String(ldrValue) + "\n";
    client.print(dataStr);
    Serial.print("📤 Sent: ");
    Serial.println(dataStr);
  } else {
    Serial.println("🔄 Reconnecting...");
    connectToServer();
  }

  delay(1000); // Send every second
}
