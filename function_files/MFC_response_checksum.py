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
    print(response)
    response = bytearray(response,'ascii')
    char_sum = sum(response)
    return hex(char_sum)[-2:].upper()

# print(check_response('@@@000ACK;5A'))