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
    return hex(char_sum)[-2:]

# print(MFC_command_checksum('@@@001UT!TEST;16'))