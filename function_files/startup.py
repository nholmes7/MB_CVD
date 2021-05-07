import serial
from MFC_command_checksum import *
from MFC_response_checksum import *

ser = serial.Serial(port='/dev/ttyUSB0',baudrate=9600,timeout=3)

# Ping all the devices on the network to make sure we have communication with each before we begin running our program.

equipment = {
    'MFC_C2H4':'101',
    'MFC_Ar':'102',
    'MFC_He':'103'
    # 'MFC_H2':'104'
}

def startup(equipment):
    for device in equipment:
        operating_mode = MFC_OM_query(equipment[device])
        print(device + ' is in ' + operating_mode + '.')

def MFC_OM_query(MFC_ID):
    command = '@@@' + str(MFC_ID) + 'OM?;'
    # append the checksum
    command = command + MFC_command_checksum(command)
    command = bytes(command,'ascii')
    send_status = False
    max_iter = 5
    counter = 0
    while not send_status:
        counter = counter + 1
        print('Sending: ' + str(command))
        ser.write(command)
        # reply = ser.read_until(expected=bytes(';','ascii'))
        reply = ser.read_until(terminator=bytes(';','ascii'))
        # append the checksum characters
        reply = reply + ser.read(size=2)
        reply = reply.decode('ascii',errors = 'ignore')
        print('Received: ' + str(reply))
        acknowledged = reply.count('ACK')
        if acknowledged and check_response(reply):
            send_status = True
            # parse out the flow rate from the reply message
            start_pos = reply.index('ACK')
            end_pos = reply.index(';')
            operating_mode = reply[start_pos+3:end_pos]
        if counter > max_iter:
            return 'No communication with MFC ' + str(MFC_ID)
    return operating_mode

startup(equipment)