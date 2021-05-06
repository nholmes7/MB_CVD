import serial
from MFC_command_checksum import *
from MFC_response_checksum import *

ser = serial.Serial(port='/dev/ttyUSB0',baudrate=9600,timeout=3)

# Function definition for setting the address of a connected MFC.

def change_address(current_address,new_address):
    command = '@@@' + str(current_address) + 'CA!' + str(new_address) + ';'
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
        reply = ser.read_until(expected=bytes(';','ascii'))
        # append the checksum characters
        reply = reply + ser.read(size=2)
        reply = reply.decode('ascii',errors = 'ignore')
        print('Received: ' + str(reply))
        acknowledged = reply.count('ACK')
        if acknowledged and check_response(reply):
            send_status = True
            # parse out the address from the reply message
            start_pos = reply.index('ACK')
            end_pos = reply.index(';')
            set_address = reply[start_pos+3:end_pos]
        if counter > max_iter:
            return 'No communication with MFC ' + str(current_address)
    return set_address

print(change_address('254','104'))