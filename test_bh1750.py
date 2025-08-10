# test_bh1750.py
import sys
import unittest
from unittest.mock import MagicMock

# --- Mock MicroPython environment ---
# This must be done before importing the bh1750 module
micropython_mock = MagicMock()
# The real const() function just returns its input, so we mock it with a lambda.
micropython_mock.const = lambda x: x
sys.modules['micropython'] = micropython_mock
sys.modules['machine'] = MagicMock()

import time
# Manually add the missing 'sleep_ms' function to the standard time module
time.sleep_ms = lambda ms: None # Do nothing during tests
# --- End Mock ---

# Now that the environment is mocked, we can import the driver
from bh1750 import BH1750, CONTINUOUS_HIGH_RESOLUTION, CONTINUOUS_HIGH_RESOLUTION_2, ONE_TIME_HIGH_RESOLUTION, _ADDR_LOW, _POWER_ON, _POWER_DOWN, _RESET, _MTREG_MIN, _MTREG_MAX

class MockI2C:
    """A mock I2C class to simulate machine.I2C for testing."""
    def __init__(self, scl=None, sda=None, freq=400000, available_addrs=None):
        self.available_addrs = available_addrs if available_addrs is not None else []
        self.written_data = []
        self._read_data = b''

    def scan(self):
        return self.available_addrs

    def writeto(self, addr, buf, stop=True):
        self.written_data.append(list(buf))

    def readfrom_into(self, addr, buf):
        for i in range(len(self._read_data)):
            buf[i] = self._read_data[i]

    def set_next_read_data(self, data):
        self._read_data = data

    def get_written_data(self):
        return self.written_data

    def clear_written_data(self):
        self.written_data = []


class TestBH1750(unittest.TestCase):

    def setUp(self):
        """Set up a new mock I2C for each test."""
        self.mock_i2c = MockI2C(available_addrs=[_ADDR_LOW])

    def test_initialization_autodetect(self):
        """Verify the sensor initializes and sends correct startup commands."""
        sensor = BH1750(self.mock_i2c)
        self.assertEqual(sensor.addr, _ADDR_LOW)
        written = self.mock_i2c.get_written_data()
        self.assertIn([_POWER_ON], written)
        self.assertIn([_RESET], written)
        self.assertIn([CONTINUOUS_HIGH_RESOLUTION], written)

    def test_autodetect_fails_if_no_device(self):
        """Verify that initialization fails if no sensor is found."""
        self.mock_i2c.available_addrs = []
        with self.assertRaisesRegex(OSError, "BH1750 not found on I2C bus"):
            BH1750(self.mock_i2c)

    def test_lux_calculation(self):
        """Verify the lux calculation is correct with default MTreg."""
        sensor = BH1750(self.mock_i2c)
        self.mock_i2c.set_next_read_data(b'\xd5\x54') # 54612
        self.assertAlmostEqual(sensor.lux, 45510.0, places=1)

    def test_lux_calculation_high_res_2(self):
        """Verify the lux calculation is halved for high-res mode 2."""
        sensor = BH1750(self.mock_i2c, mode=CONTINUOUS_HIGH_RESOLUTION_2)
        self.mock_i2c.set_next_read_data(b'\xd5\x54') # 54612
        self.assertAlmostEqual(sensor.lux, 22755.0, places=1)

    def test_lux_calculation_with_custom_mtreg(self):
        """Verify lux calculation scales correctly with a non-default MTreg."""
        sensor = BH1750(self.mock_i2c, mtreg=138)
        self.mock_i2c.set_next_read_data(b'\xd5\x54') # 54612
        self.assertAlmostEqual(sensor.lux, 22755.0, places=1)

    def test_set_mtreg_sends_correct_bytes(self):
        """Verify set_mtreg sends the correct two-byte sequence."""
        sensor = BH1750(self.mock_i2c)
        self.mock_i2c.clear_written_data()
        sensor.set_mtreg(120)
        written = self.mock_i2c.get_written_data()
        self.assertEqual(written, [[0x43], [0x78]])

    def test_set_mtreg_clamps_low_value(self):
        """Verify set_mtreg clamps values lower than the minimum."""
        sensor = BH1750(self.mock_i2c)
        sensor.set_mtreg(10)
        self.assertEqual(sensor.mtreg, _MTREG_MIN)

    def test_set_mtreg_clamps_high_value(self):
        """Verify set_mtreg clamps values higher than the maximum."""
        sensor = BH1750(self.mock_i2c)
        sensor.set_mtreg(300)
        self.assertEqual(sensor.mtreg, _MTREG_MAX)

    def test_power_down_sends_correct_command(self):
        """Verify power_down sends the correct I2C command."""
        sensor = BH1750(self.mock_i2c)
        self.mock_i2c.clear_written_data()
        sensor.power_down()
        self.assertEqual(self.mock_i2c.get_written_data(), [[_POWER_DOWN]])

    def test_set_mode_avoids_redundant_writes(self):
        """Verify set_mode does not send a command if the mode is unchanged."""
        sensor = BH1750(self.mock_i2c, mode=CONTINUOUS_HIGH_RESOLUTION)
        self.mock_i2c.clear_written_data()
        # Set the same mode again
        sensor.set_mode(CONTINUOUS_HIGH_RESOLUTION)
        self.assertEqual(self.mock_i2c.get_written_data(), [])

    def test_one_shot_mode_resends_command(self):
        """Verify that in one-shot mode, the mode command is sent before each read."""
        sensor = BH1750(self.mock_i2c, mode=ONE_TIME_HIGH_RESOLUTION)
        self.mock_i2c.clear_written_data()
        self.mock_i2c.set_next_read_data(b'\x00\x00')
        _ = sensor.lux
        written = self.mock_i2c.get_written_data()
        self.assertIn([ONE_TIME_HIGH_RESOLUTION], written)
        
        self.mock_i2c.clear_written_data()
        self.mock_i2c.set_next_read_data(b'\x00\x00')
        _ = sensor.lux
        written = self.mock_i2c.get_written_data()
        self.assertIn([ONE_TIME_HIGH_RESOLUTION], written)


if __name__ == '__main__':
    unittest.main()
