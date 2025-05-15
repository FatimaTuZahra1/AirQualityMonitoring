#include <esp_now.h>
#include <WiFi.h>
// ============== ThingSpeak ===========
#include "ThingSpeak.h"  // always include thingspeak header file after other header files and custom macros

#define SECRET_SSID "MySSID"      // replace MySSID with your WiFi network name
#define SECRET_PASS "MyPassword"  // replace MyPassword with your WiFi password

#define SECRET_CH_ID 000000        // replace 0000000 with your channel number
#define SECRET_WRITE_APIKEY "XYZ"  // replace XYZ with your channel write API Key

char ssid[] = SECRET_SSID;  // your network SSID (name)
char pass[] = SECRET_PASS;  // your network password
int keyIndex = 0;           // your network key Index number (needed only for WEP)
WiFiClient client;

unsigned long myChannelNumber = SECRET_CH_ID;
const char *myWriteAPIKey = SECRET_WRITE_APIKEY;

#define nexSerial Serial2

// Structure example to receive data
// Must match the sender structure
typedef struct struct_message {
  float temperature;
  int humidity;
  float pm1;
  float pm25;
  float pm10;
  int co;
} struct_message;


// Create a struct_message called dataReceived
struct_message dataReceived;

// callback function that will be executed when data is received
void OnDataRecv(const uint8_t *mac, const uint8_t *incomingData, int len) {
  memcpy(&dataReceived, incomingData, sizeof(dataReceived));
  Serial.print("Bytes received: ");
  Serial.println(len);
  Serial.print(", Temperature: ");
  Serial.print(dataReceived.temperature);
  Serial.print(", Humidity: ");
  Serial.print(dataReceived.humidity);
  Serial.print(", PM1: ");
  Serial.print(dataReceived.pm1);
  Serial.print(", PM2.5: ");
  Serial.print(dataReceived.pm25);
  Serial.print(", PM10: ");
  Serial.print(dataReceived.pm10);
  Serial.print(", CO: ");
  Serial.println(dataReceived.co);
  displayDataToNextion();  // Call the function to display data to nextion
  uploadToCloud();         // Send data to cloud
}

void setup() {
  // Initialize Serial Monitor
  Serial.begin(115200);
  nexSerial.begin(9600, SERIAL_8N1, 16, 17);  // Rx: 16, Tx: 17)

  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);

  // Init ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Once ESPNow is successfully Init, we will register for recv CB to
  // get recv packer info
  esp_now_register_recv_cb(esp_now_recv_cb_t(OnDataRecv));

  ThingSpeak.begin(client);  // Initialize ThingSpeak
}

void loop() {
}
void displayDataToNextion(){
  updateNumber("temp", dataReceived.temperature);
  updateText("pm1", dataReceived.pm1);
  updateNumber("hum", dataReceived.humidity);
  updateText("pm25", dataReceived.pm25);
  updateText("pm10", dataReceived.pm10);
  updateText("co", dataReceived.co);
  
}
void uploadToCloud(){
    // Connect or reconnect to WiFi
  if(WiFi.status() != WL_CONNECTED){
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(SECRET_SSID);
    while(WiFi.status() != WL_CONNECTED){
      WiFi.begin(ssid, pass);  // Connect to WPA/WPA2 network. Change this line if using open or WEP network
      Serial.print(".");
      delay(1000);     
    } 
    Serial.println("\nConnected.");
  }

  // set the fields with the values
  ThingSpeak.setField(1, dataReceived.temperature);
  ThingSpeak.setField(2, dataReceived.humidity);
  ThingSpeak.setField(3, dataReceived.pm1);
  ThingSpeak.setField(4, dataReceived.pm25);
  ThingSpeak.setField(4, dataReceived.pm10);
  ThingSpeak.setField(4, dataReceived.co);

  // write to the ThingSpeak channel
  int x = ThingSpeak.writeFields(myChannelNumber, myWriteAPIKey);
  if(x == 200){
    Serial.println("Channel update successful.");
  }
  else{
    Serial.println("Problem updating channel. HTTP error code " + String(x));
  }

}
void nexEndCmd() {
  nexSerial.write(0xff);
  nexSerial.write(0xff);
  nexSerial.write(0xff);
}
void updateText(char *label, String value) {
  nexSerial.print(label);
  nexSerial.print(".txt=\"");
  nexSerial.print(value);
  nexSerial.print("\"");
  nexEndCmd();
  delay(10);
  nexSerial.print(label);
  nexSerial.print(".txt=\"");
  nexSerial.print(value);
  nexSerial.print("\"");
  nexEndCmd();
  delay(10);
}
void updateText(char *label, float value) {
  nexSerial.print(label);
  nexSerial.print(".txt=\"");
  nexSerial.print(value);
  nexSerial.print("\"");
  nexEndCmd();
  delay(10);
  nexSerial.print(label);
  nexSerial.print(".txt=\"");
  nexSerial.print(value);
  nexSerial.print("\"");
  nexEndCmd();
  delay(10);
}
void updateNumber(char *label, int value) {
  nexSerial.print(label);
  nexSerial.print(".val=");
  nexSerial.print(value);
  nexSerial.print("");
  nexEndCmd();
  delay(10);
}
