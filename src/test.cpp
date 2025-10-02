#include <Arduino.h>

// Configure onboard LED and serial baud per board
#if defined(ESP32)
  #ifndef LED_BUILTIN
  #define LED_BUILTIN 2
  #endif
  static const unsigned long SERIAL_BAUD = 115200;
#else
  #ifndef LED_BUILTIN
  #define LED_BUILTIN 13
  #endif
  static const unsigned long SERIAL_BAUD = 9600;
#endif

void setup() {
  Serial.begin(SERIAL_BAUD);
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.println("Setup complete. Blinking onboard LED...");
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("LED ON");
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("LED OFF");
  delay(2000);
}
