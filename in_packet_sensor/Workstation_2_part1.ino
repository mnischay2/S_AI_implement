#include <WiFi.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_BMP085.h>

// -----------------------------
// DHT11 Setup
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// -----------------------------
// BMP180 Setup
Adafruit_BMP085 bmp;

// -----------------------------
// Wi-Fi Credentials
const char* ssid = "COMPUTER LAB 2.4";
const char* password = "IIPDELHI@1234";

// Server IP and port (Python server IP)
const char* host = "192.168.1.105";  // Change to your PC IP
const uint16_t port = 9999;

void setup() {
  Serial.begin(115200);

  // Init Sensors
  dht.begin();
  if (!bmp.begin()) {
    Serial.println("❌ BMP180 not found. Check wiring.");
    while (1);
  }

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("🔄 Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi Connected");
}

void loop() {
  // Read DHT11
  float dhtTemp = dht.readTemperature();
  float humidity = dht.readHumidity();

  // Read BMP180
  float bmpTemp = bmp.readTemperature();         
  float pressure = bmp.readPressure() / 100.0;   

  // Check for invalid data
  if (isnan(dhtTemp) || isnan(humidity) || isnan(bmpTemp)) {
    Serial.println("❌ Failed to read from sensors!");
    delay(5000);
    return;
  }

  // Average the temperatures
  float avgTemp = (dhtTemp + bmpTemp) / 2.0;

  // Compose payload
  String payload = "TEMP_AVG=" + String(avgTemp, 1) + ",HUM=" + String(humidity, 1) + ",PRESSURE=" + String(pressure, 1);

  // Send to server
  WiFiClient client;
  if (!client.connect(host, port)) {
    Serial.println("❌ Connection to server failed");
    delay(5000);
    return;
  }

  client.println(payload);
  Serial.println("📤 Sent: " + payload);
  client.stop();

  delay(500);  // Delay between readings
}
