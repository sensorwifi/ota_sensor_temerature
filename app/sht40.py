from comm_util import CommUtil
from time import sleep

MEASURE_CMDS = [
    0xFD, # high precision
    0xF6, # medium precision
    0xE0  # low precision
]

HEATER_CMDS = [
    0x39, 0x32, # high power 1s / 0.1s
    0x2F, 0x24, # medium power 1s / 0.1s
    0x1E, 0x15  # low power 1s / 0.1s
]

_SHT40_ADDR = const(0x44)

class SHT40(CommUtil):
    def __init__(self, i2c, check_crc=False):
        super().__init__(i2c, check_crc)

    def read_serial(self):
        """ get the serial number (32bit integer) """
        self._i2c_write(_SHT40_ADDR, [0x89])
        sleep(0.01)
        raw = self._i2c_read(_SHT40_ADDR, 6)
        #serial = [ (raw[0] << 8 | raw[1]), (raw[2] << 8 | raw[3])]
        serial = raw[0] << 24 | raw[1] << 16 | raw[2] << 8 | raw[3]
        return serial

    def measure_temp_rh_raw(self, precision=0):
        """ measure temp and rh return raw values including crc bytes """
        self._i2c_write(_SHT40_ADDR, [MEASURE_CMDS[precision]])
        sleep(0.01)
        data = self._i2c_read(_SHT40_ADDR, 6, strip_crc=False)
        return data

    def measure_temp_rh(self, precision=0):
        """ measure and convert temp (°C) and rh (%) """
        raw = self.measure_temp_rh_raw(precision)

        temp_raw = raw[0:2]
        rh_raw = raw[3:5]

        temp = -45 + (175 * (temp_raw[0] << 8 | temp_raw[1])) / (2**16 - 1)
        rh = -6 + (125 * (rh_raw[0] << 8 | rh_raw[1])) / (2**16 - 1)

        return temp, rh

    def activate_heater(self, mode=5):
        """ read datasheet - activate heater """
        self._i2c_write(_SHT40_ADDR, [HEATER_CMDS[mode]])
        return
