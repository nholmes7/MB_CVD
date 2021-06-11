from function_files.equipment import pressure_trans


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
    press_trans: pressure transducer object
        instance of the pressure_trans class
    times: list
        sequential list of recipe step times
    temps: list
        sequential list of recipe furnace temperatures
    flow: dict
        dictionary of lists
    log_initialize: bool
        tracks whether the log file has been written to yet
    _lock: threading.Lock() object
        used for threading the logging and recipe execution
    logging_state: bool
        used to start and stop logging when a recipe is run

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
        self.logging_state = False
        self._lock = threading.Lock()
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
        self.press_trans = pressure_trans(123)
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
                self.temps = [int(j[i]) for j in self.steps]
            else:
                self.MFCs[column] = MFC(recipe.MFC_address_lookup[column])
                self.flow[column] = [j[i] for j in self.steps]
            i = i + 1
    
    def run(self):
        '''
        Runs the recipe from start to finish

            Parameters:
                None
            Returns:
                None
        '''
        self.logging_state = True
        start_time = time.time()
        i = 0
        for time_step in self.times:
            with self._lock:
                print('Time: ' + str(round(time.time()-start_time,3)) + ' s.')
                # Check to see if we have a furnace.
                if self.furnace:
                    print('Setting temperature to ' + str(self.temps[i]))
                    self.furnace.SetTemp(self.temps[i])
                # Check to see if we have MFCs.
                if self.MFCs:
                    for gas in self.MFCs:
                        if i > 0:
                            if self.flow[gas][i] == self.flow[gas][i-1]:
                                pass
                            else:
                                print('Setting ' + gas + ' to ' + str(self.flow[gas][i]))
                                self.MFCs[gas].SetFlow(self.flow[gas][i])
                        else:
                            print('Setting ' + gas + ' to ' + str(self.flow[gas][i]))
                            self.MFCs[gas].SetFlow(self.flow[gas][i])

            time.sleep(time_step)
            i = i + 1
        self.logging_state = False

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
        status = self.press_trans.ReportStatus()
        success.append(status)

        success = all(success)

        if success:
            print('Communication established with all required devices.')
        else:
            print('Unable to establish communication with all devices.')

        return success

    def logging(self,freq,filename):
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
        while self.logging_state:
        # for i in range(50):
            with self._lock:
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
        # Check to see if we have a furnace.
        if self.furnace:
            current_params['Temp'] = self.furnace.QueryTemp()
        # Check to see if we have MFCs.
        if self.MFCs:
            for gas in self.MFCs:
                current_params[gas] = self.MFCs[gas].QueryFlow()
        current_params['Press'] = self.press_trans.QueryPressure()

        return current_params

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
    # test_recipe.run()
    # test_recipe.logging(2,'test_log')
    # test_recipe.initialize()
    # test_recipe.poll()
    run_task = threading.Thread(target=test_recipe.run)
    log_task = threading.Thread(target=test_recipe.logging,args=(2,'test_log'))
    run_task.start()
    log_task.start()