#!/usr/bin/env python3
"""
Integrated Control System with real-time sensor monitoring
"""

import serial
import serial.tools.list_ports
import time
import logging
import threading
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SerialBoard:
    def __init__(self, port=None, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.running = False
        
    def connect(self):
        try:
            if self.port is None:
                ports = [p.device for p in serial.tools.list_ports.comports()]
                if ports:
                    self.port = ports[-1]
                    logger.info(f"Found ports: {ports}, selecting {self.port}")
                else:
                    logger.warning("No serial ports found")
                    return False
            
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)
            logger.info(f"Connected to serial board on {self.port}")
            return True
        except Exception as e:
            logger.error(f"Serial connection failed: {e}")
            return False
    
    def read_sensor_data(self):
        """Continuously read sensor data from serial"""
        if self.ser is None or not self.ser.is_open:
            return
        
        self.running = True
        try:
            while self.running:
                if self.ser.in_waiting > 0:
                    try:
                        line = self.ser.readline().decode().strip()
                        if line:
                            logger.info(f"Sensor: {line}")
                    except Exception as e:
                        logger.error(f"Error reading serial: {e}")
        except KeyboardInterrupt:
            pass
    
    def send_command(self, command):
        """Send control command"""
        if self.ser is None or not self.ser.is_open:
            logger.warning("Serial not connected")
            return False
        
        try:
            self.ser.write(command.encode())
            return True
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    def close(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()


def main():
    serial_board = SerialBoard()
    
    if not serial_board.connect():
        logger.error("Failed to connect to serial board")
        sys.exit(1)
    
    # Start sensor reading in background thread
    sensor_thread = threading.Thread(target=serial_board.read_sensor_data, daemon=True)
    sensor_thread.start()
    
    logger.info("Integrated Control System")
    logger.info("Commands: H=Relay ON, L=Relay OFF, Q=Quit")
    
    try:
        while True:
            command = input("Enter command: ").strip().upper()
            
            if command == 'Q':
                break
            elif command == 'H':
                serial_board.send_command('H')
                logger.info("Sent: Relay ON")
            elif command == 'L':
                serial_board.send_command('L')
                logger.info("Sent: Relay OFF")
            else:
                logger.warning("Invalid command. Use H, L, or Q.")
    
    except KeyboardInterrupt:
        logger.info("\nStopped by user")
    finally:
        serial_board.close()
        logger.info("Serial connection closed")


if __name__ == "__main__":
    main()
