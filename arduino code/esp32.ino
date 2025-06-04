#include <WiFi.h>
#include <ThingSpeak.h>
#include <DHT.h>

// WiFi credentials
const char* ssid = "Naga's A14";
const char* password = "8970269585naga";

// ThingSpeak credentials
unsigned long channelID = 2978629;
const char* apiKey = "B0L1KZ4B2A1BAKUU";

// Pin definitions
#define PULSE_PIN 34    // Pulse Sensor signal
#define DHT_PIN 14      // DHT11 data pin
#define BUZZER_PIN 13   // Buzzer positive
#define DHT_TYPE DHT11  // DHT11 sensor type

// Initialize DHT
DHT dht(DHT_PIN, DHT_TYPE);

// WiFi client
WiFiClient client;

void setup() {
  // Initialize Serial for debugging
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  
  // Start DHT
  dht.begin();
  
  // Connect to WiFi
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startTime < 15000) {
    delay(500);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWIFI_OK");
    Serial.println("IP Address: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWIFI_FAIL");
  }
  
  // Initialize ThingSpeak
  ThingSpeak.begin(client);
}

void loop() {
  // Read Pulse Sensor
  int pulse = analogRead(PULSE_PIN);
  // Basic conversion to BPM (adjust based on sensor calibration)
  float bpm = map(pulse, 0, 4095, 0, 200); // Calibrate as needed
  
  // Read DHT11 temperature and humidity
  float temp = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // Check for DHT11 errors
  if (isnan(temp) || isnan(humidity)) {
    Serial.println("Error reading DHT11");
    delay(2000);
    return;
  }
  
  // Print sensor data
  Serial.print("Pulse (BPM): ");
  Serial.print(bpm);
  Serial.print(", Temperature: ");
  Serial.print(temp);
  Serial.print(" °C, Humidity: ");
  Serial.print(humidity);
  Serial.println(" %RH");
  
  // Check for anomaly (pulse > 100, temp > 38°C)
  if (bpm > 100 || temp > 38) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(500);
    digitalWrite(BUZZER_PIN, LOW);
    Serial.println("ALERT: Anomaly detected!");
  }
  
  // Send data to ThingSpeak
  if (WiFi.status() == WL_CONNECTED) {
    ThingSpeak.setField(1, bpm);
    ThingSpeak.setField(2, temp);
    ThingSpeak.setField(3, humidity);
    int response = ThingSpeak.writeFields(channelID, apiKey);
    if (response == 200) {
      Serial.println("Data sent to ThingSpeak");
    } else {
      Serial.println("ThingSpeak Error: " + String(response));
    }
  } else {
    Serial.println("WiFi disconnected, attempting to reconnect...");
    WiFi.reconnect();
    delay(5000); // Wait before retrying
  }
  
  delay(20000); // Wait 20 seconds (ThingSpeak free tier)
}