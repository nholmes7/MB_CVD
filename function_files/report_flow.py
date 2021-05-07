import serial
from MFC_command_checksum import *
from MFC_response_checksum import *

ser = serial.Serial(port='/dev/ttyUSB0',baudrate=9600,timeout=3)

# Function uses the MFC ID to query the current flow rate.

def report_flow(MFC_ID):
    command = '@@@' + str(MFC_ID) + 'FX?;'
    # append the checksum
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
            # parse out the flow rate from the reply message
            start_pos = reply.index('ACK')
            end_pos = reply.index(';')
            flow_rate = reply[start_pos+3:end_pos]
    print('MFC ' + str(MFC_ID) + ' reports a flow rate of ' + str(flow_rate) + 'sccm')
    return flow_rate

report_flow(103)