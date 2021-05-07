import serial
from MFC_command_checksum import *
from MFC_response_checksum import *

ser = serial.Serial(port='/dev/ttyUSB0',baudrate=9600,timeout=3)

# Function uses the MFC ID and desired flow rate to build the command.  
# Tries sending the command over and over until it receives an 'ACK' 
# response with a correct checksum.

def set_flow(MFC_ID,flow_rate):
    command = '@@@' + str(MFC_ID) + 'SX!' + str(flow_rate) + ';'
    command = command + MFC_command_checksum(command)
    command = bytes(command,'ascii')
    send_status = False
    while not send_status:
        ser.write(command)
        print('Sending: ' + str(command))
        reply = ser.read_until(terminator=bytes(';','ascii'))
        # append the checksum characters
        reply = reply + ser.read(size=2)
        reply = reply.decode('ascii',errors = 'ignore')
        print('Received: ' + str(reply))
        acknowledged = reply.count('ACK')
        if acknowledged and check_response(reply):
            send_status = True
    print('Flow for MFC ' + str(MFC_ID) + ' set to ' + str(flow_rate) + 'sccm')

set_flow(103,0)