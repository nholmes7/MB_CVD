'''
Defines a recipe class.  Recipes are defined from a CSV file containing the
sequential instructions.  Furnace and MFC objects are also passed in for the
recipe to use.
'''

class recipe():
    '''
    A class for the recipes that will be used for the tube furnace CVD system.

    Public Methods
    --------------

        run()
    '''

    def __init__(self,filename,furnace,MFCs):
        self.steps = []
        with open(filename,'r') as file:
            for line in file:
                if line[0] != '#':
                    self.steps.append(line[:-1].split(','))
        # Convert strings to numbers.
        self.steps = [[float(j) for j in i] for i in self.steps]
        self.furnace = furnace
        self.mfc_1 = MFCs[0]
        self.mfc_2 = MFCs[1]
        self.mfc_3 = MFCs[2]

        self.times = [i[0] for i in self.steps]
        self.temps = [i[1] for i in self.steps]
        self.flow_1 = [i[2] for i in self.steps]
        self.flow_2 = [i[3] for i in self.steps]
        self.flow_3 = [i[4] for i in self.steps]
    
    def run(self):
        start_time = time.time()
        i = 0
        for time_step in self.times:
            task_1 = threading.Thread(target=self.furnace.SetTemp,args=(self.temps[i]))
            task_2 = threading.Thread(target=self.mfc_1.SetFlow,args=(self.flow_1[i]))
            task_3 = threading.Thread(target=self.mfc_2.SetFlow,args=(self.flow_2[i]))
            task_4 = threading.Thread(target=self.mfc_3.SetFlow,args=(self.flow_3[i]))

            task_1.start()
            task_2.start()
            task_3.start()
            task_4.start()

            # some print statements for debugging
            print('Time: ' + str(round(time.time()-start_time,3)) + ' s.')
            print('Setting temperature to ' + str(self.temps[i]))
            print('Setting gas 1 to ' + str(self.flow_1[i]))
            print('Setting gas 2 to ' + str(self.flow_2[i]))
            print('Setting gas 3 to ' + str(self.flow_3[i]))

            time.sleep(time_step)

            i = i + 1

if __name__ == '__main__':
    # from function_files.equipment import *
    import threading, time
    test_recipe = recipe('example_recipe',1,[1,2,3])
    print(test_recipe.steps)
    test_recipe.run()