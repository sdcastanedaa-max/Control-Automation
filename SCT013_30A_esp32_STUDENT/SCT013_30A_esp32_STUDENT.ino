#include <Wire.h>
#define ADS1115_ADDRESS 0x48

// ============================================================================
// HARDWARE CONFIGURATION
// ============================================================================
// Pin definitions for sensor connections
const int SENSOR_PIN = A1;      // Current sensor analog input pin
const int REF_PIN = A2;          // Reference voltage pin
const int RELAY_PIN = D5;        // Relay control pin

// ============================================================================
// SENSOR CONFIGURATION
// ============================================================================
// Transformer parameters for SCT013-30A current sensor
const double TRANSFORMER_RESISTANCE = 33.3;  // Resistance in ohms (Model 30A: 33.3Ω, Model 50A: 20Ω)
double transformerTurns = 1000;              // Number of turns between primary and secondary windings
const double POWER_FREQUENCY = 50.0;         // AC power frequency in Hz

// ============================================================================
// TIMING VARIABLES
// ============================================================================
unsigned long previousTime = 0;   // Timestamp of previous measurement in microseconds
unsigned long currentTime = 0;    // Current timestamp in microseconds
unsigned long timeDelta = 0;      // Time difference between measurements in microseconds
unsigned long timeNow = 0;        // Reserved for future use
unsigned long readingTime = 0;    // Reserved for future use
unsigned long readingTimeDelta = 0; // Reserved for future use
unsigned long timer1 = 0;         // Reserved for future use
unsigned long timer2 = 0;         // Reserved for future use

// ============================================================================
// RMS CALCULATION VARIABLES
// ============================================================================
// Variables for calculating RMS current over one power cycle (20ms at 50Hz)
double quadraticSumRms = 0.0;              // Accumulated sum of squared instantaneous currents
double quadraticSumV = 0.0;                // Reserved for future use - voltage quadratic sum
int rmsSampleCounter = 0;                  // Counter for samples in current power cycle
const int SAMPLE_DURATION = 20;            // Number of samples per power cycle (20ms / 1ms sampling)

// ============================================================================
// AVERAGING VARIABLES
// ============================================================================
// Variables for calculating average RMS over multiple power cycles
double accumulatedCurrent = 0.0;           // Accumulator for RMS values
int averageSampleCounter = 0;              // Counter for number of RMS values accumulated
const int AVERAGE_SAMPLE_COUNT = 250;      // Number of power cycles for averaging (~5 seconds)

// ============================================================================
// CALIBRATION VARIABLES
// ============================================================================
bool isFirstRun = true;                    // Flag to indicate first program execution
double calibrationVoltageAccumulator = 0;  // Accumulator for voltage calibration
double calibrationVoltage = 0;             // Calibrated voltage offset value

// ============================================================================
// GENERAL PURPOSE VARIABLES
// ============================================================================
int loopCounter = 0;                       // Reserved for future use - general loop counter

// ============================================================================
// ADC CONFIGURATION BUFFER
// ============================================================================
// I2C write buffer for ADS1115 ADC configuration
byte configWriteBuffer[3];

// --- Helper functions: Function created to partition the problem in smaller parts ---
void config_i2c() {
  Wire.begin(); // begin I2C
  // ASD1115
  // set config register and start conversion
  // ANC1 and GND, 4.096v, 128s/
  configWriteBuffer[0] = 1; // config register is 1

  configWriteBuffer[1] = 0b11010010; // 0xC2 single shot off <== ORIGINAL - single conversion/ AIN1 & GND/ 4.096V/ Continuous (0)

  // bit 15 flag bit for single shot
  // Bits 14-12 input selection:
  // 100 ANC0; 101 ANC1; 110 ANC2; 111 ANC3
  // Bits 11-9 Amp gain. Default to 010 here 001 P19
  // Bit 8 Operational mode of the ADS1115.
  // 0 : Continuous conversion mode
  // 1 : Power-down single-shot mode (default)
  configWriteBuffer[2] = 0b11100101; // bits 7-0 0x85 //869 SPS

  // Bits 7-5 data rate default to 100 for 128SPS
  // Bits 4-0 comparator functions see spec sheet.
  // setup ADS1115
  Wire.beginTransmission(ADS1115_ADDRESS); // ADC
  Wire.write(configWriteBuffer[0]);
  Wire.write(configWriteBuffer[1]);
  Wire.write(configWriteBuffer[2]);
  Wire.endTransmission();
  delay(500);
}

