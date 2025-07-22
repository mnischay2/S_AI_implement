#include <WiFi.h>
#include <DHT.h>
#include <Adafruit_BMP085.h>

// Wi-Fi credentials
const char* ssid = "COMPUTER LAB 2.4";
const char* password = "IIPDELHI@1234";

// Server IP and port
const char* host = "192.168.1.104";
const uint16_t port = 5000;

// DHT11 setup
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// BMP085 setup
Adafruit_BMP085 bmp;

void setup() {
  Serial.begin(115200);
  delay(1000);

  dht.begin();
  if (!bmp.begin()) {
    Serial.println("Could not find BMP085 sensor!");
    while (1);
  }

  // Connect to Wi-Fi
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected to WiFi.");
  Serial.print("Local IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  float dhtTemp = dht.readTemperature();
  float dhtHum = dht.readHumidity();
  float bmpTemp = bmp.readTemperature();
  float bmpPressure = bmp.readPressure() / 100.0F; // convert Pa to hPa

  String message = "";

  if (isnan(dhtTemp) || isnan(dhtHum) || isnan(bmpTemp) || isnan(bmpPressure)) {
    message = "Sensor read error\n";
  } else {
    float avgTemp = dhtTemp;
    message = "Temp: " + String(avgTemp, 2) + " C\n";
    message += "Pressure: " + String(bmpPressure, 2) + " hPa\n";
    message += "Humidity: " + String(dhtHum, 2) + " %\n";
  }

  // Send to server
  WiFiClient client;
  if (client.connect(host, port)) {
    client.print(message);
    client.stop();
    Serial.println("Sent to server:");
    Serial.print(message);
  } else {
    Serial.println("Connection to server failed.");
  }

  delay(500);
}
