'''
Python classes for the various devices connected to the RS-485 network for the
tube furnace CVD system.

Classes:

    MFC -> mass flow controller
    furnace -> tube furnace
    pressure_trans -> pressure transducer
'''

class MFC:
    '''
    A class for the mass flow controllers in the system.  Includes methods 
    for controlling them.
    '''

    def __init__(self,address):
        self.address = address

    def SetFlow(self,set_point):
        try:
            reply_text = self.__SendCommand('SX!',set_point)
            print('Flow set to ' + reply_text + 'sccm.')
        except Warning:
            print('Unsuccessful communication with MFC ' + str(self.address))

    def ChangeAddress(self,new_address):
        try:
            reply_text = self.__SendCommand('CA!',new_address)
            print('Address set to ' + reply_text)
        except Warning:
            print('Unsuccessful communication with MFC ' + str(self.address))

    def ReportFlow(self):
        try:
            reply_text = self.__SendCommand('FX?')
            print('Flow reported as ' + reply_text + 'sccm.')
        except Warning:
            print('Unsuccessful communication with MFC ' + str(self.address))

    def QueryOpMode(self):
        try:
            reply_text = self.__SendCommand('OM?')
            print('MFC is in ' + reply_text)
        except Warning:
            print('Unsuccessful communication with MFC ' + str(self.address))

    def __SendCommand(self,command_text,command_value=''):
        command = self.__BuildCommand(command_text,command_value)
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
            
            send_status = self.__ValidateResponse(reply)
            
            # Parse return message from the reply.
            if send_status:
                start_pos = reply.index('ACK')
                end_pos = reply.index(';')
                returned_text = reply[start_pos+3:end_pos]

            if comm_attempts > max_iter:
                raise Warning('Unsuccessful communication with MFC ' + str(self.address))

        return returned_text

    def __BuildCommand(self,command_text,command_value):
        command = '@@@' + str(self.address) + command_text + str(command_value) + ';'
        command = command + self.__CommandChecksum(command)
        command = bytes(command,'ascii')
        return command

    def __ValidateResponse(self,response):
        '''
        Determines whether the response received over the serial comms is valid.
        A valid response contains the string "ACK" and the checksum needs to
        match the calculated value.
        '''
        valid = False
        checksum = response[-2:]
        calculated_checksum = self.__ResponseChecksum(response)
        if checksum == calculated_checksum:
            valid = True
        acknowledged = response.count('ACK')
        if acknowledged and valid:
            return True
        return False

    def __CommandChecksum(self,command):
        '''
        Function drops a checksum value if present, drops any leading @ symbols,
        and then calculates the checksum by summing the ASCII values, and
        returning the last two hexadecimal digites of the sum value. 
        '''
        command,_ = command.split(';')
        command = command + ';'
        index = command.rindex('@')
        command = command[index:]
        command = bytearray(command,'ascii')
        char_sum = sum(command)
        return hex(char_sum)[-2:].upper()
    
    def __ResponseChecksum(self,response):
        '''
        Function works the same way as the command checksum but doesn't drop the
        leading @ symbols.
        '''
        response,_ = response.split(';')
        response = response + ';'
        response = bytearray(response,'ascii')
        char_sum = sum(response)
        return hex(char_sum)[-2:].upper()

class furnace():

    def __init__(self) -> None:
        pass

    def SetTemp(self):
        pass

    def QueryTemp(self):
        pass
    
    def __CRC(self,msg):
        CRC = 0xFFFF
        for num in msg:
            CRC = CRC^num               # bitwise XOR
            for i in range(8):
                flag = CRC%2            # tells us if last bit is 1 or 0
                CRC = CRC >> 1          # bit shift right
                if flag:
                    CRC = CRC^0xA001
        
        # For some reason they flip the bits...
        error_check_code = hex(CRC)[4:] + hex(CRC)[2:4]

        return error_check_code
