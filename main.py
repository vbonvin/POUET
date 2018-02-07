"""
Launch the application, link POUET functions to the design
"""


from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import obs, meteo, run
import design
from astropy import units as u
from astropy.time import Time

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MyLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setGeometry(parent.geometry())
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)





class POUET(QtWidgets.QMainWindow, design.Ui_POUET):
    def __init__(self, parent=None):
        super(POUET, self).__init__(parent)
        self.setupUi(self)


        # logger startup...
        logTextBox = MyLogger(self.verticalLayoutWidget)
        logTextBox.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m-%d-%Y %H:%M:%S'))
        logger.addHandler(logTextBox)
        logger.info('Startup...')

        # signal and slots init...
        self.retrieveObs.clicked.connect(self.retrieve_obs)
        self.weatherRefresh.clicked.connect(self.weather_refresh)
        self.allSkyRefresh.clicked.connect(self.allsky_refresh)
        self.checkObsStatus.clicked.connect(self.check_obs_status)

        #todo: find how to share the same logger for all modules, or how to send all loggers output to my widget
        self.currentmeteo = run.startup(name='LaSilla', cloudscheck=False, debugmode=True)

        # testing stuff at startup...

        """
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
        try:
            self.observables = obs.rdbimport(filepath, obsprogram="lens")
            run.refresh_status(self.currentmeteo, self.observables)


            for o in self.observables:
                o.get_observability(self.currentmeteo, cloudscheck=False, verbose=False)

                name = QtGui.QStandardItem(o.name)
                alpha = QtGui.QStandardItem(o.alpha.to_string(unit=u.hour, sep=':'))
                delta = QtGui.QStandardItem(o.delta.to_string(unit=u.degree, sep=':'))
                observability = QtGui.QStandardItem(str(o.observability))

                name.setCheckable(True)
                model.appendRow([name, alpha, delta, observability])
                model.setHorizontalHeaderLabels(['Name', 'Alpha', 'Delta', 'Observability'])


            self.listObs.setModel(model)
            logger.info("%s Sucessfully loaded" % filepath)
            #todo: replace by redirecting the message to a logger
            self.statusLabel.setStyleSheet('color: green')
            self.statusLabel.setText("%s \n Sucessfully loaded" % filepath)

        except:
            logger.error("%s not loaded - format unknown" % filepath)
            self.statusLabel.setStyleSheet('color: red')
            self.statusLabel.setText("%s \n Format unknown" % filepath)


    def check_obs_status(self):
        """

        :return:
        """

        #0 is not checked, 1 is partially checked, 2 is checked --> 0 or 2 for us
        model = self.listObs.model()

        statuses = [model.item(i, 0).checkState() for i in range(model.rowCount())]
        print(statuses)



    def weather_refresh(self, refresh_time="now"):
        #todo: link refresh_time to a button or widget on the interface ? Could be useful for update on future time.

        if refresh_time == "now":
            obs_time = Time.now()
        else:
            obs_time = Time.now()
            pass

        run.refresh_status(meteo=self.currentmeteo, minimal=False if refresh_time == "now" else True, obs_time=obs_time)
        self.weatherWindSpeedValue.setText(str('{:2.1f}'.format(self.currentmeteo.windspeed)))
        self.weatherWindDirectionValue.setText(str('{:3d}'.format(int(self.currentmeteo.winddirection))))
        self.weatherTemperatureValue.setText(str('hi!'))
        self.weatherLastUpdateValue.setText(str(obs_time.value).split('.')[0])


    def allsky_refresh(self):

        #todo: I manage to display the image, but cannot resize it for some reason. Only the first refresh works, after that more refresh do not update nor the image neither the new date...

        run.refresh_status(meteo=self.currentmeteo, minimal=False)
        pixmap = QtGui.QPixmap(self.currentmeteo.allsky.fimage)
        #todo: for some reasons, this does not work... ?
        pixmap.scaled(461, 346)
        scene = QtWidgets.QGraphicsScene()
        scene.addPixmap(pixmap)
        self.allSkyView.setScene(scene)
        self.allSkyUpdateValue.setText(str(self.currentmeteo.time.value).split('.')[0])
        logger.info("updated allsky")




def main():
    app = QtWidgets.QApplication(sys.argv)  # A new instance of QApplication
    form = POUET()                 # We set the form to be our ExampleApp (design)
    form.show()                         # Show the form
    app.exec_()                         # and execute the app



if __name__ == '__main__':
    main()