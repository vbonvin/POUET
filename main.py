"""
Launch the application, link POUET functions to the design
"""


from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import obs, meteo
import design


class POUET(QtWidgets.QMainWindow, design.Ui_POUET):
    def __init__(self, parent=None):
        super(POUET, self).__init__(parent)
        self.setupUi(self)

        # add here all the connections to the functions below
        self.retrieveObs.clicked.connect(self.retrieve_obs)
        self.clouds_refresh_now.clicked.connect(self.refresh_clouds)


    def retrieve_obs(self):
        self.listObs.clear()
        filepath = QtWidgets.QFileDialog.getOpenFileName(self,
                                                "Select a file")[0]

        #todo: implement an obsprogram retrieve function
        observables = obs.rdbimport(filepath)

        for o in observables:
            self.listObs.addItem(o.name)


    def refresh_clouds(self):
        pass


def main():
    app = QtWidgets.QApplication(sys.argv)  # A new instance of QApplication
    form = POUET()                 # We set the form to be our ExampleApp (design)
    form.show()                         # Show the form
    app.exec_()                         # and execute the app





if __name__ == '__main__':
    main()