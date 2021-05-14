import serial

ser = serial.Serial(port='/dev/ttyUSB0',baudrate=9600,timeout=3)

# A file to house all the functions associated with MFC control.

def MFC_command(MFC_ID,command_type,command_value=""):
    command_dict = {
        'set_flow':['SX!','Flow set to ',' sccm'],
        'change_address':['CA!','Flow set to ',''],
        'report_flow':['FX?','Flow reported to be ',' sccm'],
        'query_operating_mode':['OM?','MFC is in ','']
    }
    command_text = command_dict[command_type][0]
    command = '@@@' + str(MFC_ID) + command_text + str(command_value) + ';'
    command = command + MFC_command_checksum(command)
    command = bytes(command,'ascii')
    send_status = False
    max_iter = 5
    comm_attempts = 0
    while not send_status:
        comm_attempts = comm_attempts + 1
        print('Sending: ' + str(command))
        ser.write(command)
        # reply = ser.read_until(expected=bytes(';','ascii'))
        reply = ser.read_until(terminator=bytes(';','ascii'))
        # append the checksum characters
        reply = reply + ser.read(size=2)
        reply = reply.decode('ascii',errors = 'ignore')
        print('Received: ' + str(reply))
        # Try except statement to deal with the frequent weirdness
        # at the start of the replies
        try:
            pos = reply.rindex('@')
            reply = '@@' + reply[pos:]
        except ValueError:
            pass
        print('Interpreted as: ' + str(reply))
        
        # For communication to be deemed successful, the string
        # 'ACK' must appear in the reply, and the checksum needs
        # to be correct.
        acknowledged = reply.count('ACK')
        if acknowledged and check_response(reply):
            send_status = True
            start_pos = reply.index('ACK')
            end_pos = reply.index(';')
            returned_text = reply[start_pos+3:end_pos]
        if comm_attempts > max_iter:
            return 'Unsuccessful communication with MFC ' + str(MFC_ID)
    print(command_dict[command_type][1] + returned_text + command_dict[command_type][2])
    return returned_text

# Function drops a checksum value if present, 
# drops any leading '@' symbols, and then calculates 
# the checksum by summing the ASCII values, and 
# returning the last two hexadecimal digits of the sum value.

def MFC_command_checksum(command):
    command,_ = command.split(';')
    command = command + ';'
    index = command.rindex('@')
    command = command[index:]
    command = bytearray(command,'ascii')
    char_sum = sum(command)
    return hex(char_sum)[-2:].upper()

# Function checks to see if the checksum provided 
# is correct.

def check_response(response):
    checksum = response[-2:]
    calculated_checksum = MFC_response_checksum(response)
    if checksum == calculated_checksum:
        return True
    else:
        return False

# Function drops a checksum value if present and 
# then calculates the checksum by summing the ASCII 
# values, and returning the last two hexadecimal 
# digits of the sum value.

def MFC_response_checksum(response):
    response,_ = response.split(';')
    response = response + ';'
    response = bytearray(response,'ascii')
    char_sum = sum(response)
    return hex(char_sum)[-2:].upper()