#include <WiFi.h>
#include <DHT.h>
#include <Adafruit_BMP280.h> // BMP280 instead of BMP085
// Wi-Fi credentials
const char* ssid = "COMPUTER LAB 2.4";
const char* password = "IIPDELHI@1234";
// Server IP and port
const char* host = "192.168.1.108";
const uint16_t port = 5001;
// DHT11 setup
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
// BMP280 setup
Adafruit_BMP280 bmp;

void setup() {
  Serial.begin(115200);
  delay(1000);

  dht.begin();
  if (!bmp.begin(0x76)) { // You may need to try 0x77 depending on your module
    Serial.println("Could not find BMP280 sensor!");
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
  float bmpPressure = bmp.readPressure() / 100.0F; // hPa

  if (isnan(dhtTemp) || isnan(dhtHum) || isnan(bmpTemp) || isnan(bmpPressure)) {
    Serial.println("Sensor read error");
    delay(500);
    return;
  }

  float avgTemp = dhtTemp; // use DHT temp only

  // Format: temp,pressure,humidity
  String message = String(avgTemp, 2) + "," +
                   String(bmpPressure, 2) + "," +
                   String(dhtHum, 2);

  // Send to server
  WiFiClient client;
  if (client.connect(host, port)) {
    client.println(message);
    client.stop();
    Serial.println("Sent to server:");
    Serial.println(message);
  } else {
    Serial.println("Connection to server failed.");
  }

  delay(500);
}
