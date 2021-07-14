# import our Ui_MainWindow class from our Qt Designer generated file
from gui import Ui_MainWindow
from datetime import date
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
import threading, time, serial, math, csv, pyqtgraph,random
import pandas as pd
from equipment import *
from recipe import Recipe,QueueItem

# Define a new class which inherits from the QMainWindow object - not a default 
# python object like our Ui_MainWindow class
class cvd_control(QtWidgets.QMainWindow):
    
    # override the init method
    def __init__(self, *args, **kwargs):
        # whenever you override the init method in a Qt object you need to run 
        # super().__init__ and pass in any arguments that were passed in so it 
        # still behaves like a Qt widget
        super().__init__(*args, **kwargs)
        
        # setupUi builds the GUI onto the cvd_control QMainWindow object
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # make required connections
        self.ui.save_button.clicked.connect(self.save_recipe)
        self.ui.open_button.clicked.connect(self.OpenRecipe)
        self.ui.button_start_recipe.clicked.connect(self.start_recipe)
        self.ui.button_stop_recipe.clicked.connect(self.StopRecipe)
        self.ui.button_apply_setpoints.clicked.connect(self.apply_setpoints)

        # Configure the plots and their settings.
        background_colour = self.palette().color(QtGui.QPalette.Window)
        styles = {"color": 'k', "font-size": "14px"}
        self.ui.temp_graph.setBackground(background_colour)
        self.ui.temp_graph.setTitle('Temperature',color='k',size = '16pt')
        self.ui.temp_graph.setLabel("bottom", "Time (s)", **styles)
        self.ui.gas_graph.setBackground(background_colour)
        self.ui.gas_graph.setTitle('Flow Rates',color='k',size = '16pt')
        self.ui.gas_graph.addLegend(offset = (1,-125))
        self.ui.gas_graph.setLabel("bottom", "Time (s)", **styles)

        # Define all devices.
        self.furnace = furnace(5)
        self.MFCs = {'Ethylene':MFC(101),
            'Argon':MFC(102),
            'Helium':MFC(103),
            'Hydrogen':MFC(104)
            }
        self.press_trans = pressure_trans(123)

        # Pen objects used for plotting style.
        plot_colours = ['#7a0177','#c51b8a','#f768a1','#fa9fb5']
        self.pens = {}
        i = 0
        for gas in self.MFCs:
            self.pens[gas] = pyqtgraph.mkPen(color=plot_colours[i],width=2)
            i = i+1

        # Initialize plots.
        self.temp_line = self.ui.temp_graph.plot(pen=self.pens['Ethylene'])
        self.gas_lines = {}
        for gas in self.MFCs:
            self.gas_lines[gas] = self.ui.gas_graph.plot(name=gas,pen=self.pens[gas])

        # Main loop timer used for queue execution.
        self.loop_timer = QtCore.QTimer()
        self.loop_timer.setInterval(250)
        self.loop_timer.timeout.connect(self.ExecuteQueue)
        self.loop_timer.start()

        self.queue = []
        self.log_data = {}
        self.ramping = False
        self.curr_temp = 0
        self.temp_setpoint = 0
        self.gas_setpoints = []
        self.step = []
        self.step_duration = 0
        self.recipe_start_time = time.time()

        self.curr_recipe = None
        self.running = False
        self.log_initialize = False
        self.log_period = 1

        self.plot_data = pd.DataFrame()
        self.plot_history = 120
        self.params = ['Temp','Ethylene','Argon','Helium','Hydrogen']

    def ExecuteQueue(self):
        '''
        Contains the logic for how the queue should be handled and executed.
        '''
        empty = len(self.queue) == 0
        if empty:
            # If the queue is empty, we need to add tasks to it.
            if self.running:
                if self.ramping:
                    temp_reached = abs(self.curr_temp-self.temp_setpoint) < 2
                    if temp_reached:
                        # We have reached temperature, append all the log points
                        # for the duration of the recipe step to the queue.
                        self.AppendStepLogpoints()
                        self.ramping = False
                    else:
                        # We have not reached the step temperature and are still
                        # ramping.  Append a single query of all parameters to 
                        # the queue.
                        self.RampPoll() 
                else:
                    # We are finished with a step and need to begin a new one.
                    # Append the setpoints for the next step to the queue.
                    self.AppendSetpoints()
                    self.ramping = True
            else:
                # In the event that a recipe is not running, we would still like
                # to monitor the devices.  We do that with RampPoll()
                self.RampPoll()
        else:
            # There are tasks in the queue - we use a loop in case there are
            # multiple tasks ready for execution.
            while not empty:
                task_ready = self.queue[0].timestamp < time.time()
                if task_ready:
                    task = self.queue.pop(0)
                    reply = task.Execute()
                    if reply:
                        self.log_data.update({task.fieldname:reply})
                        # If we have a complete set of plot points to update, 
                        # we do so here.
                        # print(self.log_data)
                        # print(self.params)
                        if all(field in self.log_data for field in self.params):
                            print('Time to update plots')
                            print(self.log_data)
                            print(self.params)
                            self.log_data.update({'Time':time.time()-self.recipe_start_time})
                            self.plot_data = self.plot_data.append(self.log_data,ignore_index=True)
                            self.UpdatePlots()
                            # If the recipe is running, we save data to a file.
                            if self.running:
                                self.curr_temp = self.log_data['Temp']                                
                                self.AppendToLog()
                            self.log_data = {}
                    # Make sure the queue isn't empty to avoid an IndexError
                    empty = len(self.queue) == 0
                else:
                    # If no task is ready, break out of the loop.
                    break

    def RampPoll(self):
        timestamp = time.time()+self.log_period
        self.queue.append(QueueItem(self.furnace.QueryTemp,timestamp,fieldname='Temp'))
        for gas in self.MFCs:
            self.queue.append(QueueItem(self.MFCs[gas].QueryFlow,timestamp,fieldname=gas))

    def AppendSetpoints(self):
        # Grab the next step, terminate the recipe if no steps are left.
        try:
            self.step = self.curr_recipe.steps.pop(0)
        except IndexError:
            self.StopRecipe()
            return
        timestamp = time.time()
        self.step_duration = self.step[0]
        self.temp_setpoint = self.step[1]
        i = 0
        self.gas_setpoints = []
        for gas in self.MFCs:
            self.gas_setpoints.append(self.step[i+2])
            self.queue.append(QueueItem(self.MFCs[gas].SetFlow,timestamp,params=self.gas_setpoints[i],fieldname=gas))
            i = i + 1
        self.queue.append(QueueItem(self.furnace.SetTemp,timestamp,params=self.temp_setpoint,fieldname='Temp'))

    def AppendManualSetpoints(self,manual_gases,manual_temp):
        timestamp = time.time()
        for gas in manual_gases:
            self.queue.append(QueueItem(self.MFCs[gas].SetFlow,timestamp,params=manual_gases[gas],fieldname=gas))
        if manual_temp:
            self.queue.append(QueueItem(self.furnace.SetTemp,timestamp,params=manual_temp,fieldname='Temp'))

    def AppendStepLogpoints(self):

        timestamps = [i*self.log_period + time.time() for i in range(int(self.step_duration/self.log_period))]
        for timestamp in timestamps:
            self.queue.append(QueueItem(self.furnace.QueryTemp,timestamp,fieldname='Temp'))
            for gas in self.MFCs:
                self.queue.append(QueueItem(self.MFCs[gas].QueryFlow,timestamp,fieldname=gas))

    def AppendToLog(self):
        # If this is the first time writing to the log, delete the file contents
        # if that file already exists.
        if self.log_initialize == False:
            with open('test_log','w') as file:
                # By taking no action, we will delete the file's contents
                pass
        
        # print(self.log_data)
        # names = self.curr_recipe.params
        # names.append('Time')
        # print(names)
        # print(self.curr_recipe.params)
        with open('test_log','a') as file:
            log_writer = csv.DictWriter(file, fieldnames=self.log_data.keys())
            if self.log_initialize == False:
                file.write(time.ctime() + '\n')
                log_writer.writeheader()
                self.log_initialize = True
            log_writer.writerow(self.log_data)
    
    def save_recipe(self):
        
        # create a 2D list of the ui fields we will save to the recipe file
        ui_fields = self.return_ui_fields()
        
        # write the meta data in the header
        text_to_save = []

        # set an author name if there isn't one already
        if self.ui.label_author.text() == 'Author: N/A':
            author, ok = QtWidgets.QInputDialog.getText(self,'Author','Enter the name of the recipe\'s author:')
            if ok:
                self.ui.label_author.setText('Author: ' + author)
                text_to_save += ['#Author: ' + author + '\n']
        else:
            text_to_save += ['#' + self.ui.label_author.text() + '\n']
        
        # set recipe creation date as current date if it's a new recipe
        if self.ui.label_creation_date.text() == 'Creation Date: N/A':
            self.ui.label_creation_date.setText('Creation Date: ' + str(date.today()))
            text_to_save += ['#Creation Date: ' + str(date.today()) + '\n']
        else:
            text_to_save += ['#' + self.ui.label_creation_date.text() + '\n']

        # set gases if they haven't been set yet
        if self.ui.label_gas_1.text() == 'Gas 1':
            gas_text = '#Columns:'
            gas_1, ok = QtWidgets.QInputDialog.getText(self,'Gas 1','What is the first gas?')
            if ok:
                self.ui.label_gas_1.setText(gas_1)
                gas_text += gas_1 + ','
            gas_2, ok = QtWidgets.QInputDialog.getText(self,'Gas 2','What is the second gas?')
            if ok:
                self.ui.label_gas_2.setText(gas_2)
                gas_text += gas_2 + ','
            gas_3, ok = QtWidgets.QInputDialog.getText(self,'Gas 3','What is the third gas?')
            if ok:
                self.ui.label_gas_3.setText(gas_3)
                gas_text += gas_3 + '\n'
            text_to_save += [gas_text]
        else:
            text_to_save += ['#Columns:' + self.ui.label_gas_1.text() + ',' + self.ui.label_gas_2.text() + ',' + self.ui.label_gas_3.text() + '\n']
        
        # update the tracker for when the recipe was last modified
        self.ui.label_last_updated.setText('Last Modified: ' + str(date.today()))
        text_to_save += ['#Last Modified: ' + str(date.today()) + '\n']
        
        # read the values in the ui fields and write them to 2D list of strings
        for line in ui_fields:
            # # add a new line to the file
            text_to_save += ['']
            
            for field in line:
                text_to_save[-1] += field.text() + ','
            text_to_save[-1] = text_to_save[-1][:-1] + '\n'      # remove final comma and add new line char
            # i += 1

        # show save file dialogue and write file path to fileName variable
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
                        None,
                        "Save File As",
                        "",
                        "All Files (*);;Python Files (*.py)",
                        options=options)
        
        # overwrite file
        with open(fileName,'w') as recipe:
            recipe.writelines(text_to_save)

    def OpenRecipe(self):        
        # Show open file dialogue and write file path to fileName variable.
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(
                        None,
                        "Open File",
                        "",
                        "All Files (*);;Python Files (*.py)",
                        options=options)
        
        # Create a 2D list of the ui fields we will modify with the recipe file.
        ui_fields = [[self.ui.lineEdit_time_1,self.ui.lineEdit_param1_1,self.ui.lineEdit_param2_1,self.ui.lineEdit_param3_1,self.ui.lineEdit_param4_1,self.ui.lineEdit_param5_1],
                    [self.ui.lineEdit_time_2,self.ui.lineEdit_param1_2,self.ui.lineEdit_param2_2,self.ui.lineEdit_param3_2,self.ui.lineEdit_param4_2,self.ui.lineEdit_param5_2],
                    [self.ui.lineEdit_time_3,self.ui.lineEdit_param1_3,self.ui.lineEdit_param2_3,self.ui.lineEdit_param3_3,self.ui.lineEdit_param4_3,self.ui.lineEdit_param5_3],
                    [self.ui.lineEdit_time_4,self.ui.lineEdit_param1_4,self.ui.lineEdit_param2_4,self.ui.lineEdit_param3_4,self.ui.lineEdit_param4_4,self.ui.lineEdit_param5_4],
                    [self.ui.lineEdit_time_5,self.ui.lineEdit_param1_5,self.ui.lineEdit_param2_5,self.ui.lineEdit_param3_5,self.ui.lineEdit_param4_5,self.ui.lineEdit_param5_5],
                    [self.ui.lineEdit_time_6,self.ui.lineEdit_param1_6,self.ui.lineEdit_param2_6,self.ui.lineEdit_param3_6,self.ui.lineEdit_param4_6,self.ui.lineEdit_param5_6],
                    [self.ui.lineEdit_time_7,self.ui.lineEdit_param1_7,self.ui.lineEdit_param2_7,self.ui.lineEdit_param3_7,self.ui.lineEdit_param4_7,self.ui.lineEdit_param5_7],
                    [self.ui.lineEdit_time_8,self.ui.lineEdit_param1_8,self.ui.lineEdit_param2_8,self.ui.lineEdit_param3_8,self.ui.lineEdit_param4_8,self.ui.lineEdit_param5_8],
                    [self.ui.lineEdit_time_9,self.ui.lineEdit_param1_9,self.ui.lineEdit_param2_9,self.ui.lineEdit_param3_9,self.ui.lineEdit_param4_9,self.ui.lineEdit_param5_9],
                    [self.ui.lineEdit_time_10,self.ui.lineEdit_param1_10,self.ui.lineEdit_param2_10,self.ui.lineEdit_param3_10,self.ui.lineEdit_param4_10,self.ui.lineEdit_param5_10]
                    ]

        steps = []

        # open file and copy lines to fields in GUI
        with open(fileName, 'r') as recipe:
            for line in recipe:
                if line[0:8] == '#Author:':
                    author = line[1:-1]
                elif line[0:15] == '#Creation Date:':
                    creation_date = line[1:-1]
                elif line[0:15] == '#Last Modified:':
                    last_modified = line[1:-1]
                elif line[0:9] == '#Columns:':
                    no_spaces = line.replace(' ','')
                    columns = no_spaces[9:-1].split(',')
                elif line[0] != '#':
                    steps.append(line[:-1].split(','))

        # Update UI recipe values
        i = 0
        for step in steps:
            j = 0
            for field in ui_fields[i]:
                try:
                    field.setText(step[j])
                except IndexError:
                    break
                j = j+1
            i = i+1
        
        # Convert strings to numbers.
        steps = [[float(j) for j in i] for i in steps]
        
        # set the meta data display in the ui to show the metadata in the text file
        self.ui.label_author.setText(author)
        self.ui.label_creation_date.setText(creation_date)
        self.ui.label_last_updated.setText(last_modified)

        # set the UI labels
        column_labels = [self.ui.column_1_label,
            self.ui.column_2_label,
            self.ui.column_3_label,
            self.ui.column_4_label,
            self.ui.column_5_label
            ]
        manual_labels = [self.ui.label_gas_4,
            self.ui.label_gas_5,
            self.ui.label_gas_6
            ]
        i = 0
        j = 0
        for column in columns:
            if column == 'Time':
                continue
            if column != 'Temp':
                manual_labels[j].setText(column + ':')
                j += 1
            column_labels[i].setText(column)
            i += 1

        # Update devices based on what's required by the recipe.
        if 'Temp' not in columns:
            self.furnace = None

        to_delete = []
        for gas in self.MFCs:
            if gas not in columns:
                to_delete.append(gas)

        for device in to_delete:
            del self.MFCs[device]

        # print('Columns: ')

        # print(columns)
        # Initialize the recipe object
        self.curr_recipe = Recipe(steps,columns,self.furnace,self.MFCs,self.press_trans)
        # print(self.curr_recipe.params)
        columns.remove('Time')
        # print(self.curr_recipe.params)

        self.params = columns
        print('self.params')
        print(self.params)

        # Clear the gas graph and re-plot
        self.ui.gas_graph.clear()
        for gas in self.MFCs:
            self.gas_lines[gas] = self.ui.gas_graph.plot(name=gas,pen=self.pens[gas])

        #Clear the temp graph and re-plot
        self.ui.temp_graph.clear()
        self.temp_line = self.ui.temp_graph.plot(pen=self.pens['Ethylene'])
    
    def UpdatePlots(self):
        # update the variables by chopping off the first value and adding one on the end
        # print(self.plot_data.iloc[-10:])
        start_time = self.plot_data['Time'].iloc[-1]-self.plot_history
        plot_time = self.plot_data['Time'][self.plot_data['Time']>start_time]
        plot_temp = self.plot_data['Temp'][self.plot_data['Time']>start_time]
        plot_time.reset_index(drop=True,inplace=True)
        plot_temp.reset_index(drop=True,inplace=True)
        # print(plot_time)
        # print(plot_temp)

        # update the plots
        self.temp_line.setData(plot_time,plot_temp)
        for gas in self.MFCs:
            gas_flow = self.plot_data[gas][self.plot_data['Time']>start_time]
            gas_flow.reset_index(drop=True,inplace=True)
            self.gas_lines[gas].setData(plot_time,gas_flow)

    def start_recipe(self):
        self.ui.label_recipe_status.setText("<html><head/><body><p>Recipe \
            Status: <span style=\" font-weight:600;\">RUNNING</span></p></body>\
            </html>")
        self.running = True
        self.recipe_start_time = time.time()
        self.log_initialize = False

    def StopRecipe(self):
        self.ui.label_recipe_status.setText("<html><head/><body><p>Recipe \
            Status: <span style=\" font-weight:600;\">STOPPED</span></p></body>\
            </html>")
        self.running = False

    def apply_setpoints(self):
        manual_gas_keys = []
        manual_gas_values = []
        manual_temp = None
        if self.ui.manual_temp.text() != '':
            self.ui.label_temp_setpoint.setText('<html><head/><body><p>Temp.: </p></body></html>' + self.ui.manual_temp.text() + '<html><head/><body><p><span style=\" vertical-align:super;\">o</span>C</p></body></html>' )
            manual_temp = float(self.ui.manual_temp.text())
        if self.ui.manual_gas1.text() != '':
            self.ui.label_gas_1_setpoint.setText('Gas 1: ' + self.ui.manual_gas1.text() + ' sccm')
            manual_gas_keys.append(self.ui.label_gas_4.text()[:-1])
            manual_gas_values.append(float(self.ui.manual_gas1.text()))
        if self.ui.manual_gas2.text() != '':
            self.ui.label_gas_2_setpoint.setText('Gas 2: ' + self.ui.manual_gas2.text() + ' sccm')
            manual_gas_keys.append(self.ui.label_gas_5.text()[:-1])
            manual_gas_values.append(float(self.ui.manual_gas2.text()))
        if self.ui.manual_gas3.text() != '':
            self.ui.label_gas_3_setpoint.setText('Gas 3: ' + self.ui.manual_gas3.text() + ' sccm')
            manual_gas_keys.append(self.ui.label_gas_6.text()[:-1])
            manual_gas_values.append(float(self.ui.manual_gas3.text()))

        manual_gases = dict(zip(manual_gas_keys,manual_gas_values))
        self.AppendManualSetpoints(manual_gases,manual_temp)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = cvd_control()
    window.show()
    app.exec_()