import serial
import time
import re

# Set up the serial port
ser = serial.Serial('COM3', 115200, timeout=1)
time.sleep(2)  # Wait for Arduino to initialize

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode().strip()  # Read a line and decode

            # Use regex to find all numbers in the received line
            numbers = re.findall(r"[-+]?\d*\.?\d+", line)
            # Print the extracted sensor values
            print(f"Extracted values: {numbers}")
except KeyboardInterrupt:
    print("Exiting...")
finally:
    ser.close()
