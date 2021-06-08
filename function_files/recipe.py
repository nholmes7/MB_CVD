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
    flow: dict
        dictionary of lists
    log_initialize: bool
        tracks whether the log file has been written to yet

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

    def __init__(self,filename) -> None:
        self.log_initialize = False
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
        # Initialize the recipe sequence lists
        self.times = []
        self.temps = []
        self.flow = {}

        # Define the equipment based on the column labels and define the recipe
        # sequence lists
        i = 0
        for column in columns:
            if column == 'Time':
                self.times = [j[i] for j in self.steps]
            elif column == 'Temp':
                self.furnace = furnace(5)
                self.temps = [j[i] for j in self.steps]
            else:
                self.MFCs[column] = MFC(recipe.MFC_address_lookup[column])
                self.flow[column] = [j[i] for j in self.steps]
            i = i + 1
    
    def run(self,log_freq=2):
        start_time = time.time()
        i = 0
        for time_step in self.times:
            # Some print statements for debugging.
            print('Time: ' + str(round(time.time()-start_time,3)) + ' s.')
            # Check to see if we have a furnace.
            if self.furnace:
                print('Setting temperature to ' + str(self.temps[i]))
            # Check to see if we have MFCs.
            if self.MFCs:
                for gas in self.flow:
                    if i > 0:
                        if self.flow[gas][i] == self.flow[gas][i-1]:
                            pass
                        else:
                            print('Setting ' + gas + ' to ' + str(self.flow[gas][i]))
                    else:
                        print('Setting ' + gas + ' to ' + str(self.flow[gas][i]))
            
            # Set it up with no threading to start for simplicity and to get the
            # bugs worked out.
            # Check to see if we have a furnace.
            if self.furnace:
                self.furnace.SetTemp(self.temps[i])
            # Check to see if we have MFCs.
            if self.MFCs:
                for gas in self.MFCs:
                    if i > 0:
                        if self.flow[gas][i] == self.flow[gas][i-1]:
                            pass
                        else:
                            self.MFCs[gas].SetFlow(self.flow[gas][i])
                    else:
                        self.MFCs[gas].SetFlow(self.flow[gas][i])
            
            # Now with threading...
            # task_1 = threading.Thread(target=self.furnace.SetTemp,args=(self.temps[i]))
            # task_2 = threading.Thread(target=self.mfc_1.SetFlow,args=(self.flow_1[i]))
            # task_3 = threading.Thread(target=self.mfc_2.SetFlow,args=(self.flow_2[i]))
            # task_4 = threading.Thread(target=self.mfc_3.SetFlow,args=(self.flow_3[i]))

            # task_1.start()
            # task_2.start()
            # task_3.start()
            # task_4.start()

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
        success = []

        if self.furnace:
            status = self.furnace.ReportStatus()
            success.append(status)
        if self.MFCs:
            for gas in self.flow:
                status = self.MFCs[gas].QueryOpMode()
                success.append(status)

        success = all(success)

        if success:
            print('Communication established with all required devices.')
        else:
            print('Unable to establish communication with all devices.')

        return success
        

    
# Here follows code  which will be used for data logging when I get there.

    def __logging(self,freq,filename):
        '''
        Logs the operating parameters at a given frequency.

            Parameters:
                freq (float): logging frequency in Hz
                filename (str): filename including the file extension
            Returns:
                None
        '''
        log_start = time.time()
        delay = 1/freq
        # while True:
        for i in range(100):
            params = self.poll()
            log_time = time.time()-log_start
            params['Time'] = log_time
            self.__write_to_file(filename,params)
            time.sleep(delay)

    def poll(self):
        '''
        Polls all devices to query current operating parameters.

            Parameters:
                None
            Returns:
                current_params (dict): a dictionary of all the current operating
                    parameters
        '''
        current_params = {}
        # Set it up with no threading to start for simplicity and to get the
        # bugs worked out.
        # Check to see if we have a furnace.
        if self.furnace:
            current_params['Temp'] = self.furnace.QueryTemp()
        # Check to see if we have MFCs.
        if self.MFCs:
            for gas in self.MFCs:
                current_params[gas] = self.MFCs[gas].QueryFlow()

        return current_params

    #     task_1 = threading.Thread(target=self.furnace.QueryTemp)
    #     task_2 = threading.Thread(target=self.mfc_1.QueryFlow)
    #     task_3 = threading.Thread(target=self.mfc_2.QueryFlow)
    #     task_4 = threading.Thread(target=self.mfc_3.QueryFlow)

    #     task_1.start()
    #     task_2.start()
    #     task_3.start()
    #     task_4.start()


    def __write_to_file(self,filename,params):
        '''
        Write the current process parameters to a file.

            Parameters:
                filename (str): filename including the file extension
                params (dict): the current process parameters as read from the
                    networked devices
            Returns:
                None
        '''
        # If this is the first time writing to the log, delete the file contents
        # if that file already exists.
        if self.log_initialize == False:
            with open(filename,'w') as file:
                # By taking no action, we will in fact delete the file's
                # contents
                pass

        fieldnames = [name for name in params]
        
        with open(filename,'a') as file:
            log_writer = csv.DictWriter(file, fieldnames=fieldnames)
            if self.log_initialize == False:
                # Add code to write the date and time here
                log_writer.writeheader()
                self.log_initialize = True
            log_writer.writerow(params)
    
if __name__ == '__main__':
    # import serial
    # ser = serial.Serial(port='/dev/ttyUSB0',baudrate=9600,timeout=3)
    from equipment import *
    import threading, time, csv
    test_recipe = recipe('example_recipe')
    # print(test_recipe.steps)
    # print(test_recipe.flow)
    test_recipe.run()
    # test_recipe.initialize()
    # test_recipe.poll()