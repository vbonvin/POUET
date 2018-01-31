"""
Launch the application, link POUET functions to the design
"""


from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import obs, meteo, run
import design
from astropy import units as u


class POUET(QtWidgets.QMainWindow, design.Ui_POUET):


    def __init__(self, parent=None):
        super(POUET, self).__init__(parent)
        self.setupUi(self)

        # add here all the connections to the functions below
        self.retrieveObs.clicked.connect(self.retrieve_obs)

        # startup tings todo: once happy, put that in a function in run.py
        self.currentmeteo = meteo.Meteo(name='LaSilla', cloudscheck=True, debugmode=True)

        # testing stuff at startup...
        """
        filepath = '2m2lenses.rdb'
        self.observables = obs.rdbimport(filepath, obsprogram="lens")
        run.refresh_status(self.observables, self.currentmeteo)
        for o in self.observables:
            o.get_observability(self.currentmeteo, cloudscheck=True, verbose=False)
        """

    def retrieve_obs(self):
        model = QtGui.QStandardItemModel(self.listObs)

        self.listObs.clearSpans()
        filepath = QtWidgets.QFileDialog.getOpenFileName(self,
                                                "Select a file")[0]

        #todo: implement an obsprogram retrieve function
        self.observables = obs.rdbimport(filepath, obsprogram="lens")
        run.refresh_status(self.observables, self.currentmeteo)

        for o in self.observables:
            o.get_observability(self.currentmeteo, cloudscheck=True, verbose=False)

            name = QtGui.QStandardItem(o.name)
            alpha = QtGui.QStandardItem(o.alpha.to_string(unit=u.hour, sep=':'))
            delta = QtGui.QStandardItem(o.delta.to_string(unit=u.degree, sep=':'))
            observability = QtGui.QStandardItem(str(o.observability))

            name.setCheckable(True)
            model.appendRow([name, alpha, delta, observability])


        self.listObs.setModel(model)




def main():
    app = QtWidgets.QApplication(sys.argv)  # A new instance of QApplication
    form = POUET()                 # We set the form to be our ExampleApp (design)
    form.show()                         # Show the form
    app.exec_()                         # and execute the app



if __name__ == '__main__':
    main()