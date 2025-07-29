#include <WiFi.h>
#include <DHT.h>
#include <Adafruit_BMP085.h>

// Wi-Fi credentials
const char* ssid = "COMPUTER LAB 2.4";
const char* password = "IIPDELHI@1234";

// Server IP and port
const char* host = "192.168.1.108";
const uint16_t port = 5001;

#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
Adafruit_BMP085 bmp;

WiFiClient client;

void setup() {
  Serial.begin(115200);
  dht.begin();
  bmp.begin();

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ Connected to WiFi!");
}

void loop() {
  if (!client.connect(host, port)) {
    Serial.println("❌ Connection to server failed");
    delay(2000);
    return;
  }

  float temp = dht.readTemperature();
  float humidity = dht.readHumidity();
  float pressure = bmp.readPressure() / 100.0F;

  if (isnan(temp) || isnan(humidity)) {
    Serial.println("Sensor read failed");
    delay(2000);
    return;
  }

  String data = String(temp, 2) + "," + String(pressure, 2) + "," + String(humidity, 2);
  client.println(data);
  Serial.println("Sent: " + data);

  client.stop();
  delay(500);  // Send every 3 seconds
}