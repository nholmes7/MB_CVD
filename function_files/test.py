def returnSomething():
    print('This function returns something.')
    return 10

def dontReturn():
    print('This function returns nothing.')

def execute(func):
    reply = func()
    if reply:
        print('There was a reply')
        return
    print('Does this print?')


execute(dontReturn)
