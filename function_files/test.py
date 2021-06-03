# line = '#Columns: Time,Temp,Helium,Hydrogen,Ethylene'
# print(line[:8])
# if line[:8] == '#Columns':
#                     columns = line[10:-1].split(',')

# print(columns)


# for column in columns









# class car():
#     test_text = '2007 '
#     def __init__(self,make):
#         self.make = make

#     def set_model(self,model):
#         self.model = car.test_text + model

# test = car('Volkswagen')

# print(test.make)
# # print(test.model)

# test.set_model('Rabbit')

# print(test.model)




# MFC_address_lookup = {
#     'Ethylene':101,
#     'C2H4':101,
#     'C2h4':101,
#     'c2h4':101,
#     'ethylene':101,
#     'ETHYLENE':101,
#     'Argon':102,
#     'Ar':102,
#     'AR':102,
#     'argon':102,
#     'ARGON':102,
#     'ar':102,
#     'Helium':103,
#     'He':103,
#     'HE':103,
#     'helium':103,
#     'HELIUM':103,
#     'he':103,
#     'Hydrogen':104,
#     'H2':104,
#     'h2':104,
#     'hydrogen':104,
#     'HYDROGEN':104
# }

# print(len(MFC_address_lookup))

import serial

print(serial.__version__)