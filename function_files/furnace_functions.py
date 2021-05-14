def furnace_checksum(command):
    CRC = 0xFFFF
    
    # parse command out into bytes
    msg = [int(command[i:i+2]) for i in range(len(command)) if not i%2]

    for num in msg:
        CRC = CRC^num          # XOR operation
        for i in range(8):
            flag = CRC & 1     # tells us if the bit we lose in the shift is 1 or 0
            CRC = CRC >> 1     # bit shift one to the right
            if flag:
                CRC = CRC^0xA001

    # it will be more useful to return this formatted as a string
    CRC = hex(CRC)[2:]
    
    # for some reason the furnace ones the bytes reversed -
    # need to figure out if I'm understanding this correctly
    CRC = CRC[2:]+CRC[:2]
    
    return CRC

# useful for debugging
if __name__ == '__main__':
    print(furnace_checksum('0207'))