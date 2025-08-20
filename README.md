# BH1750.py — MicroPython BH1750 Ambient Light Sensor Driver

[![Releases](https://img.shields.io/badge/Releases-%20Download-blue?logo=github)](https://github.com/MarcosCruto/bh1750.py/releases) [![Topics](https://img.shields.io/badge/topics-bh1750%20%7C%20driver%20%7C%20i2c%20%7C%20micropython-light--sensor-blue)](#)

![BH1750 sensor](https://upload.wikimedia.org/wikipedia/commons/3/3d/Light_bulb.svg)

MicroPython driver for the BH1750 ambient light sensor. The driver works on ESP32, ESP8266, RP2040 and other MicroPython boards that expose I2C. It reads lux values from the BH1750 and exposes a small API for common modes and power control.

Since the link includes a path, the bh1750.py file needs to be downloaded and executed. Get the driver file here:
https://github.com/MarcosCruto/bh1750.py/releases

Table of contents
- Features
- Hardware and wiring
- Installation
- Quick start examples
  - ESP32 / ESP8266 / RP2040 MicroPython
  - One-shot measurement
  - Continuous measurement with averaging
- API reference
- Commands and timing
- Troubleshooting
- Tests
- Contributing
- License

Features
- Small, single-file MicroPython driver.
- Support for BH1750 modes:
  - Continuous high-res (1 lx resolution)
  - Continuous high-res2 (0.5 lx resolution)
  - Continuous low-res (4 lx)
  - One-time modes for power saving
- Power on / power down and reset support.
- Works with standard machine.I2C on ESP32, ESP8266, RP2040.
- Simple API: read lux, set mode, power control.

Hardware and wiring
- BH1750 uses I2C. Connect:
  - VCC -> 3.3V (or 5V depending on module)
  - GND -> GND
  - SDA -> board SDA pin
  - SCL -> board SCL pin
- Some modules include pull-up resistors. If your board already provides pull-ups, check for double pull-ups and remove extras.
- Default I2C address: 0x23. Some modules can use 0x5C by wiring ADDR pin.

Wiring examples
- ESP32
  - SDA -> GPIO21
  - SCL -> GPIO22
- ESP8266 (NodeMCU)
  - SDA -> D2
  - SCL -> D1
- Raspberry Pi Pico (RP2040)
  - SDA -> GP0
  - SCL -> GP1

Installation
1. Download the driver file. Since the releases link has a path part, download the bh1750.py file from:
   https://github.com/MarcosCruto/bh1750.py/releases
2. Copy bh1750.py to your board's filesystem (flash) root or to your project folder.
   - Use ampy, rshell, mpfshell, Thonny, or the WebREPL.
3. Import the driver in your script or REPL:
   - import bh1750

If you cannot access the link above, check the project's Releases section in the repository to find the latest bh1750.py file.

Quick start — ESP32 / ESP8266 / RP2040 (MicroPython)
- Example: minimal script. Save as main.py on the device.

```python
from machine import Pin, I2C
import time
import bh1750

# ESP32 example pins
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)

sensor = bh1750.BH1750(i2c)   # default address 0x23
sensor.power_on()
lux = sensor.read_lux()
print("Lux:", lux)
```

One-shot measurement
- Use a one-time high resolution mode if you need a single immediate read and want to save power.

```python
from machine import Pin, I2C
import bh1750

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = bh1750.BH1750(i2c)

# One-time high resolution mode:
lux = sensor.one_time_measure()
print("One-shot lux:", lux)
```

Continuous measurement with averaging
- Read repeatedly and average to reduce noise.

```python
from machine import Pin, I2C
import bh1750
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = bh1750.BH1750(i2c)
sensor.set_mode(bh1750.CONT_H_RES_MODE)  # continuous high-res
sensor.power_on()

readings = []
for _ in range(5):
    readings.append(sensor.read_lux())
    time.sleep(0.2)

avg = sum(readings) / len(readings)
print("Average lux:", avg)
```

API reference
- Class: BH1750(i2c, address=0x23)
  - i2c: machine.I2C instance
  - address: I2C address (0x23 default)
- Methods:
  - power_on(): send power on command.
  - power_down(): send power down command to save power.
  - reset(): reset internal data (BH1750 accepts reset only in power on state).
  - set_mode(mode): set measurement mode (continuous or one-time).
  - read_lux(): read two bytes and return lux as float. In continuous modes this returns the last measurement.
  - one_time_measure(mode=ONE_TIME_H_RES_MODE): perform a one-shot measurement and return lux.
- Constants (typical names)
  - POWER_DOWN = 0x00
  - POWER_ON = 0x01
  - RESET = 0x07
  - CONT_H_RES_MODE = 0x10
  - CONT_H_RES_MODE2 = 0x11
  - CONT_L_RES_MODE = 0x13
  - ONE_TIME_H_RES_MODE = 0x20
  - ONE_TIME_H_RES_MODE2 = 0x21
  - ONE_TIME_L_RES_MODE = 0x23

Commands and timing
- Measurement timing:
  - High-res mode: ~120 ms
  - High-res2: ~120 ms, higher resolution factor 0.5 lx
  - Low-res: ~16 ms
- Conversion:
  - Read two bytes. raw = (high << 8) | low
  - lux = raw / 1.2
- Power states:
  - POWER_ON required before reset.
  - POWER_DOWN saves power; the device stops measuring.

Troubleshooting
- I2C scan finds no device:
  - Verify wiring and power.
  - Confirm SDA and SCL pins.
  - Check pull-up resistors.
  - Try proper I2C frequency (100kHz recommended).
- Readings return odd values:
  - Confirm correct address (0x23 or 0x5C).
  - Check ambient light: sensor saturates in direct strong light.
  - Ensure proper measurement mode and wait time.
- Reset has no effect:
  - Reset only works when the sensor is powered on.
  - Call power_on() before reset().

Testing
- Use a simple REPL test:
  - import bh1750
  - Create BH1750 instance and call read_lux().
- Use test scripts to verify continuous and one-shot modes.
- Compare readings to a phone lux app or a calibrated meter for accuracy checks.

Contributing
- Pull requests welcome.
- Keep changes small and test on at least one MicroPython board.
- Follow MicroPython API patterns.
- If you add features, update examples and documentation.

Releases and downloads
- Download the driver file if you prefer a single-file install. Since the link points to the repository releases, download the bh1750.py file from:
  https://github.com/MarcosCruto/bh1750.py/releases
- After download, copy bh1750.py to your board and import it from your script or REPL.

Repository topics
- bh1750 | driver | embedded-systems | esp32 | esp8266 | i2c | iot | light-sensor | micropython | rp2040 | sensor

References and links
- BH1750 datasheet (search "BH1750 datasheet" for the full spec).
- MicroPython I2C docs: machine.I2C
- Example boards: ESP32, ESP8266, Raspberry Pi Pico (RP2040)

License
- MIT License.