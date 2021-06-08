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

    ...

    Attributes
    ----------
    address: int
        the address used for serial comms

    Public Methods
    --------------
    SetFlow(set_point)
    ChangeAddress(new_address)
    QueryFlow()
    QueryOpMode()
    '''

    import serial
    ser = serial.Serial(port='/dev/ttyUSB0',baudrate=9600,timeout=3)

    def __init__(self,address) -> None:
        self.address = address

    def SetFlow(self,set_point):
        '''
        Set a flow rate for an MFC object.

            Parameters:
                set_point (float): the desired set point
            Returns:
                None
        '''
        try:
            self.__SendCommand('SX!',set_point)
            print('Flow set to ' + str(set_point) + ' sccm.')
        except Warning:
            print('Unsuccessful communication with MFC ' + str(self.address))

    def ChangeAddress(self,new_address):
        '''
        Changes the serial address of an existing MFC object.

            Parameters:
                new_address (int): the updated address
            Returns:
                None
        '''
        try:
            reply_text = self.__SendCommand('CA!',new_address)
            print('Address set to ' + reply_text)
        except Warning:
            print('Unsuccessful communication with MFC ' + str(self.address))

    def QueryFlow(self):
        '''
        Queries the current flow rate of an MFC object.

            Parameters:
                None
            Returns:
                flow_rate (float): the mass flow rate measured by the device
        '''
        try:
            reply_text = self.__SendCommand('FX?')
            print('Flow reported as ' + reply_text + 'sccm.')
            flow_rate = float(reply_text)
            return flow_rate
        except Warning:
            print('Unsuccessful communication with MFC ' + str(self.address))

    def QueryOpMode(self):
        '''
        Checks to see if the MFC is in run mode or in ______ mode.

            Parameters:
                None
            Returns:
                boolean value which indicates whether communication with MFC was
                successful
        '''
        try:
            reply_text = self.__SendCommand('OM?')
            print('MFC is in ' + reply_text)
            return True
        except Warning:
            print('Unsuccessful communication with MFC ' + str(self.address))
            return False

    def __SendCommand(self,command_text,command_value=''):
        '''
        Send a command to an MFC object over serial connection.

            Parameters:
                command_text (str): the portion of the serial message containing
                    the unique command identifier
                command_value (str): an optional argument when an additional
                    value is required, such as the mass flow rate value when
                    setting a new mass flow rate
            Returns:
                returned_text (str): the portion of the returned serial message 
                    between the 'ACK', and the end of message character ';' -
                    sometimes empty depending on the command.
        '''
        command = self.__BuildCommand(command_text,command_value)
        send_status = False
        max_iter = 5
        comm_attempts = 0
        while not send_status:
            comm_attempts = comm_attempts + 1
            # print('Sending: ' + str(command))
            MFC.ser.write(command)
            reply = MFC.ser.read_until(expected=bytes(';','ascii'))
            # reply = MFC.ser.read_until(terminator=bytes(';','ascii'))
            # append the checksum characters
            reply = reply + MFC.ser.read(size=2)
            reply = reply.decode('ascii',errors = 'ignore')
            # print('Received: ' + str(reply))
            # Try except statement to deal with the frequent weirdness
            # at the start of the replies
            try:
                pos = reply.rindex('@')
                reply = '@@' + reply[pos:]
            except ValueError:
                pass
            # print('Interpreted as: ' + str(reply))
            
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
        '''
        Builds the command as per the MFC serial comms specifications.

            Parameters:
                command_text (str): the portion of the serial message containing
                    the unique command identifier
                command_value (str): an optional argument when an additional
                    value is required, such as the mass flow rate value when
                    setting a new mass flow rate
            Returns:
                command (ascii bytes): a string of the complete command, 
                    including a checksum value at the end
        '''
        command = '@@@' + str(self.address) + command_text + str(command_value) + ';'
        command = command + self.__CommandChecksum(command)
        command = bytes(command,'ascii')
        return command

    def __ValidateResponse(self,response):
        '''
        Determines whether the response received over the serial comms is valid.
        A valid response contains the string "ACK" and the checksum needs to
        match the calculated value.

            Parameters:
                response (str): the reply message from the MFC
            Returns:
                boolean value indicating whether the response contains the 'ACK'
                string and the checksum is correct
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

            Parameters:
                command (str): the command to send
            Returns:
                a hex number in string form which represents the checksum value
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

            Parameters:
                response (str): the reply message from the MFC
            Returns:
                a hex number in string form which represents the checksum value
        '''
        response,_ = response.split(';')
        response = response + ';'
        response = bytearray(response,'ascii')
        char_sum = sum(response)
        return hex(char_sum)[-2:].upper()

class furnace:
    '''
    A class for the tube furnace in the system.  Includes methods for control.

    ...

    Attributes
    ----------
    address: str
        the address used for serial comms over MODBUS as a two digit hex byte

    Public Methods
    --------------
    SetTemp(setpoint)
    QueryTemp()
    ChangeAddress()
    ReportStatus()
    '''

    import serial
    ser = serial.Serial(port='/dev/ttyUSB0',baudrate=9600,timeout=3)

    def __init__(self,address) -> None:
        self.address = hex(address)[2:]
        # If the address is only one char, add a leading zero for compatibility
        # with methods
        if len(self.address) == 1:
            self.address = '0' + self.address

    def SetTemp(self,setpoint):
        function_code = '10'
        address = '0077'
        no_of_words = '0001'
        no_of_bytes = '02'
        data = hex(setpoint)[2:].upper()
        response_length = 8
        # Prepend leading zeros
        while len(data) < 4:
            data = '0' + data
        command = self.address + function_code + address + no_of_words + \
            no_of_bytes + data
        CRC = self.__CRC(command)
        command += CRC
        try:
            self.__SendCommand(command,response_length,function_code)
            print('Temperature set to ' + str(setpoint) + ' C.')
        except Warning:
            raise Warning('Unsuccessful communication with tube furnace.')

    def QueryTemp(self):
        '''
        Check the current temperature as reported by the furnace

            Parameters:
                None
            Returns:
                temperature (int): temperature reported by the furnace
        '''
        function_code = '03'
        address = '0001'
        no_of_words = '0001'
        response_length = 5 + int(no_of_words,base=16)*2
        command = self.address + function_code + address + no_of_words
        CRC = self.__CRC(command)
        command += CRC
        try:
            response = self.__SendCommand(command,response_length,function_code)
            temperature = int.from_bytes(response[3:-2],byteorder='big')
            print('Temperature is ' + str(temperature) + ' C.')
        except Warning:
            raise Warning('Unsuccessful communication with tube furnace.')

        return temperature

    def ChangeAddress(self,new_address):
        pass

    def ReportStatus(self):
        function_code = '07'
        response_length = 5
        command = self.address + function_code
        CRC = self.__CRC(command)
        command += CRC
        try:
            response = self.__SendCommand(command,response_length,function_code)
        except Warning:
            raise Warning('Unsuccessful communication with tube furnace.')
        
        # If we want to actually check the status we can throw some code in here
        # in the future.  Otherwise as long as we didn't get the unsuccessful
        # comms warning then we'll assume everything is functioning as intended.
        return True

    
    def __SendCommand(self,command,response_length,function_code):
        '''
        Private method responsible for repeatedly sending the command until a
        response is received with correct CRC and no error message.

        Returns the raw bytes received
        '''
        # print('Command before byte conversion: ' + command)
        command = bytes.fromhex(command)
        send_status = False
        max_iter = 5
        comm_attempts = 0
        while not send_status:
            comm_attempts = comm_attempts + 1
            # print('Sending: ' + str(command))
            furnace.ser.write(command)
            valid,error_flag,response = self.__ReceiveResponse(response_length,function_code)

            if valid and not(error_flag):
                send_status = True
                # print('Received: ' + str(response))

            if comm_attempts > max_iter:
                raise Warning('Unsuccessful communication with tube furnace.')
        return response

    def __ReceiveResponse(self,response_length,function_code):
        '''
        Private method which listens for a MODBUS response.  Checks if the
        response is an error message and inspects the CRC value.

        Returns:
            - valid: whether the CRC checks out
            - error_flag: whether the message is an error message
            - response: raw bytes received
        '''
        valid = False
        error_flag = False
        response = furnace.ser.read(size=2)
        # print(response)
        function_code = int.from_bytes(bytes.fromhex(function_code),byteorder='big')
        
        # Check the second byte to see if we have a legitimate response or an
        # error message.  If we have an error message, the second byte will be
        # the function code plus 128.
        if response[1] == function_code:
            response = response + furnace.ser.read(size=(response_length-2))
        elif response[1] == function_code + 128:
            response = response + furnace.ser.read(size=3)
            error_flag = True

        returned_CRC = response[-2:]
        calculated_CRC = self.__CRC(response[:-2])
        calculated_CRC = bytearray.fromhex(calculated_CRC)

        if calculated_CRC == returned_CRC:
            valid = True
        
        return valid, error_flag, response

    def __CRC(self,msg):
        if type(msg) is str:
            msg = bytearray.fromhex(msg)
        CRC = 0xFFFF
        for num in msg:
            CRC = CRC^num               # bitwise XOR
            for i in range(8):
                flag = CRC%2            # tells us if last bit is 1 or 0
                CRC = CRC >> 1          # bit shift right
                if flag:
                    CRC = CRC^0xA001
        error_check_code = hex(CRC)[2:]
        # Prepend leading zeros
        while len(error_check_code) < 4:
            error_check_code = '0' + error_check_code

        # For some reason they flip the bit order...
        # error_check_code = hex(CRC)[2:]
        error_check_code = error_check_code[2:] + error_check_code[0:2]
        error_check_code = error_check_code.upper()
        # print('CRC: ' + hex(CRC))
        # print('CRC code: ' + error_check_code)

        return error_check_code

if __name__ == '__main__':
    test_furnace = furnace(5)
    test_furnace.QueryTemp()
    test_furnace.SetTemp(55)