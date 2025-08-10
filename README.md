<p align="center">
  <img src="assets/logo.webp" alt="BH1750 Ambient Light Sensor" width="200"/>
  <br/>
  <em>Because even creatures of the night need to know when it's <em>really</em> dark.</em>
</p>

# bh1750.py

[![CI](https://github.com/adyavanapalli/bh1750.py/actions/workflows/ci.yml/badge.svg)](https://github.com/adyavanapalli/bh1750.py/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-quality, robust, and memory-efficient MicroPython driver for the BH1750 I2C ambient light sensor.

This driver is designed with best practices for embedded systems, making it suitable for resource-constrained devices like the ESP32, RP2040, and others running MicroPython.

## Features

- **Memory Efficient:** Uses `micropython.const()` and pre-allocated buffers to minimize RAM usage.
- **Robust:** Includes `try/except` blocks for I2C communication to handle potential hardware errors gracefully.
- **Idiomatic API:** Uses Python properties (`sensor.lux`) for intuitive sensor readings.
- **Flexible:** Supports all measurement modes (continuous and one-shot) and allows configuration of sensitivity (`MTreg`).
- **Auto-Detection:** Automatically scans the I2C bus to find the sensor's address (0x23 or 0x5C).
- **Power Conscious:** Provides `power_on()` and `power_down()` methods for managing power in battery-operated applications.

## Installation

This driver can be installed via `mip` from GitHub. Simply run the following command on your device:

```python
import mip
mip.install("github:adyavanapalli/bh1750.py/bh1750.py")
```

Alternatively, you can manually copy the `bh1750.py` file to the `lib/` directory on your device.

## Usage Examples

### Continuous Mode (Simple Example)

This example shows how to read from the sensor continuously. This is useful when you need frequent updates.

```python
import machine
import time
from bh1750 import BH1750, CONTINUOUS_HIGH_RESOLUTION

# Configure I2C - adjust pins as needed for your board.
# This example is for an ESP8266.
i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))

# For other boards with hardware I2C peripherals, you must provide an ID and can set the frequency.
# For ESP32: i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21), freq=400000)
# For Raspberry Pi Pico: i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8), freq=400000)

# Initialize the sensor in continuous mode
sensor = BH1750(i2c, mode=CONTINUOUS_HIGH_RESOLUTION)

print("BH1750 sensor initialized. Reading values...")
for _ in range(5):
    print(f"Luminosity: {sensor.lux:.2f} lx")
    time.sleep(1)

sensor.power_down()
print("Sensor powered down.")
```

### One-Shot Mode (Power Saving Example)

This example demonstrates how to use a "one-shot" mode, which is ideal for battery-powered applications. The sensor takes a single reading and then automatically powers down.

```python
import machine
import time
from bh1750 import BH1750, ONE_TIME_HIGH_RESOLUTION

i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))

# Initialize the sensor, setting a one-shot mode
# The driver will handle powering on and off for each reading.
sensor = BH1750(i2c, mode=ONE_TIME_HIGH_RESOLUTION)

print("Reading sensor every 5 seconds in one-shot mode...")
for _ in range(5):
    lux_value = sensor.lux
    print(f"Luminosity: {lux_value:.2f} lx (sensor is now powered down)")
    time.sleep(5)

print("Done.")
```

### A Note on `machine.I2C` Initialization

On microcontrollers like the **ESP32** and **Raspberry Pi Pico**, the first argument to `machine.I2C` (e.g., `0`) is the **ID of the hardware I2C peripheral**. These boards have dedicated silicon for I2C communication, which is fast and reliable. You can (and should) set the bus frequency using `freq=400000` to take advantage of the BH1750's support for I2C Fast Mode.

The **ESP8266**, however, uses a **software (bit-banging) implementation** for I2C because it lacks dedicated hardware. Its `I2C` constructor does not take an ID, and the actual clock speed is limited by CPU performance. While you can provide a `freq` argument, it's more of a target, and the default speed is already set to a reliable level. For this reason, it's often omitted in examples.

## API Reference

### Class `BH1750`

#### `BH1750(i2c, addr=None, mode=CONTINUOUS_HIGH_RESOLUTION, mtreg=69)`
- **`i2c`**: An initialized `machine.I2C` object.
- **`addr`**: (Optional) The I2C address of the sensor. If `None`, the driver will scan for the device at `0x23` and `0x5C`.
- **`mode`**: (Optional) The initial measurement mode. Defaults to `CONTINUOUS_HIGH_RESOLUTION`.
- **`mtreg`**: (Optional) The initial measurement time register value (sensitivity). Defaults to `69`.

### Properties

#### `sensor.lux`
- Returns the ambient light reading in lux (float).
- This property handles measurement delays and triggers new readings in one-shot modes.

#### `sensor.raw`
- Returns the raw, unscaled 16-bit sensor value (integer).

### Methods

#### `sensor.set_mode(mode)`
- Sets the measurement mode (e.g., `CONTINUOUS_LOW_RESOLUTION`).

#### `sensor.set_mtreg(value)`
- Sets the measurement time register (sensitivity). An integer between 31 and 254. Higher values provide higher sensitivity and longer measurement times.

#### `sensor.power_on()`
- Wakes the sensor from a powered-down state.

#### `sensor.power_down()`
- Puts the sensor in a low-power state.

#### `sensor.reset()`
- Resets the sensor's internal data register.

## Hardware

### Wiring

Connect the BH1750 sensor to your microcontroller as follows:

- **VCC** -> 3.3V
- **GND** -> GND
- **SCL** -> I2C SCL (Clock) pin
- **SDA** -> I2C SDA (Data) pin
- **ADDR**:
    - Connect to **GND** or leave floating for I2C address `0x23`.
    - Connect to **VCC (3.3V)** for I2C address `0x5C`.

**Note:** Ensure your I2C bus has appropriate pull-up resistors (typically 2.2kΩ to 10kΩ). Many development boards and sensor modules include them already.

### Datasheet

For more details, refer to the [BH1750FVI Datasheet](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6165/bh1750fvi-e.pdf).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.