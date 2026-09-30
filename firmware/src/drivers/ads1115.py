"""ADS1115 16-bit I2C ADC driver. All analog sensors depend on this."""

from micropython import const
import time

_ADDR = const(0x48)

_REG_CONV   = const(0x00)
_REG_CONFIG = const(0x01)

# Config register bits
_OS_START   = const(0x8000)
_MUX_AIN0   = const(0x4000)   # AIN0 vs GND
_MUX_AIN1   = const(0x5000)
_MUX_AIN2   = const(0x6000)
_MUX_AIN3   = const(0x7000)
_PGA_4V096  = const(0x0200)   # ±4.096 V, 1 LSB = 125 µV (inputs still limited to VDD = 3.3 V)
_PGA_2V048  = const(0x0400)   # ±2.048 V, 1 LSB = 62.5 µV
_MODE_SINGLE = const(0x0100)
_DR_128SPS  = const(0x0080)
_COMP_OFF   = const(0x0003)

_MUX = (_MUX_AIN0, _MUX_AIN1, _MUX_AIN2, _MUX_AIN3)
_PGA = {2.048: _PGA_2V048, 4.096: _PGA_4V096}   # full-scale V -> config bits

_CONV_WAIT_MS = const(9)   # 1/128 SPS + margin


class ADS1115:
    def __init__(self, i2c, addr=_ADDR):
        self._i2c = i2c
        self._addr = addr
        self._buf = bytearray(2)

    def _write_reg(self, reg, value):
        self._buf[0] = (value >> 8) & 0xFF
        self._buf[1] = value & 0xFF
        self._i2c.writeto_mem(self._addr, reg, self._buf)

    def _read_reg(self, reg):
        self._i2c.readfrom_mem_into(self._addr, reg, self._buf)
        return (self._buf[0] << 8) | self._buf[1]

    def read_raw(self, channel, fsr=2.048):
        """Return signed 16-bit ADC count for AIN<channel> vs GND at full-scale range fsr (V)."""
        cfg = _OS_START | _MUX[channel] | _PGA[fsr] | _MODE_SINGLE | _DR_128SPS | _COMP_OFF
        self._write_reg(_REG_CONFIG, cfg)
        time.sleep_ms(_CONV_WAIT_MS)
        raw = self._read_reg(_REG_CONV)
        if raw & 0x8000:
            raw -= 0x10000
        return raw

    def read_voltage(self, channel, fsr=2.048):
        """Return voltage in volts. fsr = full-scale range: 2.048 (default) or 4.096 V."""
        return self.read_raw(channel, fsr) * fsr / 32768
