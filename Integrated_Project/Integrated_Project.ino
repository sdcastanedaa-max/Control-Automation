#include <Wire.h>
#define ADS1115_ADDRESS 0x48

// ============================================================================
// HARDWARE CONFIGURATION
// ============================================================================
const int SENSOR_PIN = A1;
const int CURRENT_REF_PIN = A0;
const int TEMP_SENSOR_PIN = A3;
const int RELAY_PIN = D5;
const int LED_PIN = D2;

// ============================================================================
// SENSOR CONFIGURATION
// ============================================================================
const double TRANSFORMER_RESISTANCE = 33.3;
const double TRANSFORMER_TURNS = 1000;
const double POWER_FREQUENCY = 50.0;

// ============================================================================
// TIMING VARIABLES
// ============================================================================
unsigned long previousTime = 0;
unsigned long currentTime = 0;
unsigned long timeDelta = 0;

// ============================================================================
// RMS CALCULATION VARIABLES
// ============================================================================
double quadraticSumRms = 0.0;
int rmsSampleCounter = 0;
const int SAMPLE_DURATION = 20;

// ============================================================================
// AVERAGING VARIABLES
// ============================================================================
double accumulatedCurrent = 0.0;
int averageSampleCounter = 0;
const int AVERAGE_SAMPLE_COUNT = 250;

// ============================================================================
// ADC CONFIGURATION BUFFER
// ============================================================================
byte configWriteBuffer[3];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

void config_i2c_current() {
  Wire.begin();
  configWriteBuffer[0] = 1;
  configWriteBuffer[1] = 0b11010010; // AIN1 & GND
  configWriteBuffer[2] = 0b11100101;
  Wire.beginTransmission(ADS1115_ADDRESS);
  Wire.write(configWriteBuffer[0]);
  Wire.write(configWriteBuffer[1]);
  Wire.write(configWriteBuffer[2]);
  Wire.endTransmission();
  delay(10);
}

void config_i2c_temp() {
  configWriteBuffer[0] = 1;
  configWriteBuffer[1] = 0b11110010; // AIN3 & GND
  configWriteBuffer[2] = 0b11100101;
  Wire.beginTransmission(ADS1115_ADDRESS);
  Wire.write(configWriteBuffer[0]);
  Wire.write(configWriteBuffer[1]);
  Wire.write(configWriteBuffer[2]);
  Wire.endTransmission();
  delay(10);
}

float read_voltage() {
  Wire.beginTransmission(ADS1115_ADDRESS);
  Wire.write(0x00);
  Wire.endTransmission();
  Wire.requestFrom(ADS1115_ADDRESS, 2);
  int16_t result = Wire.read() << 8 | Wire.read();
  Wire.endTransmission();
  float voltage = result * 4.096 / 32768.0;
  return voltage;
}

float read_temperature() {
   int rawValue = analogRead(TEMP_SENSOR_PIN);
   float voltage = rawValue * (3.3 / 4095.0); // ESP32 ADC: 0-4095 for 0-3.3V
   float temperature = voltage * 100.0; // LM35: 10mV/°C
   return temperature;
 }

// ============================================================================
// SETUP FUNCTION
// ============================================================================

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  
  Serial.begin(115200);
  Wire.begin();
  config_i2c_current();
}

// ============================================================================
// LOOP FUNCTION
// ============================================================================

void loop() {
  // Handle serial commands
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == 'H') {
      digitalWrite(RELAY_PIN, HIGH);
      digitalWrite(LED_PIN, HIGH);
      Serial.println("Relay/LED ON");
    } else if (command == 'L') {
      digitalWrite(RELAY_PIN, LOW);
      digitalWrite(LED_PIN, LOW);
      Serial.println("Relay/LED OFF");
    }
    }

  // Current sensor measurement
  currentTime = micros();
  timeDelta = currentTime - previousTime;
  
  if (timeDelta >= 1000) {
    previousTime = currentTime;
    double instantVoltage = read_voltage() - 1.65;
    double instantCurrent = instantVoltage * 30;
    quadraticSumRms = quadraticSumRms + (instantCurrent * instantCurrent * (timeDelta / 1000000.0));
    rmsSampleCounter++;
  }
  
  if (rmsSampleCounter >= SAMPLE_DURATION) {
    double currentRms = sqrt(POWER_FREQUENCY * quadraticSumRms);
    rmsSampleCounter = 0;
    quadraticSumRms = 0;
    
    if (currentRms <= 0.1) {
      currentRms = 0;
    }
    
    accumulatedCurrent += currentRms;
    averageSampleCounter++;
  }
  
  if (averageSampleCounter >= AVERAGE_SAMPLE_COUNT) {
     double filteredCurrentRms = accumulatedCurrent / ((double)averageSampleCounter);
     averageSampleCounter = 0;
     accumulatedCurrent = 0;
     
     float temperature = read_temperature();
     Serial.print("Temperature: ");
     Serial.print(temperature, 2);
     Serial.print(" | ");
     Serial.print("Current: ");
     Serial.println(filteredCurrentRms, 5);
   }
}
