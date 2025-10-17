#!/bin/bash
# ESP32 Serial Monitor Script
# Usage: ./monitor_serial.sh

# Kill any existing monitors
pkill -f "cat.*cu.usbserial\|hexdump.*cu.usbserial\|python.*serial\|arduino-cli.*monitor" || true

# Set correct baud rate for ESP32
stty -f /dev/cu.usbserial-10 115200 cs8 -cstopb -parenb

# Start monitoring
echo "Starting ESP32 serial monitor at 115200 baud..."
echo "Press Ctrl+C to stop"
cat /dev/cu.usbserial-10
