import serial
import time
import sys

try:
    ser = serial.Serial('COM7', 115200, timeout=1)
    time.sleep(2)
except serial.SerialException as e:
    print(f"Error opening COM7: {e}")
    print("\nPossible solutions:")
    print("1. Close Arduino IDE Serial Monitor")
    print("2. Check if COM7 is the correct port")
    print("3. Reconnect the ESP32")
    sys.exit(1)

def send_command(command):
    ser.write(command.encode())
    time.sleep(0.1)
    if ser.in_waiting > 0:
        response = ser.readline().decode().strip()
        print(response)
        return response
    return None

try:
    print("Integrated Control System")
    print("Commands: H=Relay ON, L=Relay OFF, T=Read Temperature, Q=Quit")
    
    while True:
        command = input("Enter command: ").strip().upper()
        
        if command == 'Q':
            break
        elif command in ['H', 'L', 'T']:
            send_command(command)
        else:
            print("Invalid command. Use H, L, T, or Q.")
            
except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    ser.close()
    print("Serial connection closed")
