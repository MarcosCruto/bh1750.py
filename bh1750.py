# bh1750.py - MicroPython BH1750 ambient light sensor driver.
#
# A production-quality driver that prioritizes memory efficiency, robustness,
# and an idiomatic API. It is suitable for resource-constrained devices.
#
# Copyright (c) 2025 Anand Dyavanapalli
#
# SPDX-License-Identifier: MIT

from micropython import const
from machine import I2C
import time

# BH1750 I2C addresses
_ADDR_LOW = const(0x23)  # ADDR pin low or floating
_ADDR_HIGH = const(0x5C) # ADDR pin high (3.3V)

# Commands
_POWER_DOWN = const(0x00)
_POWER_ON = const(0x01) # Waits for the measurement command
_RESET = const(0x07)      # Resets the data register value

# The amount of time to wait in milliseconds after issuing a command
_COMMAND_DELAY_MS = const(5)

# Measurement Time Register (MTreg) values
_MTREG_MIN = const(31)
_MTREG_MAX = const(254)
_MTREG_DEFAULT = const(69)

# Measurement Modes
CONTINUOUS_HIGH_RESOLUTION = const(0x10)   # 1.0 lx resolution, ~120-160 ms
CONTINUOUS_HIGH_RESOLUTION_2 = const(0x11) # 0.5 lx resolution, ~120-160 ms
CONTINUOUS_LOW_RESOLUTION = const(0x13)    # 4.0 lx resolution, ~16-24 ms
ONE_TIME_HIGH_RESOLUTION = const(0x20)     # 1.0 lx resolution, ~120-160 ms
ONE_TIME_HIGH_RESOLUTION_2 = const(0x21)   # 0.5 lx resolution, ~120-160 ms
ONE_TIME_LOW_RESOLUTION = const(0x23)      # 4.0 lx resolution, ~16-24 ms

class BH1750:
    """
    MicroPython driver for the BH1750 ambient light sensor.

    This driver is designed for memory efficiency and robustness, making it
    suitable for production use on resource-constrained microcontrollers.

    Example:
        import machine
        import time
        from bh1750 import BH1750

        i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8))
        sensor = BH1750(i2c)

        while True:
            print(f"Luminosity: {sensor.lux:.2f} lx")
            time.sleep(1)
    """
    def __init__(self, i2c: I2C, addr: int = None, mode: int = CONTINUOUS_HIGH_RESOLUTION, mtreg: int = _MTREG_DEFAULT):
        self.i2c = i2c
        self.addr = addr if addr is not None else self._autodetect_addr()

        # Pre-allocate buffers for memory efficiency
        self._write_buf = bytearray(1)
        self._read_buf = bytearray(2)

        self.power_on()
        self.reset()

        self.set_mtreg(mtreg)
        self.set_mode(mode, force=True)

    def _autodetect_addr(self) -> int:
        """Scans the I2C bus to find the sensor's address."""
        try:
            addrs = self.i2c.scan()
            if _ADDR_LOW in addrs:
                return _ADDR_LOW
            if _ADDR_HIGH in addrs:
                return _ADDR_HIGH
            raise OSError("BH1750 not found on I2C bus")
        except OSError as e:
            raise OSError(f"I2C scan failed: {e}")

    def _write_cmd(self, cmd: int):
        """Writes a single command byte to the sensor."""
        try:
            self._write_buf[0] = cmd
            self.i2c.writeto(self.addr, self._write_buf)
        except OSError as e:
            raise OSError(f"BH1750 I2C write failed: {e}")

    def power_on(self):
        """Powers on the sensor."""
        self._write_cmd(_POWER_ON)
        time.sleep_ms(_COMMAND_DELAY_MS)

    def power_down(self):
        """Powers down the sensor, reducing power consumption."""
        self._write_cmd(_POWER_DOWN)

    def reset(self):
        """Resets the sensor's data register. Valid only when powered on."""
        self._write_cmd(_RESET)
        time.sleep_ms(_COMMAND_DELAY_MS)

    def set_mtreg(self, mtreg: int):
        """
        Sets the measurement time register (MTreg).

        Per the datasheet, this value adjusts the sensor's sensitivity and
        measurement time. Higher values increase sensitivity and duration.

        Args:
            mtreg: An integer between 31 and 254.
        """
        self.mtreg = max(_MTREG_MIN, min(mtreg, _MTREG_MAX))
        # Two-part write, as per datasheet:
        high_byte = 0b0100_0000 | (self.mtreg >> 5)    # 01000_MT[7:5]
        low_byte = 0b0110_0000 | (self.mtreg & 0b0001_1111) # 011_MT[4:0]
        self._write_cmd(high_byte)
        self._write_cmd(low_byte)

    def set_mode(self, mode: int, force: bool = False):
        """
        Sets the measurement mode.

        In continuous modes, the sensor takes measurements constantly. In
        one-shot modes, it takes a single measurement and then powers down.

        Args:
            mode: The desired measurement mode constant.
            force: If True, sends the command even if the mode is unchanged.
        """
        if self.mode == mode and not force:
            return
        self.mode = mode
        self._write_cmd(self.mode)

    @property
    def raw(self) -> int:
        """
        Reads the raw 16-bit sensor value.
        
        Returns:
            The raw, unscaled sensor reading.
        """
        try:
            self.i2c.readfrom_into(self.addr, self._read_buf)
            return (self._read_buf[0] << 8) | self._read_buf[1]
        except OSError as e:
            raise OSError(f"BH1750 I2C read failed: {e}")

    @property
    def lux(self) -> float:
        """
        Reads the ambient light in lux.

        This property handles the necessary delays and commands for the
        configured measurement mode. For one-shot modes, it triggers a new
        measurement on each call.

        Returns:
            The luminosity in lux.
        """
        # For one-shot modes, trigger a new measurement each time
        is_one_shot = (self.mode & 0xF0) == 0x20
        if is_one_shot:
            self.set_mode(self.mode, force=True)

        # Wait for the measurement to complete. The datasheet specifies a max
        # measurement time of 180ms for high-res modes and 24ms for low-res.
        base_ms = 180 if self.mode in (CONTINUOUS_HIGH_RESOLUTION, CONTINUOUS_HIGH_RESOLUTION_2, ONE_TIME_HIGH_RESOLUTION, ONE_TIME_HIGH_RESOLUTION_2) else 24
        wait_ms = int(base_ms * (self.mtreg / _MTREG_DEFAULT))
        time.sleep_ms(wait_ms)

        # Read the raw value and scale it to lux
        raw_val = self.raw
        
        # Lux calculation based on datasheet: lux = (raw / 1.2) * (default_mtreg / current_mtreg)
        # The scaling factor of 1.2 is for when MTreg is at its default of 69.
        lux = (raw_val / 1.2) * (_MTREG_DEFAULT / self.mtreg)

        # Per datasheet, the result must be divided by 2 for H-Resolution Mode 2.
        if self.mode in (CONTINUOUS_HIGH_RESOLUTION_2, ONE_TIME_HIGH_RESOLUTION_2):
            lux /= 2.0

        return lux