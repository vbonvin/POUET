"""
Launch the application, link POUET functions to the design
"""


from PyQt5 import QtCore, QtGui, QtWidgets
import os, sys
import obs, meteo, run
import design
from astropy import units as u
from astropy.time import Time, TimeDelta
import copy

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

COLORWARN = "orange"
COLORLIMIT = "red"

class MyLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setGeometry(parent.geometry())
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class MultiPopup(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(460, 320)


        layout = QtWidgets.QGridLayout()

        self.nameColLabel = QtWidgets.QLabel("Name:")
        self.nameColValues = QtWidgets.QComboBox()
        self.nameColValues.addItems(["name1", "name2"])

        layout.addWidget(self.nameColLabel, 0, 0)
        layout.addWidget(self.nameColValues, 0, 1)

        self.alphaColLabel = QtWidgets.QLabel("Alpha:")
        self.alphaColValues = QtWidgets.QComboBox()
        self.alphaColValues.addItems(["alpha1", "alpha2"])

        layout.addWidget(self.alphaColLabel, 1, 0)
        layout.addWidget(self.alphaColValues, 1, 1)

        self.okButton = QtWidgets.QPushButton('OK', self)
        self.okButton.clicked.connect(self.saveandclose)
        layout.addWidget(self.okButton, 2, 0)


        self.cancelButton = QtWidgets.QPushButton()
        self.cancelButton.setText('Cancel')
        layout.addWidget(self.cancelButton, 2, 1)

        self.setLayout(layout)
        self.exec()

    def saveandclose(self):
        self.alpha_col = self.alphaColValues.currentIndex()
        self.accept()




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
        self.weatherDisplayRefresh.clicked.connect(self.weather_display)
        self.allSkyRefresh.clicked.connect(self.allsky_refresh)
        self.checkObsStatus.clicked.connect(self.check_obs_status)

        #todo: find how to share the same logger for all modules, or how to send all loggers output to my widget
        self.currentmeteo = run.startup(name='LaSilla', cloudscheck=False, debugmode=True)
        
        self.site_display()
        self.weather_display()
        # testing stuff at startup...

        """
        run.refresh_status(self.observables, self.currentmeteo)
        for o in self.observables:
            o.get_observability(self.currentmeteo, cloudscheck=True, verbose=False)
        """

        self.popup = MultiPopup()
        self.popup.show()

        print(self.popup.alpha_col)
        sys.exit()

    def retrieve_obs(self):

        logmsg = ''

        model = QtGui.QStandardItemModel(self.listObs)

        self.listObs.clearSpans()
        filepath = QtWidgets.QFileDialog.getOpenFileName(self, "Select a file")[0]

        logmsg += '%s ' % filepath

        ext = os.path.splitext(filepath)[1]

        if ext != 'pouet':  # then it's a first load:
            obsprogramlist = run.retrieve_obsprogramlist()
            obsprogramnames = (o["name"] for o in obsprogramlist)

            self.popup = MultiPopup()
            self.popup.show()


            self.popup = QtWidgets.QInputDialog()
            #todo rename Cancel button as default if possible
            obsprogram, ok = self.popup.getItem(self, "Select an observing program", "Existing programs - hit Cancel to use default", obsprogramnames, 0, False)


            if not ok:
                obsprogram = None
                logmsg += 'as default '

            else:
                logmsg += 'as %s ' % obsprogram

        else:  # then it's a pouet file. We assume it follows our own convention for the rdbimport
            pass


        try:
            if ext != 'pouet':
                self.observables = obs.rdbimport(filepath, obsprogram=obsprogram, namecol=namecol, alphacol=alphacol, deltacol=deltacol, obsprogramcol=obsprogramcol)
                run.refresh_status(self.currentmeteo, self.observables)

            else:
                self.observables = obs.rdbimport(filepath, obsprogram=obsprogram)
                run.refresh_status(self.currentmeteo, self.observables)


            for o in self.observables:
                o.get_observability(self.currentmeteo, cloudscheck=False, verbose=False)

                name = QtGui.QStandardItem(o.name)
                alpha = QtGui.QStandardItem(o.alpha.to_string(unit=u.hour, sep=':'))
                delta = QtGui.QStandardItem(o.delta.to_string(unit=u.degree, sep=':'))
                observability = QtGui.QStandardItem(str(o.observability))
                obsprogram = QtGui.QStandardItem(o.obsprogram)

                name.setCheckable(True)
                model.appendRow([name, alpha, delta, observability, obsprogram])
                model.setHorizontalHeaderLabels(['Name', 'Alpha', 'Delta', 'Observability', 'Program'])


            self.listObs.setModel(model)
            logmsg += 'successfully loaded'
            logger.info(logmsg)
            #todo: replace by redirecting the message to a logger
            self.statusLabel.setStyleSheet('color: green')
            self.statusLabel.setText("%s \n Sucessfully loaded" % filepath)

        except:
            logmsg += ' not loaded - format unknown'
            logger.error(logmsg)
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


    def weather_display(self):
        
        if not self.currentmeteo.lastest_weatherupdate_time is None and (Time.now() - self.currentmeteo.lastest_weatherupdate_time).to(u.s).value < 2:
            logger.info("Last weather report was downloaded more recently than 2 seconds ago, I don't download it again")
        else:
            self.currentmeteo.updateweather()
        
        self.weatherWindSpeedValue.setText(str('{:2.1f}'.format(self.currentmeteo.windspeed)))
        if float(self.currentmeteo.location.get("weather", "windLimitLevel")) < self.currentmeteo.windspeed:
            self.weatherWindSpeedValue.setStyleSheet("QLabel { color : %s; }" % format(COLORLIMIT))
        elif float(self.currentmeteo.location.get("weather", "windWarnLevel")) < self.currentmeteo.windspeed:
            self.weatherWindSpeedValue.setStyleSheet("QLabel { color : %s; }" % format(COLORWARN))
         
        self.weatherWindDirectionValue.setText(str('{:3d}'.format(int(self.currentmeteo.winddirection))))
        
        self.weatherTemperatureValue.setText(str('{:2.1f}'.format(int(self.currentmeteo.temperature))))
        
        self.weatherHumidityValue.setText(str('{:3d}'.format(int(self.currentmeteo.humidity))))
        if float(self.currentmeteo.location.get("weather", "humidityLimitLevel")) < self.currentmeteo.humidity:
            self.weatherHumidityValue.setStyleSheet("QLabel { color : %s; }" % format(COLORLIMIT))
        elif float(self.currentmeteo.location.get("weather", "humidityWarnLevel")) < self.currentmeteo.humidity:
            self.weatherHumidityValue.setStyleSheet("QLabel { color : %s; }" % format(COLORWARN))
        
        self.weatherLastUpdateValue.setText(str(self.currentmeteo.lastest_weatherupdate_time).split('.')[0])


    def site_display(self):
        
        self.siteLocationValue.setText(str('Lat={:s}\tLon={:s}'.format(self.currentmeteo.location.get("location", "longitude"), self.currentmeteo.location.get("location", "latitude"))))
        
        #TODO: Get the time from configTime !!!
        obs_time = Time.now()
        logger.warning("Update time here too!!")
        
        #-------------------------------------------------------- Night here only
        
        obs_time.format = 'iso'
        obs_time.out_subfmt = 'date'
        
        ref_time = Time('%s 12:00:00' % obs_time, format='iso', scale='utc') #5h UT is approx. the middle of the night
        
        is_after_midday = (obs_time-ref_time).value > 0
        
        if is_after_midday:
            day_before = copy.copy(obs_time)
            obs_time += TimeDelta(1, format="jd")
            day_after = obs_time
        else:
            day_after = obs_time
            day_before = obs_time - TimeDelta(1, format="jd")
            
            
        print (obs_time)

        sunrise, sunset = self.currentmeteo.get_twilights(obs_time, twilight='civil')
        self.nightStartCivilValue.setText(str('{:s}'.format(str(sunset))))
        self.nightEndCivilValue.setText(str('{:s}'.format(str(sunrise))))
        
        sunrise, sunset = self.currentmeteo.get_twilights(obs_time, twilight='nautical')
        self.nightStartNauticalValue.setText(str('{:s}'.format(str(sunset))))
        self.nightEndNauticalValue.setText(str('{:s}'.format(str(sunrise))))
        
        sunrise, sunset = self.currentmeteo.get_twilights(obs_time, twilight='astronomical')
        self.nightStartAstroValue.setText(str('{:s}'.format(str(sunset))))
        self.nightEndAstroValue.setText(str('{:s}'.format(str(sunrise))))
        
        self.nightLastUpdateValueBefore.setText(str(day_before).split('.')[0])
        self.nightLastUpdateValueAfter.setText(str(day_after).split('.')[0])
        
        #-------------------------------------------------------- Bright objects now
        
        sunAz, sunAlt = self.currentmeteo.get_sun(obs_time)
        sunAlt = sunAlt.to(u.degree).value
        sunAz = sunAz.to(u.degree).value
        
        self.sunCoordinatesValues.setText(str('RA={:s}  DEC={:s}'.format(self.currentmeteo.sun.ra.__str__(), self.currentmeteo.sun.dec.__str__())))
        self.sunAltazValue.setText(str('{:2.1f}°\t{:2.1f}°'.format(sunAlt, sunAz)))
        
        moonAz, moonAlt = self.currentmeteo.get_moon(obs_time)
        moonAlt = moonAlt.to(u.degree).value
        moonAz = moonAz.to(u.degree).value
        
        self.moonCoordinatesValues.setText(str('RA={:s}  DEC={:s}'.format(self.currentmeteo.moon.ra.__str__(), self.currentmeteo.moon.dec.__str__())))
        self.moonAltazValue.setText(str('{:2.1f}°\t{:2.1f}°'.format(moonAlt, moonAz)))
        
        day_after.out_subfmt = 'date_hms'
        self.brightLastUpdateValue.setText(str(obs_time).split('.')[0])

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