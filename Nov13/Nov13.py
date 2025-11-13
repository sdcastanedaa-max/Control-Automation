import serial
import time
from datetime import datetime

# Set up the serial port
ser = serial.Serial('COM3', 115200, timeout=1)
time.sleep(2)  # Wait for Arduino to initialize

try:
    while True:
        current_time = datetime.now()
        # Determine if the current second is even or odd to toggle the relay
        if current_time.second % 30 < 15:
            command = 'H' # Send HIGH
        else:
            command = 'L' # Send LOW
            ser.write(command. encode())
            # Schd the command to Arduino
            print(f"Sent command: {command} at {current_time.strftime('%H:%M:%S')}")
            time.sleep(1) # Adjust the sleep time as necessary

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    ser.close() # Close the serial connection when done