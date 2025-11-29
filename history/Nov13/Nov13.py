import serial
import time

ser = serial.Serial('COM7', 115200, timeout=1)
time.sleep(2)

try:
    while True:
        ser.write('H'.encode())
        print("Relay/LED ON")
        time.sleep(10)
        ser.write('L'.encode())
        print("Relay/LED OFF")
        time.sleep(10)
except KeyboardInterrupt:
    print("Stopped by user")
finally:
    ser.close()