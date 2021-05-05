def poll_pressure():
    string_to_send = '#123P\r'
    string_to_send = bytes(string_to_send, 'ascii')
    poll_status = 'failed'
    while poll_status == 'failed':                                          # the pressure transducer is a bit buggy so we need to check if the returned value is valid
        ser.write(string_to_send)
        returned_data = ser.read_until(terminator=bytes(">",'ascii'))       
        returned_data = returned_data.decode('ascii',errors='ignore')       # this turns it into a string and gets rid of all the random hex characters
        index = returned_data.find('.')                                     # the '.' marks the decimal point in the pressure reading
        returned_data = returned_data[index-3:index+4]
        try:                                                                
            returned_data = float(returned_data)                            # if the result can't be converted to a float, something went wrong and we try again
            poll_status = 'success'
        except:
            pass
    return returned_data