float read_voltage() {
  //unsigned long start = micros();
  // read conversion register
  Wire.beginTransmission(ADS1115_ADDRESS);
  Wire.write(0x00); // Conversion register
  Wire.endTransmission();
  Wire.requestFrom(ADS1115_ADDRESS, 2);
  int16_t result = Wire.read() << 8 | Wire.read(); // Mount the 2 byte value
  Wire.endTransmission();

  //unsigned long end = micros();
  //Serial.print("ADC Read Time (us): ");
  // Serial.println(end - start);
  // Convert result to voltage
  float voltage = result * 4.096 / 32768.0; // Raw adc reference voltage configured / maximum adc value
  //Serial.print("Vref: ");
  //Serial.println(voltage);
  return voltage; // Voltage in V
}

// --- setup Function: Function that runs once on startup ---
void setup() {
  // relay
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);
  // Initialize serial communications
  Serial.begin(115200);
  // Initialize IIC communications
  config_i2c();
}

// --- loop Function: Function that runs cyclically indefinitely ---
void loop() {
  // Read the time in microseconds since the Arduino started
  currentTime = micros();
  // Calculate the time difference between the current time and the last time the instantaneous current was updated
  timeDelta = currentTime - previousTime;
  // EVERY 1 MILLISECOND, READ ADC AND CALCULATE THE INSTANTANEOUS CURRENT TO CALCULATE THE RMS
  if (timeDelta >= 1000) {
    // Update the time record with the current time
    previousTime = currentTime;

    // Read the voltage from the sensor
    double instantVoltage = read_voltage() - 1.65; // in deliverable explain how you calibrate this
    // Serial.print("Vinst: ");
    // Serial.println(instantVoltage);
    // Convert voltage in shunt to current measurement
    double instantCurrent = instantVoltage * 30;
    // Accumulate quadratic sum (20ms for 1 T, 50Hz)
    quadraticSumRms = quadraticSumRms + (instantCurrent * instantCurrent * (timeDelta / 1000000.0));
    rmsSampleCounter++;
  }
  // EVERY POWER CYCLE (20 ACCUMULATED VALUES), CALCULATE RMS
  if (rmsSampleCounter >= SAMPLE_DURATION) {
    // Take the square root to calculate the RMS of the last power cycle
    double currentRms = sqrt(POWER_FREQUENCY * quadraticSumRms);
    // Reset accumulation values to calculate the RMS of the last power cycle
    rmsSampleCounter = 0;
    quadraticSumRms = 0;
    // Filter base error
    if (currentRms <= 0.1) {
      currentRms = 0;
    }
    // Accumulate RMS current values to calculate the average RMS
    accumulatedCurrent += currentRms;
    averageSampleCounter++;
    //Serial.print("Irms: ");
    //Serial.println(currentRms,5); //for locating error in the code
  }
  // EVERY 250 POWER CYCLES (approximately 5 seconds), CALCULATE THE AVERAGE RMS
  if (averageSampleCounter >= AVERAGE_SAMPLE_COUNT) {
    // Calculate the average of the RMS current
    double filteredCurrentRms = accumulatedCurrent / ((double)averageSampleCounter);
    // Reset accumulation values to calculate the average RMS
    averageSampleCounter = 0;
    accumulatedCurrent = 0;
    // Print the filtered current
    Serial.print("Irms_filt: ");
    Serial.println(filteredCurrentRms, 5);
  }
}
