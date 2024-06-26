import pwnagotchi
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import logging
import struct
import datetime
import smbus
import time

# Config Register (R/W)
_REG_CONFIG                 = 0x00
# SHUNT VOLTAGE REGISTER (R)
_REG_SHUNTVOLTAGE           = 0x01

# BUS VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE             = 0x02

# POWER REGISTER (R)
_REG_POWER                  = 0x03

# CURRENT REGISTER (R)
_REG_CURRENT                = 0x04

# CALIBRATION REGISTER (R/W)
_REG_CALIBRATION            = 0x05


class BusVoltageRange:
    """Constants for ``bus_voltage_range``"""
    RANGE_16V               = 0x00      # set bus voltage range to 16V
    RANGE_32V               = 0x01      # set bus voltage range to 32V (default)

class Gain:
    """Constants for ``gain``"""
    DIV_1_40MV              = 0x00      # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV              = 0x01      # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV             = 0x02      # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV             = 0x03      # shunt prog. gain set to /8, 320 mV range

class ADCResolution:
    """Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``"""
    ADCRES_9BIT_1S          = 0x00      #  9bit,   1 sample,     84us
    ADCRES_10BIT_1S         = 0x01      # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S         = 0x02      # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S         = 0x03      # 12 bit,  1 sample,    532us
    ADCRES_12BIT_2S         = 0x09      # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S         = 0x0A      # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S         = 0x0B      # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S        = 0x0C      # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S        = 0x0D      # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S        = 0x0E      # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S       = 0x0F      # 12bit, 128 samples, 68.10ms

class Mode:
    """Constants for ``mode``"""
    POWERDOW                = 0x00      # power down
    SVOLT_TRIGGERED         = 0x01      # shunt voltage triggered
    BVOLT_TRIGGERED         = 0x02      # bus voltage triggered
    SANDBVOLT_TRIGGERED     = 0x03      # shunt and bus voltage triggered
    ADCOFF                  = 0x04      # ADC off
    SVOLT_CONTINUOUS        = 0x05      # shunt voltage continuous
    BVOLT_CONTINUOUS        = 0x06      # bus voltage continuous
    SANDBVOLT_CONTINUOUS    = 0x07      # shunt and bus voltage continuous


class INA219:
    def __init__(self, i2c_bus=1, addr=0x40):
        self.bus = smbus.SMBus(i2c_bus);
        self.addr = addr

        # Set chip to known config values to start
        self._cal_value = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_16V_5A()

    def read(self,address):
        data = self.bus.read_i2c_block_data(self.addr, address, 2)
        return ((data[0] * 256 ) + data[1])

    def write(self,address,data):
        temp = [0,0]
        temp[1] = data & 0xFF
        temp[0] =(data & 0xFF00) >> 8
        self.bus.write_i2c_block_data(self.addr,address,temp)

    def set_calibration_16V_5A(self):
        self._current_lsb = 0.1524
        self._cal_value = 26868

        # 6. Calculate the power LSB
        # PowerLSB = 20 * CurrentLSB
        # PowerLSB = 0.002 (2mW per bit)
        self._power_lsb = 0.003048  # Power LSB = 2mW per bit
        self.write(_REG_CALIBRATION,self._cal_value)

        # Set Config register to take into account the settings above
        self.bus_voltage_range = BusVoltageRange.RANGE_16V
        self.gain = Gain.DIV_2_80MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.mode = Mode.SANDBVOLT_CONTINUOUS
        self.config = self.bus_voltage_range << 13 | \
                      self.gain << 11 | \
                      self.bus_adc_resolution << 7 | \
                      self.shunt_adc_resolution << 3 | \
                      self.mode
        self.write(_REG_CONFIG,self.config)

    def getShuntVoltage_mV(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        value = self.read(_REG_SHUNTVOLTAGE)
        if value > 32767:
            value -= 65535
        return value * 0.01

    def getBusVoltage_V(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        self.read(_REG_BUSVOLTAGE)
        return (self.read(_REG_BUSVOLTAGE) >> 3) * 0.004

    def getCurrent_mA(self):
        value = self.read(_REG_CURRENT)
        if value > 32767:
            value -= 65535
        return value * self._current_lsb

    def getPower_W(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        value = self.read(_REG_POWER)
        if value > 32767:
            value -= 65535
        return value * self._power_lsb

    def check_battery_shutdown(battery_percentage, shutdown_threshold, delay_seconds=5):
        start_time = time.time()
        while time.time() - start_time < delay_seconds:
            if battery_percentage > shutdown_threshold:
                return False
            time.sleep(1)
        return True

class waveshareups(plugins.Plugin):
    __author__ = 'https://github.com/leopascal1, https://github.com/Shreyas-ITB'
    __version__ = '1.0.1'
    __license__ = 'GPL3'
    __description__ = 'battery in percentage (Waveshare UPS HAT (C) for RP Zero) with some additional added information and safety'

    
    def __init__(self):
        self.loaded = False
        self.bat = None
        self.addr = 0x43
        self._black = 0xFF
    def on_loaded(self):
        #load plugin stuff
        
        #if toml allows it
        if 'address' in self.options:
            self.addr = self.options['address']
        
        self.loaded = True
        self.bat = INA219(addr=self.addr)
        logging.info("[waveshareups] Battery Plugin loaded.")

    
    def on_ui_setup(self, ui):
        logging.debug("[waveshareups] Battery Plugin UI Setup starting.")
        ui.add_element('ups', LabeledValue(color=self._black, label='UPS', value='-', position=(int(self.options["ups_x_coord"]), int(self.options["ups_y_coord"])),
                                           label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element('volt', LabeledValue(color=self._black, label='VOL', value='-', position=(int(self.options["vol_x_coord"]), int(self.options["vol_y_coord"])),
                                           label_font=fonts.Bold, text_font=fonts.Medium))
        logging.debug("[waveshareups] Battery Plugin UI Setup finished OK.")
    
    def on_ui_update(self, ui):
        bus_voltage = self.bat.getBusVoltage_V()
        p = (bus_voltage - 3)/1.2*100
        if(p > 100):p = 100
        if(p < 0):p = 0
        ui.set('ups', "{:02d}%".format(int(p)))

        voltage = self.bat.getBusVoltage_V()
        ui.set('volt', "{:.2f}v".format(voltage))

        if p <= self.options['shutdown']:
            logging.info('[waveshareups] Battery at or below shutdown threshold (<= %s%%): checking for sustained low battery..' % self.options['shutdown'])
            if self.bat.check_battery_shutdown(p, self.options['shutdown']):
                logging.info('[waveshareups] Empty battery (<= %s%%): shutting down..' % self.options['shutdown'])
                ui.update(force=True, new_data={'status': 'Battery exhausted, bye ...'})
                time.sleep(5)
                pwnagotchi.shutdown()
            else:
                logging.info('[waveshareups] Battery level recovered, shutdown aborted.')
