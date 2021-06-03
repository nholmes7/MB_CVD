class recipe():
    '''
    A class for the recipes that will be used for the tube furnace CVD system.

    ...

    Attributes
    ----------
    steps: list
        nested list of all the recipe steps
    furnace: furnace object
        instance of the furnace class
    MFCs: dict
        dictionary of the instances of the MFC class, done so that the MFCs may
        be dynamically created based on the recipe
    times: list
        sequential list of recipe step times
    temps: list
        sequential list of recipe furnace temperatures
    flows: dict
        dictionary of lists
    

    Public Methods
    --------------
    run(log_freq)
    initialize()
    '''

    MFC_address_lookup = {
        'Ethylene':101,
        'C2H4':101,
        'C2h4':101,
        'c2h4':101,
        'ethylene':101,
        'ETHYLENE':101,
        'Argon':102,
        'Ar':102,
        'AR':102,
        'argon':102,
        'ARGON':102,
        'ar':102,
        'Helium':103,
        'He':103,
        'HE':103,
        'helium':103,
        'HELIUM':103,
        'he':103,
        'Hydrogen':104,
        'H2':104,
        'h2':104,
        'hydrogen':104,
        'HYDROGEN':104
    }

    def __init__(self,filename):
        self.steps = []
        with open(filename,'r') as file:
            for line in file:
                if line[0] != '#':
                    self.steps.append(line[:-1].split(','))
                if line[:8] == '#Columns':
                    columns = line[10:-1].split(',')
        # Convert strings to numbers.
        self.steps = [[float(j) for j in i] for i in self.steps]
        
        # Initialize the equipment objects
        self.furnace = None
        self.MFCs = {}

        # Define the equipment
        for column in columns:
            if column == 'Time':
                pass
            elif column == 'Temp':
                self.furnace = furnace(150)
            else:
                self.MFCs[column] = MFC(recipe.MFC_address_lookup[column])

        self.times = [i[0] for i in self.steps]
        self.temps = [i[1] for i in self.steps]
        self.flow_1 = [i[2] for i in self.steps]
        self.flow_2 = [i[3] for i in self.steps]
        self.flow_3 = [i[4] for i in self.steps]
    
    def run(self,log_freq=2):
        start_time = time.time()
        i = 0
        for time_step in self.times:
            # task_1 = threading.Thread(target=self.furnace.SetTemp,args=(self.temps[i]))
            # task_2 = threading.Thread(target=self.mfc_1.SetFlow,args=(self.flow_1[i]))
            # task_3 = threading.Thread(target=self.mfc_2.SetFlow,args=(self.flow_2[i]))
            # task_4 = threading.Thread(target=self.mfc_3.SetFlow,args=(self.flow_3[i]))

            # task_1.start()
            # task_2.start()
            # task_3.start()
            # task_4.start()

            # some print statements for debugging
            print('Time: ' + str(round(time.time()-start_time,3)) + ' s.')
            print('Setting temperature to ' + str(self.temps[i]))
            print('Setting gas 1 to ' + str(self.flow_1[i]))
            print('Setting gas 2 to ' + str(self.flow_2[i]))
            print('Setting gas 3 to ' + str(self.flow_3[i]))

            time.sleep(time_step)

            i = i + 1

    def initialize(self):
        '''
        Verifies the status of the devices required by the recipe.

            Parameters:
                self
            Returns:
                success (bool): whether communication was established with all
                devices
        '''
        pass
        # a = self.furnace.ReportStatus()
        # b = self.mfc_1.QueryOpMode()
        # c = self.mfc_2.QueryOpMode()
        # d = self.mfc_3.QueryOpMode()

        # if a and b and c and d:
        #     return True
        # else:
        #     return False
        

    
# Here follows code  which will be used for data logging when I get there.

    # def __logging(self,freq,filename):
    #     delay = 1/freq
    #     while True:
    #         params = self.__poll()
    #         self.__write_to_file(filename,params)
    #         time.sleep(delay)

    # def __poll(self):
    #     task_1 = threading.Thread(target=self.furnace.QueryTemp)
    #     task_2 = threading.Thread(target=self.mfc_1.QueryFlow)
    #     task_3 = threading.Thread(target=self.mfc_2.QueryFlow)
    #     task_4 = threading.Thread(target=self.mfc_3.QueryFlow)

    #     task_1.start()
    #     task_2.start()
    #     task_3.start()
    #     task_4.start()

    # def __write_to_file(self,filename,params):
    #     pass
    
if __name__ == '__main__':
    from equipment import *
    import threading, time
    test_recipe = recipe('example_recipe')
    print(test_recipe.steps)
    print(test_recipe.MFCs['Helium'].address)