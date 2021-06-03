# line = '#Columns: Time,Temp,Helium,Hydrogen,Ethylene'
# print(line[:8])
# if line[:8] == '#Columns':
#                     columns = line[10:-1].split(',')

# print(columns)


# for column in columns









class car():
    test_text = '2007 '
    def __init__(self,make):
        self.make = make

    def set_model(self,model):
        self.model = car.test_text + model

test = car('Volkswagen')

print(test.make)
# print(test.model)

test.set_model('Rabbit')

print(test.model)