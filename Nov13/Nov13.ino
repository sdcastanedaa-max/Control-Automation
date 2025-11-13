const int relayPin = D3; // Pin connected to the relay or LED

void setup() {
    Serial.begin(115200); // Start serial communication at 115200 baud
    pinMode(relayPin, OUTPUT); // Set the relay pin as an output
}

void loop() {
    if (Serial.available() > 0) { // Check if data is available to read
        char command = Serial.read(); // Read the incoming command
        if (command == 'H') {
            digitalWrite(relayPin, HIGH); // Turn on the relay or LED
            Serial.println("Relay/LED ON");
        } else if (command == 'L') {
            digitalWrite(relayPin, LOW); // Turn off the relay or LED
            Serial.println("Relay/LED OFF");
        }
    }
}
