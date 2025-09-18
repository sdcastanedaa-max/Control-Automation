#include <Arduino.h>

// Pin definitions
#ifdef ESP32
  #define LED_PIN 2  // Built-in LED on ESP32
#else
  #define LED_PIN 13 // Built-in LED on Arduino Uno
#endif

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Initialize the LED pin as an output
  pinMode(LED_PIN, OUTPUT);
  
  Serial.println("Arduino/ESP32 setup complete!");
}

void loop() {
  // Blink the LED
  digitalWrite(LED_PIN, HIGH);
  Serial.println("LED ON");
  delay(1000);
  
  digitalWrite(LED_PIN, LOW);
  Serial.println("LED OFF");
  delay(1000);
}
