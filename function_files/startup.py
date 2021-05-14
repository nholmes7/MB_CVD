import serial
from MFC_functions import *

ser = serial.Serial(port='/dev/ttyUSB0',baudrate=9600,timeout=3)

# Ping all the devices on the network to make sure we have 
# communication with each before we begin running our program.

equipment = {
    'MFC_C2H4':'101',
    'MFC_Ar':'102',
    'MFC_He':'103'
    # 'MFC_H2':'104'
}

def startup(equipment):
    for device in equipment:
        operating_mode = MFC_command(equipment[device],'query_operating_mode')

startup(equipment)