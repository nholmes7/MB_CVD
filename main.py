# import our Ui_MainWindow class from our Qt Designer generated file
from gui import Ui_MainWindow
from datetime import date
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
import pyqtgraph

# define a new class which inherits from the QMainWindow object - not a default python object like our Ui_MainWindow class
class cvd_control(QtWidgets.QMainWindow): 
    
    # override the init method
    def __init__(self, *args, **kwargs):
        # whenever you override the init method in a Qt object you need to run super().__init__ and pass in any arguments that were passed in so it still behaves like a Qt widget
        super().__init__(*args, **kwargs)
        
        # setupUi builds the GUI onto the cvd_control QMainWindow object
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # make required connections
        self.ui.save_button.clicked.connect(self.save_recipe)
        self.ui.open_button.clicked.connect(self.open_recipe)

        # configure the plots and their settings
        background_colour = self.palette().color(QtGui.QPalette.Window)         # gets the background window colour to use as teh plot background colour
        self.ui.temp_graph.setBackground(background_colour)
        self.ui.gas_graph.setBackground(background_colour)
        self.ui.temp_graph.setTitle('Temperature',color='k',size = '16pt')
        self.ui.gas_graph.setTitle('Flow Rates',color='k',size = '16pt')
        self.ui.gas_graph.addLegend(offset = (1,-150))
        styles = {"color": 'k', "font-size": "14px"}
        self.ui.temp_graph.setLabel("bottom", "Time (s)", **styles)
        self.ui.gas_graph.setLabel("bottom", "Time (s)", **styles)
        
        # put some static data onto the plots
        self.plot([1,2,3,4,5,6,7,8,9,10], [30,32,34,32,33,31,29,32,35,45],[30,32,34,32,33,31,29,32,35,45],[20,37,32,36,37,38,23,34,36,42],[34,35,37,38,34,33,26,35,34,48])

    def return_ui_fields(self):
        ui_fields = [[self.ui.lineEdit_time_1,self.ui.lineEdit_temp_1,self.ui.lineEdit_heFlow_1,self.ui.lineEdit_h2Flow_1,self.ui.lineEdit_c2h4Flow_1],
                     [self.ui.lineEdit_time_2,self.ui.lineEdit_temp_2,self.ui.lineEdit_heFlow_2,self.ui.lineEdit_h2Flow_2,self.ui.lineEdit_c2h4Flow_2],
                     [self.ui.lineEdit_time_3,self.ui.lineEdit_temp_3,self.ui.lineEdit_heFlow_3,self.ui.lineEdit_h2Flow_3,self.ui.lineEdit_c2h4Flow_3]
                    ]
        return ui_fields
    
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

    def open_recipe(self):
        
        # show open file dialogue and write selected file path to fileName variable
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(
                        None,
                        "Open File",
                        "",
                        "All Files (*);;Python Files (*.py)",
                        options=options)
        
        # create a 2D list of the ui fields we will modify with the recipe file
        ui_fields = self.return_ui_fields()
        
        i = 0   # loop counter

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
                    column_names = []
                    column_names += line[9:-1].split(',')
                elif line[0] != '#':                        # values for the actual recipe
                    recipe_fields = []
                    recipe_fields += line[:-1].split(',')   # [:-1] is to exclude new line char
                    j = 0
                    for field in ui_fields[i]:
                        field.setText(recipe_fields[j])
                        j += 1
                    i += 1
        
        # set the meta data display in the ui to show the metadata in the text file
        self.ui.label_author.setText(author)
        self.ui.label_creation_date.setText(creation_date)
        self.ui.label_last_updated.setText(last_modified)

        # set the labels for the gas columns from the recipe text file
        column_labels = [self.ui.label_gas_1,self.ui.label_gas_2,self.ui.label_gas_3]
        i = 0
        for column in column_labels:
            column.setText(column_names[i])
            i += 1

    def plot(self,time,temp,gas_1_flow,gas_2_flow,gas_3_flow):
        pen_1 = pyqtgraph.mkPen(color='#7a0177',width=2)
        pen_2 = pyqtgraph.mkPen(color='#c51b8a',width=2)
        pen_3 = pyqtgraph.mkPen(color='#f768a1',width=2)
        self.ui.temp_graph.plot(time,temp,pen=pen_1)
        self.ui.gas_graph.plot(time,gas_1_flow,name='Gas 1',pen=pen_1)
        self.ui.gas_graph.plot(time,gas_2_flow,name='Gas 2',pen=pen_2)
        self.ui.gas_graph.plot(time,gas_3_flow,name='Gas 3',pen=pen_3)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = cvd_control()
    window.show()
    app.exec_()