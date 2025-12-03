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
import random
import os

# DEMO MODE: Set to 1 to divide protocol durations by 10 (for testing)
DEMO_MODE = 1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SerialBoard:
    def __init__(self, port=None, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.running = False
        self.latest_temp = 0.0
        self.latest_current = 0.0

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
            
            # ✅ CRITICAL: Test Arduino handshake
            self.ser.write(b'PING\r\n')  # Send test command
            time.sleep(0.5)
            
            if self.ser.in_waiting > 0:
                response = self.ser.readline().decode().strip()
                if "OK" in response or "PONG" in response:
                    logger.info(f"✅ Arduino verified on {self.port}: {response}")
                    return True
            else:
                logger.warning(f"No response from {self.port} - not Arduino?")
            
            # No response - close and fail
            self.ser.close()
            self.ser = None
            return False
            
        except Exception as e:
            logger.error(f"Serial connection failed: {e}")
            if hasattr(self, 'ser') and self.ser:
                self.ser.close()
                self.ser = None
            return False

    def read_sensor_data(self):
        """Parse Arduino's 'Temperature: 23.45 | Current: 1.23456' format"""
        if self.ser is None or not self.ser.is_open:
            return
        
        self.running = True
        self.latest_temp = 0.0
        self.latest_current = 0.0
        
        try:
            while self.running:
                if self.ser.in_waiting > 0:
                    try:
                        line = self.ser.readline().decode().strip()
                        if "Temperature:" in line and "Current:" in line:
                            # Parse "Temperature: 23.45 | Current: 1.23456"
                            parts = line.split('|')
                            if len(parts) == 2:
                                temp_str = parts[0].split(':')[1].strip()
                                curr_str = parts[1].split(':')[1].strip()
                                self.latest_temp = float(temp_str)
                                self.latest_current = float(curr_str)
                                logger.info(f"Sensors: T:{self.latest_temp:.1f}°C C:{self.latest_current:.2f}A")
                    except Exception as e:
                        logger.error(f"Parse error: {e}")
                time.sleep(0.1)  # Match Arduino's ~5s rate
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


def fetch_protocol(
    temp: float = 22.0,
    humidity: float = 55.0,
    hair_type: str = "medium",
    porosity: str = "normal",
    towel_level: float = 80.0,
    time_priority: float = 0.5,
    temp_threshold: float = 110.0,
    current_threshold: float = 7.5,
) -> dict:
    """
    Fetch safety protocol from mock API with user-specific parameters.
    
    Args:
        temp: Room temperature in Celsius
        humidity: Room humidity (0-100%)
        hair_type: One of "fine", "medium", "thick"
        porosity: One of "low", "normal", "high"
        towel_level: Remaining wetness percentage (0-100)
        time_priority: Time priority (0.0=gentle, 1.0=fast)
        temp_threshold: Temperature threshold in Celsius
        current_threshold: Current threshold in Amperes
    """
    protocol = None
    try:
        import requests
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000/protocol")
        params = {
            "temp": temp,
            "humidity": humidity,
            "hair_type": hair_type,
            "porosity": porosity,
            "towel_level": towel_level,
            "time_priority": time_priority,
            "temp_threshold": temp_threshold,
            "current_threshold": current_threshold,
        }
            
        response = requests.get(api_url, params=params, timeout=5)
        if response.status_code == 200:
            protocol = response.json()
            print(f"✅ Protocol received: {protocol}")
        else:
            raise Exception(f"API error: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to fetch protocol: {e}")
        # Fallback protocol
        protocol = {
            "conditions": [
                {"sensor_type": "temperature", "threshold": 80.0, "duration_ms": 5000},
                {"sensor_type": "current", "threshold": 2.0, "duration_ms": 3000},
            ],
            "max_total_runtime_ms": 1800000,
        }
    
    # Apply DEMO_MODE: divide durations by 10 for faster testing
    if DEMO_MODE:
        protocol = apply_demo_mode(protocol)
        print(f"🎬 DEMO MODE applied - durations divided by 10")
    
    return protocol


def apply_demo_mode(protocol):
    """Divide protocol durations by 10 for demo/testing purposes"""
    demo_protocol = protocol.copy()
    demo_protocol["conditions"] = []
    
    for condition in protocol.get("conditions", []):
        demo_condition = condition.copy()
        if "duration_ms" in demo_condition:
            demo_condition["duration_ms"] = int(demo_condition["duration_ms"] / 10)
        demo_protocol["conditions"].append(demo_condition)
    
    if "max_total_runtime_ms" in demo_protocol:
        demo_protocol["max_total_runtime_ms"] = int(demo_protocol["max_total_runtime_ms"] / 10)
    
    return demo_protocol



def main():
    from api.safety_strategy import SafetyStrategy
    from api.protocol_calculator import fetch_room_conditions
    import random  # For simulation

    # 1. Get user inputs
    print("\n🔧 Hair Dryer Safety Protocol Setup\n")
    location_input = input("Location [default: Barcelona]: ").strip() or "Barcelona"
    hair_type_input = input("Hair thickness (fine/medium/thick) [default: medium]: ").strip().lower() or "medium"
    porosity_input = input("Hair porosity (low/normal/high) [default: normal]: ").strip().lower() or "normal"
    
    # Fixed safety thresholds based on sensor placement and hairdryer power usage
    temp_threshold = 80.0
    current_threshold = 5.0
    
    print(f"\n📊 Inputs: {hair_type_input} hair, {porosity_input} porosity, {location_input}")
    print(f"📋 Safety Thresholds: Temperature {temp_threshold}°C, Current {current_threshold}A")
    print("📡 Fetching room conditions from API...\n")

    # Fetch room conditions based on location
    temp, humidity = fetch_room_conditions(location_input)
    print(f"🌡️ Room conditions: {temp}°C, {humidity}% humidity\n")

    # Fetch protocol with location-based room conditions
    protocol = fetch_protocol(
        temp=temp,
        humidity=humidity,
        hair_type=hair_type_input,
        porosity=porosity_input,
        towel_level=80.0,
        time_priority=0.5,
        temp_threshold=temp_threshold,
        current_threshold=current_threshold,
    )

    # 1. Connect Arduino
    serial_board = SerialBoard()
    arduino_ok = serial_board.connect()
    if arduino_ok:
        logger.info("✅ Arduino connected")
        sensor_thread = threading.Thread(target=serial_board.read_sensor_data, daemon=True)
        sensor_thread.start()
    else:
        logger.warning("⚠️ SIMULATION mode")
    
    strategy = SafetyStrategy(protocol)
    
    print(f"\n🔧 STRATEGY DEPLOYED ({len(strategy.conditions)} conditions)")
    for cond in strategy.conditions:
        print(f"   {cond['sensor']}: threshold {cond['threshold']}, duration {cond['duration_ms']}ms")
    if arduino_ok:
        serial_board.send_command('H')
        strategy.relay_state = True
        print("🔌 Relay ON")

    if DEMO_MODE:
        print("🤖 DEMO MODE (Protocol durations ÷ 10)\n")
    else:
        print("🤖 FULLY AUTOMATED\n")

    # 3. Main safety loop - match real Arduino timing
    # Arduino timing: 250 RMS samples × 20ms per RMS = 5000ms (5 seconds) per output
    # DEMO_MODE only affects protocol durations, not sensor data frequency
    data_interval = 5.0
    last_data_time = time.time()
    i = 0
    
    try:
        while True:
            if not arduino_ok:
                # Simulation: sleep until next data point
                time_until_next = data_interval - (time.time() - last_data_time)
                if time_until_next > 0:
                    time.sleep(time_until_next)
                
                current_time = time.time()
                temp = 65 + (i % 8) * 3 + random.uniform(-1, 1)
                current = 5 + (i % 5) * 0.4 + random.uniform(-0.1, 0.1)
                last_data_time = current_time
                i += 1
                # Print in Arduino format (matches real hardware output)
                print(f"Temperature: {temp:.2f} | Current: {current:.5f}")
            else:
                # Real Arduino: get latest data
                temp = serial_board.latest_temp
                current = serial_board.latest_current
                if temp == 0 and current == 0:
                    # No data yet, wait a bit
                    time.sleep(0.1)
                    continue

            # Check for safety violations
            violated = strategy.check_violations(temp, current)
            
            if violated and strategy.relay_state:
                if arduino_ok:
                    serial_board.send_command('L')
                strategy.relay_state = False
                print(f"🛑 SAFETY SHUTDOWN! (T:{temp:.1f}°C exceeds {temp_threshold}°C or I:{current:.2f}A exceeds {current_threshold}A)")
                break

    except KeyboardInterrupt:
        print("\n🛑 Stopped")
    finally:
        if arduino_ok:
            serial_board.send_command('L')
            serial_board.close()


if __name__ == "__main__":
    main()
