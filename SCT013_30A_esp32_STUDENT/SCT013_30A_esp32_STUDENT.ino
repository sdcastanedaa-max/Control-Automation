#include <Wire.h>
#define ADS1115_ADDRESS 0x48

// ============================================================================
// HARDWARE CONFIGURATION
// ============================================================================
// Pin definitions for sensor connections
const int SENSOR_PIN = A1;       // Current sensor analog input pin
const int REF_PIN = A2;          // Reference voltage pin
const int RELAY_PIN = D5;        // Relay control pin

// ============================================================================
// SENSOR CONFIGURATION
// ============================================================================
// Transformer parameters for SCT013-30A current sensor
const double TRANSFORMER_RESISTANCE = 33.3;  // Resistance in ohms (Model 30A: 33.3Ω, Model 50A: 20Ω)
const double TRANSFORMER_TURNS = 1000;       // Number of turns between primary and secondary windings
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

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================
// Function created to partition the problem in smaller parts

void config_i2c() {
  // Initialize I2C communication
  Wire.begin();
  
  // Configure ADS1115 ADC:
  // - Set config register and start conversion
  // - AIN1 and GND inputs
  // - 4.096V full scale range
  // - 128 SPS data rate
  configWriteBuffer[0] = 1;  // Config register address
  
  // Configuration byte 1 (0xC2):
  // Bit 15: Flag bit for single shot
  // Bits 14-12: Input selection (101 = ANC1 & GND)
  //   Options: 100 = ANC0, 101 = ANC1, 110 = ANC2, 111 = ANC3
  // Bits 11-9: Amp gain (010 = default, 001 = P19)
  // Bit 8: Operational mode (0 = Continuous, 1 = Single-shot)
  configWriteBuffer[1] = 0b11010010;
  
  // Configuration byte 2 (0x85, 869 SPS):
  // Bits 7-5: Data rate (100 = 128 SPS)
  // Bits 4-0: Comparator functions (see spec sheet)
  configWriteBuffer[2] = 0b11100101;
  
  // Send configuration to ADS1115 via I2C
  Wire.beginTransmission(ADS1115_ADDRESS);
  Wire.write(configWriteBuffer[0]);
  Wire.write(configWriteBuffer[1]);
  Wire.write(configWriteBuffer[2]);
  Wire.endTransmission();
  delay(500);
}

float read_voltage() {
  // Read conversion register from ADS1115
  Wire.beginTransmission(ADS1115_ADDRESS);
  Wire.write(0x00);  // Conversion register address
  Wire.endTransmission();
  Wire.requestFrom(ADS1115_ADDRESS, 2);
  
  // Combine two bytes into 16-bit signed integer
  int16_t result = Wire.read() << 8 | Wire.read();
  Wire.endTransmission();

  // Convert ADC result to voltage
  // Formula: (ADC_value / max_ADC_value) * reference_voltage
  float voltage = result * 4.096 / 32768.0;
  
  return voltage;  // Returns voltage in volts
}

// ============================================================================
// SETUP FUNCTION
// ============================================================================
// Function that runs once on startup

void setup() {
  // Configure relay pin as output and set to HIGH (relay off)
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);
  
  // Initialize serial communications for debugging
  Serial.begin(115200);
  
  // Initialize I2C communications and configure ADC
  config_i2c();
}

// ============================================================================
// LOOP FUNCTION
// ============================================================================
// Function that runs cyclically indefinitely

void loop() {
  // Get current time and calculate time difference since last measurement
  currentTime = micros();
  timeDelta = currentTime - previousTime;
  
  // EVERY 1 MILLISECOND: Read ADC and calculate instantaneous current for RMS
  if (timeDelta >= 1000) {
    previousTime = currentTime;

    // Read voltage from sensor and apply calibration offset
    // Note: Calibration method should be explained in deliverable
    double instantVoltage = read_voltage() - 1.65;
    
    // Convert voltage measurement to current (30A full scale)
    double instantCurrent = instantVoltage * 30;
    
    // Accumulate quadratic sum for RMS calculation over one power cycle (20ms at 50Hz)
    quadraticSumRms = quadraticSumRms + (instantCurrent * instantCurrent * (timeDelta / 1000000.0));
    rmsSampleCounter++;
  }
  
  // EVERY POWER CYCLE (20 samples): Calculate RMS current
  if (rmsSampleCounter >= SAMPLE_DURATION) {
    // Calculate RMS of the last power cycle
    double currentRms = sqrt(POWER_FREQUENCY * quadraticSumRms);
    
    // Reset accumulation values for next power cycle
    rmsSampleCounter = 0;
    quadraticSumRms = 0;
    
    // Filter out base noise/error (values below 0.1A set to zero)
    if (currentRms <= 0.1) {
      currentRms = 0;
    }
    
    // Accumulate RMS values for averaging
    accumulatedCurrent += currentRms;
    averageSampleCounter++;
  }
  
  // EVERY 250 POWER CYCLES (~5 seconds): Calculate and print average RMS
  if (averageSampleCounter >= AVERAGE_SAMPLE_COUNT) {
    // Calculate average RMS current over the measurement period
    double filteredCurrentRms = accumulatedCurrent / ((double)averageSampleCounter);
    
    // Reset accumulation values for next averaging period
    averageSampleCounter = 0;
    accumulatedCurrent = 0;
    
    // Print filtered current RMS value
    Serial.print("filteredCurrentRms: ");
    Serial.println(filteredCurrentRms, 5);
  }
}
