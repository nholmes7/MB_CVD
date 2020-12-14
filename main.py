# import our Ui_MainWindow class from our Qt Designer generated file
from test import Ui_MainWindow

from PyQt5 import QtCore
from PyQt5 import QtWidgets

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

    def return_ui_fields(self):
        ui_fields = [[self.ui.lineEdit_time_1,self.ui.lineEdit_temp_1,self.ui.lineEdit_heFlow_1,self.ui.lineEdit_h2Flow_1,self.ui.lineEdit_c2h4Flow_1],
                     [self.ui.lineEdit_time_2,self.ui.lineEdit_temp_2,self.ui.lineEdit_heFlow_2,self.ui.lineEdit_h2Flow_2,self.ui.lineEdit_c2h4Flow_2],
                     [self.ui.lineEdit_time_3,self.ui.lineEdit_temp_3,self.ui.lineEdit_heFlow_3,self.ui.lineEdit_h2Flow_3,self.ui.lineEdit_c2h4Flow_3]
                    ]
        return ui_fields
    
    def save_recipe(self):
        
        # create a 2D list of the ui fields we will save to the recipe file
        ui_fields = self.return_ui_fields()
        
        # read the values in the ui fields and write them to 2D list of strings
        text_to_save = []
        i = 0
        for line in ui_fields:
            # # add a new line to the file if required
            try:
                text_to_save[i]
            except IndexError:
                text_to_save += ['']
            
            for field in line:
                text_to_save[i] += field.text() + ','
            text_to_save[i] = text_to_save[i][:-1] + '\n'      # remove final comma and add new line char
            i += 1

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

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = cvd_control()
    window.show()
    app.exec_()