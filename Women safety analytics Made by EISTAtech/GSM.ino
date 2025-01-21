#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <SoftwareSerial.h>

// WiFi credentials
const char* ssid = "Auditorium AP 4";
const char* password = "audi@ap4";

// GSM module pins (adjust according to your wiring)
SoftwareSerial gsmSerial(D2, D3);  // RX, TX pins for GSM module

// GSM phone number (recipient of SOS message)
const char* sosPhoneNumber = "+91 80100 58189";  // Replace with the recipient's phone number

ESP8266WebServer server(80);  // Web server running on port 80

// Define GPIO pins
const int redLedPin = D4;    // Red LED for WiFi status
const int greenLedPin = D5;  // Green LED controlled by the switch
const int switchPin = D6;    // Switch button pin

void setup() {
  Serial.begin(9600);  // Initialize Serial communication
  gsmSerial.begin(9600); // Initialize GSM serial communication

  // Set the pin modes
  pinMode(redLedPin, OUTPUT);
  pinMode(greenLedPin, OUTPUT);
  pinMode(switchPin, INPUT_PULLUP);  // Configure the switch as INPUT with an internal pull-up resistor

  digitalWrite(redLedPin, HIGH);  // Turn LED on initially (WiFi not connected)
  digitalWrite(greenLedPin, LOW); // Ensure the green LED is off initially

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.println("\nConnecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  digitalWrite(redLedPin, LOW);  // Turn red LED off (WiFi connected)

  // Handle HTTP GET requests
  server.on("/data", HTTP_GET, handleRequest);

  // Start the server
  server.begin();
}

void sendSOS() {
  Serial.println("Threat detected, sending SOS...");
  gsmSerial.println("AT");  // Test the GSM module
  delay(1000);
  
  gsmSerial.println("AT+CMGF=1");  // Set SMS to text mode
  delay(1000);
  
  gsmSerial.print("AT+CMGS=\"");
  gsmSerial.print(sosPhoneNumber);  // Recipient phone number
  gsmSerial.println("\"");
  delay(1000);
  
  gsmSerial.println("SOS! Threat detected, sending alert.");  // The message content
  delay(1000);
  
  gsmSerial.write(26);  // Send Ctrl+Z to send the SMS
  delay(5000);  // Wait for the message to be sent
}

void handleRequest() {
  String message = server.arg("message");  // Get the message parameter from the URL
  Serial.println("Received message: " + message);
  
  // Check if the message contains the word "threat"
  if (message.indexOf("threat") != -1) {
    sendSOS();  // Send the SOS message if "threat" is found
    server.send(200, "text/plain", "SOS sent due to threat!");
  } else {
    server.send(200, "text/plain", "No threat detected.");
  }
}

void loop() {
  // Handle incoming HTTP requests
  server.handleClient();

  // Check WiFi connection and control the red LED
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi Disconnected");
    digitalWrite(redLedPin, HIGH);  // Turn the red LED on
    WiFi.begin(ssid, password);    // Attempt to reconnect
    delay(5000);                   // Wait before retrying
  } else {
    digitalWrite(redLedPin, LOW);  // Turn the red LED off
  }

  // Read the switch state and control the green LED
  if (digitalRead(switchPin) == LOW) {  // Button pressed
    Serial.println("Switch pressed, toggling green LED");
    digitalWrite(greenLedPin, !digitalRead(greenLedPin));  // Toggle green LED state
    delay(300);  // Debounce delay
  }
}
