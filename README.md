# Automation

This repository contains automation scripts and tooling.

## Setup

- Install Miniconda and ensure `conda` is available.
- Create and activate an environment as needed.

## Git

- Main branch is `main`.
- Use feature branches and pull requests.

## Usage (Arduino/ESP32 with PlatformIO)

### Prerequisites

- `conda` installed and initialized
- USB cable for your board (Arduino Uno or ESP32)

### 1) Activate environment

```bash
conda activate arduino
```

### 2) Build

- Arduino Uno:
```bash
pio run -e uno
```

- ESP32 (devkit):
```bash
pio run -e esp32dev
```

### 3) Upload firmware

First, plug in your board and find the port:
```bash
pio device list
```

Optionally set `upload_port` and `monitor_port` in `platformio.ini` under the desired environment.

- Arduino Uno:
```bash
pio run -e uno -t upload
```

- ESP32:
```bash
pio run -e esp32dev -t upload
```

### 4) Open Serial Monitor

- Arduino Uno (9600 baud):
```bash
pio device monitor -e uno
```

- ESP32 (115200 baud):
```bash
pio device monitor -e esp32dev
```

### Notes

- Example app is in `src/main.cpp` and blinks the onboard LED on both Uno and ESP32.
- If upload fails on ESP32, press and hold BOOT (if present) during the initial upload attempt.
- You can also compile/upload with Arduino CLI if preferred.

