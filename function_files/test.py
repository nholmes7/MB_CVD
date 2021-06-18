def AddFive(num):
    return num + 5

def AddTen(num):
    return num + 10

def Execute(func,num):
    return func(num)

print(Execute(AddTen,4))
