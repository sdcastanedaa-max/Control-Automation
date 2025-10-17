# ESP32 Current Sensor Project

SCT013 current sensor with ESP32 and ADS1115 ADC.

## Hardware
- ESP32 Dev Module
- SCT013-30A Current Sensor  
- ADS1115 ADC (I2C)

## Usage
```bash
conda activate arduino
pio run -e esp32dev --target upload --upload-port /dev/cu.usbserial-10
./monitor_serial.sh
```

## Status
✅ ESP32 Communication: Working  
✅ ADS1115 I2C: Working  
✅ Current Sensor: Detecting real current  
❌ Serial Monitor: NOT WORKING - shows garbage after first line  

Monitor script still needs debugging for garbage character issue.