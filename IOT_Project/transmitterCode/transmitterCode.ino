#include <esp_now.h>
#include <WiFi.h>
#include "MQ7.h"
#include "Plantower_PMS7003.h"
#include "DHT.h"


// REPLACE WITH YOUR RECEIVER MAC Address
uint8_t broadcastAddress[] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };

// Structure to send data
typedef struct struct_message {
  float temperature;
  int humidity;
  float pm1;
  float pm25;
  float pm10;
  int co;
} struct_message;

// Create a struct_message called dataToSend
struct_message dataToSend;

esp_now_peer_info_t peerInfo;


// ========== DHT Variables ==========
#define DHTPIN 14  // Digital pin connected to the DHT sensor

#define DHTTYPE DHT22  // DHT 22  (AM2302), AM2321

DHT dht(DHTPIN, DHTTYPE);

// ======== MQ-7 Variables ========== 
#define A_PIN 32
#define VOLTAGE 3.3

// init MQ7 device
MQ7 mq7(A_PIN, VOLTAGE);

// ================= PMS7003 Variables ==================
#define PMS7003_RX_PIN 19  // Connect to RDM6300 TX
#define PMS7003_TX_PIN 18  // Not used

// Use Serial1 for UART communication
HardwareSerial pmsSerial(1);
char output[256];

Plantower_PMS7003 pms7003 = Plantower_PMS7003();


// callback when data is sent
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  Serial.print("\r\nLast Packet Send Status:\t");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery Success" : "Delivery Fail");
}

void setup() {
  // Init Serial Monitor
  Serial.begin(115200);

  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);

  // Init ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Once ESPNow is successfully Init, we will register for Send CB to
  // get the status of Trasnmitted packet
  esp_now_register_send_cb(OnDataSent);

  // Register peer
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;

  // Add peer
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Failed to add peer");
    return;
  }


  Serial2.begin(9600, SERIAL_8N1, 16, 17);  // rdmSerial config for RDM6300

  pms7003.init(&Serial2);

  //pms7003.debug = true;
  Serial.println("Starting");

  dht.begin();
  Serial.println("Calibrating MQ7");
	mq7.calibrate();		// calculates R0
	Serial.println("Calibration done!");

}

void loop() {
  // Read data from PMS Sensor
  readPMSSensor();
  delay(1000); // wait for 1 second
  // Read DHT sensor
  readDHTSensor();
  delay(1000); // wait for 1 second
  // Read MQ-7  Sensor
  readMQ7Sensor(); 
  delay(100); // wait for 100 millisecond
  
  // Send message via ESP-NOW
  esp_err_t result = esp_now_send(broadcastAddress, (uint8_t *)&dataToSend, sizeof(dataToSend));

  if (result == ESP_OK) {
    Serial.println("Sent with success");
  } else {
    Serial.println("Error sending the data");
  }
  delay(2000);
}
void readDHTSensor() {
  // Reading temperature or humidity takes about 250 milliseconds!
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
  float h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  float t = dht.readTemperature();

  // Check if any reads failed and exit early (to try again).
  if (isnan(h) || isnan(t) ) {
    Serial.println(F("Failed to read from DHT sensor!"));
    dataToSend.temperature = 0;
    dataToSend.humidity = 0;
    return;
  }

  Serial.print(F("Humidity: "));
  Serial.print(h);
  Serial.print(F("%  temperature: "));
  Serial.print(t);
  Serial.println(F("°C "));
  dataToSend.temperature = t;
  dataToSend.humidity = h;
}
void readPMSSensor() {
  pms7003.updateFrame();

  if (pms7003.hasNewData()) {

    sprintf(output, "\nSensor Version: %d    Error Code: %d\n",
            pms7003.getHWVersion(),
            pms7003.getErrorCode());
    Serial.print(output);

    sprintf(output, "    PM1.0 (ug/m3): %2d     [atmos: %d]\n",
            pms7003.getPM_1_0(),
            pms7003.getPM_1_0_atmos());
    Serial.print(output);
    sprintf(output, "    PM2.5 (ug/m3): %2d     [atmos: %d]\n",
            pms7003.getPM_2_5(),
            pms7003.getPM_2_5_atmos());
    Serial.print(output);
    sprintf(output, "    PM10  (ug/m3): %2d     [atmos: %d]\n",
            pms7003.getPM_10_0(),
            pms7003.getPM_10_0_atmos());
    Serial.print(output);

    dataToSend.pm1 = pms7003.getPM_1_0();
    dataToSend.pm25 = pms7003.getPM_2_5();
    dataToSend.pm10 = pms7003.getPM_10_0();
    
  }
}
void readMQ7Sensor(){
  int coReading = mq7.readPpm();
  Serial.print("PPM = "); Serial.println(coReading);

	Serial.println(""); 	// blank new line
	dataToSend.co = coReading;
}
