const int relayPin = D5;
const int ledPin = D2;

void setup() {
    Serial.begin(115200);
    pinMode(relayPin, OUTPUT);
    pinMode(ledPin, OUTPUT);
}

void loop() {
    if (Serial.available() > 0) {
        char command = Serial.read();
        if (command == 'H') {
            digitalWrite(relayPin, HIGH);
            digitalWrite(ledPin, HIGH);
            Serial.println("Relay/LED ON");
        } else if (command == 'L') {
            digitalWrite(relayPin, LOW);
            digitalWrite(ledPin, LOW);
            Serial.println("Relay/LED OFF");
        }
    }
}
