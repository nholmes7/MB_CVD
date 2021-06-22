params = ['Temp','Ethylene','Argon','Helium','Hydrogen']

test = {'Ethylene':12,'Argon':7,'Goober':5,'Tasty':4}

to_delete = []
for item in test:
    if item not in params:
        to_delete.append(item)

print(to_delete)