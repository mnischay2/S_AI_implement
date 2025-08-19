#include <WiFi.h>

// ==== WiFi credentials ====
const char* ssid = "COMPUTER LAB 2.4";
const char* password = "IIPDELHI@1234";
const char* host = "192.168.1.106";
const uint16_t port = 5002;          // <-- Replace with server port

WiFiClient client;
 
int LDRS[] = {34};        
int numLDRs = sizeof(LDRS) / sizeof(LDRS[0]);
int read_ldr(int pin);
int read_all_ldr();
void ensureConnection();

void setup() {
  Serial.begin(115200);
  delay(200);

  analogReadResolution(12);       
  analogSetAttenuation(ADC_11db); 
  int a=0;
  for (a=0;a<numLDRs;a++){
    pinMode(LDRS[a], INPUT);
  }

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
}

void loop() {
  ensureConnection();

  // Get LDR data
  int ldrPercent = read_all_ldr();

  if (client.connected()) {
    client.println(ldrPercent);  // sends as "val\n"
    Serial.print("Sent: ");
    Serial.println(ldrPercent);
  }

  delay(1000);
}

void ensureConnection() {
  if (!client.connected()) {
    Serial.println("Connecting to server...");
    if (client.connect(host, port)) {
      Serial.println("Connected to server!");
    } else {
      Serial.println("Connection failed. Retrying...");
      delay(2000);
    }
  }
}

int read_ldr(int pin) {
  int rawValue = analogRead(pin);
  int lightPercent = map(rawValue, 0, 3000, 0, 100);
  if (lightPercent < 0) lightPercent = 0;
  if (lightPercent > 100) lightPercent = 100;
  return lightPercent;
}

int read_all_ldr() {
  int val = 0;
  for (int i = 0; i < numLDRs; i++) {
    val += read_ldr(LDRS[i]);
  }
  return val;
}
