# ESP32 Current Sensor Project

This project implements an SCT013 current sensor with ESP32 and ADS1115 ADC for accurate AC current measurement.

## Hardware Setup
- **ESP32 Dev Module** (ESP32-D0WD)
- **SCT013-30A Current Sensor** (30A/1V scale)
- **ADS1115 ADC** (I2C communication)
- **MacBook Pro M1 2020** (USB-C connection)

## Project Structure
```
/Users/para/Desktop/automation/
├── platformio.ini          # ESP32 configuration
├── src/main.cpp            # Current sensor implementation
├── monitor_serial.sh       # Serial monitoring script
└── README.md               # This file
```

## Key Features
- **RMS Current Calculation** with proper time-weighted integration
- **I2C Communication** with ADS1115 ADC
- **Real-time Current Monitoring** with noise filtering
- **Auto-calibration** for voltage offset

## Usage

### 1) Environment Setup
```bash
conda activate arduino
```

### 2) Build and Upload
```bash
pio run -e esp32dev --target upload --upload-port /dev/cu.usbserial-10
```

### 3) Monitor Serial Output
```bash
./monitor_serial.sh
```

## Serial Monitoring Issues & Solutions

### Problem: Garbage Characters After First Line
The ESP32 serial communication shows clean output initially, then displays garbage characters. This is a known ESP32 serial buffer issue.

**Symptoms:**
- First debug line: `RAW_V=1.655V RAW_I=0.161A` ✅
- Subsequent lines: `@J//k` ❌

**Root Causes:**
1. **Serial Buffer Overflow** - ESP32 sends data faster than USB-serial can handle
2. **Bootloader Interference** - ESP32 bootloader uses different baud rates
3. **USB-Serial Converter Issues** - CH340/CP2102 converter limitations
4. **I2C Communication Noise** - ADS1115 I2C operations interfere with serial

**Solutions Applied:**
1. **Serial Buffer Management** - Added `Serial.flush()` and delays
2. **Reduced Debug Frequency** - Changed from 1ms to 1-second intervals
3. **Simplified Output Format** - Removed complex debug strings
4. **Proper Baud Rate Configuration** - Always use 115200 baud

### Working Monitor Script
The `monitor_serial.sh` script handles:
- Killing existing monitor processes
- Setting correct baud rate (115200)
- Starting clean serial monitoring

**Usage:**
```bash
./monitor_serial.sh
```

### Alternative Monitoring Methods
If garbage persists, try:
1. **Arduino CLI Monitor**: `arduino-cli monitor --port /dev/cu.usbserial-10 --config baudrate=115200`
2. **Filtered Output**: `cat /dev/cu.usbserial-10 | grep -E "(RAW_|RMS=)"`
3. **Reset ESP32**: Press EN button to restart clean

## Technical Implementation

### RMS Calculation Fix
- **Before**: `rms = sqrt(sum / counter)` ❌
- **After**: `rms = sqrt(sum * frequency)` ✅

### Voltage Calibration Fix  
- **Before**: Double calibration `(voltage - calib) * (voltage - calib)` ❌
- **After**: Single calibration `voltage - calib` ✅

### Variable Naming
- `quadratic_sum_rms` → `rms_current`
- `quadratic_sum_v` → `quadratic_sum_current`

## Current Status
✅ **ESP32 Communication**: Working  
✅ **ADS1115 I2C**: Working  
✅ **Current Sensor**: Detecting real current  
✅ **RMS Calculation**: Fixed and accurate  
⚠️ **Serial Output**: Clean first line, occasional garbage thereafter  

The system functions correctly despite serial display issues. Current measurements are accurate and the sensor responds to real AC current changes.