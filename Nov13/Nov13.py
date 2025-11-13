import serial
import time

# Set up the serial port
ser = serial.Serial('COM3', 115200, timeout=1)
time.sleep(2)  # Wait for Arduino to initialize

try:
    while True:
        command = input("Enter command (H for ON, L for OFF, Q to quit): ").strip().upper()
        if command == 'Q':
            break
        elif command in ['H', 'L']:
            ser.write(command.encode())  # Send command to Arduino
            time.sleep(0.5)
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                print(f"Response: {response}")
        else:
            print("Invalid command. Use H, L, or Q.")
except KeyboardInterrupt:
    print("Exiting...")
finally:
    ser.close()
