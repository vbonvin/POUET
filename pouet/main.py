#!/usr/bin/env python
# -*- coding: utf-8 -*- 

"""
Launch the application, link POUET functions to the design
"""


from PyQt5 import QtCore, QtGui, QtWidgets, uic
import os, sys

import obs, run, util, plots

from astropy import units as u
from astropy.time import Time, TimeDelta
import astropy.coordinates.angles as angles
import copy
import ephem

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pylab as plt
from matplotlib.patches import Wedge
from matplotlib import gridspec
from matplotlib.colors import LinearSegmentedColormap

import numpy as np

import logging
mutex = QtCore.QMutex()

import inspect


# define a bunch of hardcoded global variables (bad!) depending on user config

global SETTINGS  # TKU: I know I did it like this, how to do it better (and stay SIMPLE)

herepath = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))

SETTINGS = util.readconfig(os.path.join(herepath, "config/settings.cfg"))

if SETTINGS["display"]["windowsize"] == "regular":
    import design
    visibility_height = 4.0
elif SETTINGS["display"]["windowsize"] == "small":
    import design_small as design
    visibility_height = 2.78
else:
    logging.critical("Windowsize keyword not recognized in settings.cfg. Exiting...")
    sys.exit()




class POUET(QtWidgets.QMainWindow, design.Ui_POUET):
    def __init__(self, parent=None):
        super(POUET, self).__init__(parent)
        self.setupUi(self)
        
        print("Starting up... This can take a minute...")

        # logger startup...
        self._logwriter = LogWriter()
        self._logwriter.dataSent.connect(self.on_threadlog)
        
        self.viewLogs = QtWidgets.QPlainTextEdit(self.verticalLayoutWidget)
        self.viewLogs.setGeometry(self.verticalLayoutWidget.geometry())
        self.viewLogs.setReadOnly(True)

        logTextBox = MyLogger(self._logwriter)
        logTextBox.setFormatter(logging.Formatter(fmt='%(asctime)s | %(levelname)s: %(name)s(%(funcName)s): %(message)s', datefmt='%m-%d-%Y %H:%M:%S'))
        logging.getLogger().addHandler(logTextBox)

        # You can control the logging level
        logging.getLogger().setLevel(logging.DEBUG)

        logging.info('Startup...')
        
        self.allsky_debugmode = False  
        self.name_location = 'LaSilla'
        self.cloudscheck = True
        self.currentmeteo = run.startup(name=self.name_location, cloudscheck=self.cloudscheck, debugmode=self.allsky_debugmode)
        self.set_configTimeNow()
        self.save_Time2obstime()


        self.allsky = AllSkyView(meteo=self.currentmeteo, parent=self.allskyView)
        self.allsky_redisplay()
        self.allskylayer = AllSkyView(meteo=self.currentmeteo, parent=self.allskyViewLayer)
        self.allskylayerTargets = AllSkyView(meteo=self.currentmeteo, parent=self.allskyViewLayerTargets)
        
        self.visibilitytool = VisibilityView(parent=self.visibilityView)
        self.visibilitytool_draw()
        
        self.init_warn_station()
        self.weather_display()
        self.site_display()
        
        # signal and slots init...
        self.loadObs.clicked.connect(self.load_obs)
        self.weatherDisplayRefresh.clicked.connect(self.weather_display)
        self.allSkyRefresh.clicked.connect(self.allsky_refresh)
        self.configCloudsShowLayersValue.clicked.connect(self.allsky_redisplay)
        self.configAutoupdateFreqValue.valueChanged.connect(self.set_timer_interval)
        self.configTimenow.clicked.connect(self.set_configTimeNow)
        self.configUpdate.clicked.connect(self.do_update)
        self.visibilityDraw.clicked.connect(self.visibilitytool_draw)
        self.configDebugModeValue.clicked.connect(self.set_debug_mode)
        self.configCloudsAnalysis.clicked.connect(self.set_cloud_analysis_mode)
        self.updatePlotObs.clicked.connect(self.listObs_plot_targets)
        self.updateSelectall.clicked.connect(self.listObs_selectall)
        self.displaySelectedObs.clicked.connect(self.hide_observables)
        self.displayAllObs.clicked.connect(self.unhide_observables)

        #self.toggleAirmassObs.selfChecked.connect()
        self.visibilitytool.figure.canvas.mpl_connect('motion_notify_event', self.on_visibilitytoolmotion)
        self.listObs.doubleClicked.connect(self.doubleclik_list)
        self.listObs.verticalHeader().sectionDoubleClicked.connect(self.doubleclik_list)

        # Stating timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30000) #trigger every 2 minutes by default.
        self.timer.timeout.connect(self.auto_refresh)
        
        # Some housekeeping stuff...
        self.allskylayerTargets.show_coordinates(150, 150, color="None")
        self.listObs_check_state = 0

        # To handle the all sky in a thread...
        self.threadAllskyUpdate = ThreadAllskyUpdate(parent=self)
        self.threadAllskyUpdate.allskyUpdate.connect(self.on_threadAllskyUpdate)

        # initialize regular expression validators for alpha and delta selecters
        alpha_regexp = QtCore.QRegExp('([01]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]')
        delta_regexp = QtCore.QRegExp('-?[0-8][0-9]:[0-5][0-9]:[0-5][0-9]')

        self.alpha_validator = QtGui.QRegExpValidator(alpha_regexp)
        self.delta_validator = QtGui.QRegExpValidator(delta_regexp)

        # we do not set validators as attribute of QLineEdit as it prevents the user to enter what he wants. Instead, we test against them when the textfield is changed

        self.alphaMinObs.textChanged.connect(self.validate_alpha)
        self.alphaMaxObs.textChanged.connect(self.validate_alpha)

        self.deltaMinObs.textChanged.connect(self.validate_delta)
        self.deltaMaxObs.textChanged.connect(self.validate_delta)

        #todo: initialize the validation at startup - it avoids having to define these flags here
        self.alphaMinObs.isValid = True
        self.alphaMaxObs.isValid = True
        self.deltaMinObs.isValid = True
        self.deltaMaxObs.isValid = True

        # testing stuff at startup...
        herepath = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))

        self.load_obs(filepath=os.path.join(herepath, '../cats/2m2lenses_withobsprogram.pouet'))
        obs_model = self.listObs.model()

        #sys.exit()

    def validate_alpha(self):
        """
        Validate that the user input for the alpha min and max fields are well inside predefined boudaries (00:00:00 to 23:59:59)

        Add a boolean to the sender field (isValid)
        """

        state = self.alpha_validator.validate(self.sender().text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = '#c4df9b'
            self.sender().isValid = True
        elif state == QtGui.QValidator.Intermediate:
            color = '#fff79a'  # yellow
            self.sender().isValid = False
        else:
            color = '#f6989d'  # red
            self.sender().isValid = False

        self.sender().setStyleSheet('QLineEdit { background-color: %s }' % color)



    def validate_delta(self):
        """
        Validate that the user input for the delta min and max fields are well inside predefined boudaries (-89:59:59 to 89:59:59)

        Add a boolean to the sender field (isValid), set to True only when the validator returns an Acceptable
        """

        state = self.delta_validator.validate(self.sender().text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = '#c4df9b'
            self.sender().isValid = True
        elif state == QtGui.QValidator.Intermediate:
            color = '#fff79a'  # yellow
            self.sender().isValid = False
        else:
            color = '#f6989d'  # red
            self.sender().isValid = False

        self.sender().setStyleSheet('QLineEdit { background-color: %s }' % color)


    @QtCore.pyqtSlot(str)
    def on_threadlog(self, msg):
        """
        Helper that writes a message to the log box when prompted from a `logging` call.
        """
        self.viewLogs.appendPlainText(msg)
        
    @QtCore.pyqtSlot(list)
    def on_threadAllskyUpdate(self, sample):
        """
        When an AllSky update is finished, this method is being called. It gets the image from the thread (element 0 in the list `sample`) and displays it.
        """
        
        self.currentmeteo.allsky = sample[0]
        
        self.allskylayer.erase()
        
        self.allsky_redisplay()
        
        self.print_status("All Sky refresh done.")
        
        
    def init_warn_station(self):
        """
        Initialises the weather warning flags for the current observing station
        """
        
        self.station_reached_limit = False
        self.station_reached_warn = False
        self.weather_reached_limit = False
        self.weather_reached_warn = False
        
    def does_warn_station(self):
        """
        Rings the (weather) alarm if there are warning flags by changing the color of the `Station` tab.
        """
        
        if self.station_reached_limit or self.weather_reached_limit:
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.weather), QtCore.QCoreApplication.translate("POUET", "Station (!)"))
            self.changeTabColor(color=SETTINGS['color']['limit'])
        elif self.station_reached_warn or self.weather_reached_warn:
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.weather), QtCore.QCoreApplication.translate("POUET", "Station (!)"))
            self.changeTabColor(color=SETTINGS['color']['warn'])
        else:
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.weather), QtCore.QCoreApplication.translate("POUET", "Station"))
            self.changeTabColor(color=SETTINGS['color']['nominal'])

        
    def changeTabColor(self, color, tab=None):
        """
        Helper to change the font color of a tab.
        
        :param color: a pyqt recognised color
        :param tab: the tab for which to change the color (default: station). Note that you should give the tab widget variable here.
        """
        
        if tab is None:
            tab = self.weather
            
        self.tabWidget.tabBar().setTabTextColor(self.tabWidget.indexOf(tab), QtGui.QColor(color))

    def on_visibilitytoolmotion(self, event):
        """
        When the mouse is hovering over the visibility plot, this shows the same coordinates in the all sky window.
        
        :param event: given by pyqt, contains the coordinates in the visibility window.
        
        .. note:: this is only active if All Sky has an image and difference between obs_time and last all sky refresh is smaller than value defined in settings under `showallskycoordinates` - OR in debug mode.
        """
        
        if event.inaxes != self.visibilitytool.axis: return
        
        if not self.allsky_debugmode and (self.currentmeteo.allsky.last_im_refresh is None or np.abs(self.currentmeteo.time - self.currentmeteo.allsky.last_im_refresh).to(u.s).value / 60. > float(SETTINGS['validity']['showallskycoordinates'])):
            #logging.debug("Not showing coordinates on All Sky, delta time too large")
            return
        
        ra = angles.Angle(event.xdata, unit="hour")
        dec = angles.Angle(event.ydata, unit="deg")
        azimuth, altitude = self.currentmeteo.get_AzAlt(ra, dec, obs_time=self.currentmeteo.time)
        xpix, ypix = self.currentmeteo.allsky.station.get_image_coordinates(azimuth.value, altitude.value)
        self.allskylayer.show_coordinates(xpix, ypix)
        
    def doubleclik_list(self, mi):
        """
        Method that defines what to do when the user double-clics on a observable
        
        :param mi: given by pyqt, represent the list item in focus.
        """
        
        obs_model = self.listObs.model()
        
        try:
            row_id = mi.row()
        except AttributeError:
            row_id = mi
        
        targetname = obs_model.item(row_id, 0).data(0)
        
        # Do we have something better than this search?
        for target in self.observables:
            
            if not target.name == targetname:
                continue
            
            ####################################################
            
            if self.configDoubleClicAirmassValue.checkState() == 2:
            
                self.plot_show = uic.loadUi("dialogPlots.ui")
                
                
                self.plot_show.setWindowTitle("Airmass for {}".format(target.name))
                
                amv = AirmassView(parent=self.plot_show.widget)
                amv.show(target, self.currentmeteo)
                
                self.plot_show.open()
            
            #####################################################
            
            if self.configDoubleClicSkyChartValue.checkState() == 2:
                
                self.print_status('Opening Sky Chart for {}...'.format(target.name), SETTINGS["color"]["warn"])
            
                self.skychart_show = uic.loadUi("dialogSkyChart.ui")
                self.skychart_show.setWindowTitle("Sky chart for {}".format(target.name))
                
                skychart = SkychartView(target=target, parent=self.skychart_show.widget)
                skychart.show()
                
                self.skychart_show.flipNorth.clicked.connect(skychart.flipNorth)
                self.skychart_show.flipEast.clicked.connect(skychart.flipEast)
                self.skychart_show.SurveyBox.currentTextChanged.connect(skychart.changeSurvey)
                self.skychart_show.sizeBox.currentTextChanged.connect(skychart.changeBoxSize)
                self.skychart_show.invertColors.clicked.connect(skychart.invertColors)
                
                self.skychart_show.open()
                
                self.print_status('Sky chart opened.')
    
    def print_status(self, msg, color=None):
        """
        Helper that prints a status in the status box
        
        :param msg: text to display
        :param color: pyqt recognised named color
        """
        
        if color is None:
            color = SETTINGS['color']['nominal']
            
        self.statusLabel.setText(msg)
        self.statusLabel.setStyleSheet('color: {}'.format(color))
        QtWidgets.QApplication.processEvents()
        
    def set_timer_interval(self):
        """
        Helper that sets the auto-refresh frequency when the corresponding field in the `configuration` tab is changed
        """

        interval = self.configAutoupdateFreqValue.value() * 1000 * 60
        self.timer.setInterval(interval)
        logging.debug("Set auto-refresh to {} min".format(self.configAutoupdateFreqValue.value()))
        
    def set_configTimeNow(self):
        """
        Helper that sets the date/time Edit widget to current time when prompted by the `Set to now` button
        """
        
        #get current date and time
        now = QtCore.QDateTime.currentDateTimeUtc()

        #set current date and time to the object
        self.configTime.setDateTime(now)
        
    def save_Time2obstime(self):
        """
        Sets the meteo time object to what the date/time edit widget shows
        """
        
        self.currentmeteo.time = Time(self.configTime.dateTime().toPyDateTime(), scale="utc")
        logging.debug("obs_time is now set to {:s}".format(str(self.currentmeteo.time)))
        
    def set_debug_mode(self):
        """
        Changes the mode to either `debug` or `production`. When in debug, local AllSky and the WeatherReport archive files are used (for the LaSilla station)
        """ 
        
        if self.configDebugModeValue.checkState() == 0:
            goto_mode = False
        else:
            goto_mode = True
        
        if goto_mode != self.allsky_debugmode:
            
            if goto_mode:
                mode="debug"
            else:
                mode="production"
            
            self.print_status("Changing to {} mode...".format(mode), color=SETTINGS['color']['warn'])
            
            self.allsky_debugmode = goto_mode  
            self.currentmeteo = run.startup(name=self.name_location, cloudscheck=self.cloudscheck, debugmode=self.allsky_debugmode)
            self.auto_refresh()
            self.do_update()

            logging.warning("Now in {} mode for the All Sky!".format(mode))
            self.print_status("Change of mode complete.")
            
    def set_cloud_analysis_mode(self):
        """
        Enables or disables the cloud analysis in the observation computation.
        """ 
        
        if self.configCloudsAnalysis.checkState() == 0:
            self.cloudscheck = False
            logging.info("Clouds will no longer be taken into account when computing the observability. Changes will be executed during the next update.")
        else:
            self.cloudscheck = True
            logging.info("Clouds will be taken into account when computing the observability. Changes will be executed during the next update.")
        
    def do_update(self):
        """
        Method to perform a complete update of the observability for the date/time set in the obs_time widget
        """

        self.print_status("Updating observability...", SETTINGS['color']['warn'])
        self.save_Time2obstime()
        self.site_display()
        self.visibilitytool_draw()
        self.update_obs()
        
        self.listObs_plot_targets()
        logging.info("General update performed")
        self.print_status("Update done")



    def get_standard_items(self, o, FLAG='---'):
        """
        Create the default QStandardItem objects for an observable o

        Assumes the time has been refreshed

        :param o: :class:`~obs.Observable`
        :param FLAG: A string representing how non-defined variables, such as wind for non-visible observables, are represented.
        :return:
        """


        # Initial params
        name = QtGui.QStandardItem(o.name)
        name.setCheckable(True)
        alpha = QtGui.QStandardItem(o.alpha.to_string(unit=u.hour, sep=':', pad=True))
        delta = QtGui.QStandardItem(o.delta.to_string(unit=u.degree, sep=':', pad=True))
        observability = QtGui.QStandardItem(str("{:1.1f}".format(o.observability)))
        obsprogram = QtGui.QStandardItem(o.obsprogram)


        # Angle to the moon
        moondist = QtGui.QStandardItem()
        moondist.setData(str("{:03.0f}".format(o.angletomoon.degree)), role=QtCore.Qt.DisplayRole)
        if o.obs_moondist:
            moondist.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['success'])), role=QtCore.Qt.BackgroundRole)
        else:
            moondist.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['limit'])), role=QtCore.Qt.BackgroundRole)
        
        # Angle to the Sun, TODO: What default requirements?   
        sundist = QtGui.QStandardItem()
        sundist.setData(str("{:03.0f}".format(o.angletosun.degree)), role=QtCore.Qt.DisplayRole)

        # Airmass
        airmass = QtGui.QStandardItem()
        airmass.setData(str("%.2f" % o.airmass), role=QtCore.Qt.DisplayRole)
        if o.obs_airmass:
            airmass.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['success'])), role=QtCore.Qt.BackgroundRole)
        else:
            if o.obs_highairmass:
                airmass.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['warn'])), role=QtCore.Qt.BackgroundRole)
            else:
                airmass.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['limit'])), role=QtCore.Qt.BackgroundRole)

        # Wind
        wind = QtGui.QStandardItem()
        if o.obs_wind_info:
            wind.setData(str("{:03.0f}".format(o.angletowind.degree)), role=QtCore.Qt.DisplayRole)
            if o.obs_wind:
                wind.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['success'])), role=QtCore.Qt.BackgroundRole)
            else:
                wind.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['limit'])), role=QtCore.Qt.BackgroundRole)
        else:
            wind.setData(str(FLAG), role=QtCore.Qt.DisplayRole)
            wind.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['nodata'])), role=QtCore.Qt.BackgroundRole)

        # Clouds
        clouds = QtGui.QStandardItem()
        if o.obs_clouds_info:
            clouds.setData(str("{:1.1f}".format(o.cloudcover)), role=QtCore.Qt.DisplayRole)
            if o.cloudcover <= 0.25:
                clouds.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['success'])), role=QtCore.Qt.BackgroundRole)
            elif o.cloudcover <= 0.75:
                clouds.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['warn'])), role=QtCore.Qt.BackgroundRole)
            elif o.cloudcover <= 1:
                clouds.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['limit'])), role=QtCore.Qt.BackgroundRole)
            else:
                clouds.setData(str(FLAG), role=QtCore.Qt.DisplayRole)
                clouds.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['nodata'])), role=QtCore.Qt.BackgroundRole)
        else:
            clouds.setData(str(FLAG), role=QtCore.Qt.DisplayRole)
            clouds.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['nodata'])), role=QtCore.Qt.BackgroundRole)



        return name, alpha, delta, observability, obsprogram, moondist, sundist, airmass, wind, clouds




    def load_obs(self, filepath=None):

        """
        Loads a catalogue given a filepath or a user-chosen file (this prompts a select file and a column definition pop-ups)
        
        :param filepath: optional argument to bypass the Select a file dialogue (but not the column definition pop-up)
        """

        logmsg = ''

        # initialize a new obs_model
        obs_model = QtGui.QStandardItemModel(self.listObs)
        obs_model.setHorizontalHeaderLabels(['Name', 'Alpha', 'Delta', 'Obs', 'Program', "S", "M", "A", "W", "C"])


        # we start from scratch
        # todo: add an update function to load many obs one after the other
        self.listObs.clearSpans()
        if not filepath:
            filepath = QtWidgets.QFileDialog.getOpenFileName(self, "Select a file")[0]

        logmsg += '%s ' % filepath

        ext = os.path.splitext(filepath)[1]

        try:
            if ext != '.pouet':  # then it's a first load:

                obsprogramlist = run.retrieve_obsprogramlist()
                obsprogramnames = (o["name"] for o in obsprogramlist)

                # header popup
                self.headerPopup = uic.loadUi("headerdialog.ui")

                # split by tabs/spaces
                #todo: if columns are empty, the reader misses that. Either correct or print a warning, e.g. assert len(headers) == len(lines[0]) ??
                headers_input = open(filepath, 'r').readlines()[0].split('\n')[0].split()

                for i, cb in enumerate([self.headerPopup.headerNameValue, self.headerPopup.headerRAValue, self.headerPopup.headerDecValue, self.headerPopup.headerObsprogramValue]):
                    for h in headers_input:
                        cb.addItem(h)
                    cb.setCurrentIndex(i)

                self.headerPopup.headerObsprogramValue.addItem("None")
                self.headerPopup.headerObsprogramValue.setCurrentIndex(self.headerPopup.headerObsprogramValue.findText("None"))

                # ok is 0 if rejected, 1 if accepted
                ok = self.headerPopup.exec()
                if ok:

                    namecol = int(self.headerPopup.headerNameValue.currentIndex())+1
                    alphacol = int(self.headerPopup.headerRAValue.currentIndex())+1
                    deltacol = int(self.headerPopup.headerDecValue.currentIndex())+1

                    if self.headerPopup.headerObsprogramValue.currentText() == "None":
                        obsprogramcol = None
                    else:
                        obsprogramcol = int(self.headerPopup.headerObsprogramValue.currentIndex())+1

                    # obsprogram popup
                    self.popup = QtWidgets.QInputDialog()
                    #todo rename Cancel button as default if possible
                    obsprogram, okop = self.popup.getItem(self, "Select an observing program", " - Existing programs -\nSelect Cancel to use the default configuration.\nThis setting applies only to the observables\nthat do not already have an obsprogram defined in the input file", obsprogramnames, 1, False)

                    if okop:
                        logmsg += 'as %s ' % obsprogram
                    else:
                        obsprogram = None
                        logmsg += 'as default '

                else:
                    # we exit the load function
                    logging.info("Load of % aborted by user" % filepath)
                    return

            else:  # then it's a pouet file. We assume it follows our own convention for the rdbimport
                # col#1 = name, col#2 = alpha, col#3 = dec, col#4 = obsprogram
                pass


            try:
                if ext != '.pouet':
                    self.print_status("Loading catalogue...", color=SETTINGS["color"]["warn"])
                    self.observables = obs.rdbimport(filepath, obsprogram=obsprogram, namecol=namecol, alphacol=alphacol, deltacol=deltacol, obsprogramcol=obsprogramcol)

                    # check that names are unique
                    try:
                        names = [o.name for o in self.observables]
                        assert(len(names) == len(set(names)))
                    except:
                        logging.error("Names in your catalog are not unique!")
                        return

                else:

                    self.observables = obs.rdbimport(filepath, obsprogram=None)

                run.refresh_status(self.currentmeteo, self.observables)


                for o in self.observables:
                    logging.debug("entering compute observability")
                    o.compute_observability(self.currentmeteo, cloudscheck=self.cloudscheck, verbose=False, cwvalidity=float(SETTINGS['validity']['cloudwindanalysis']))

                    # create the QStandardItem objects
                    name, alpha, delta, observability, obsprogram, moondist, sundist, airmass, wind, clouds = self.get_standard_items(o)

                    # feed the model
                    obs_model.appendRow([name, alpha, delta, observability, obsprogram, sundist, moondist, airmass, wind, clouds])


                logging.debug('exiting model update')

                self.listObs.setModel(obs_model)
                self.listObs.resizeColumnsToContents()

                logmsg += 'successfully loaded'
                logging.info(logmsg)
                namecat = filepath.split("/")[-1]
                self.print_status("%s \nSucessfully loaded" % namecat, SETTINGS['color']['success'])

            except:
                logmsg += ' not loaded - wrong formatting'
                logging.error(logmsg)

                namecat = filepath.split("/")[-1]
                self.print_status("%s \nWrong formatting: headers and columns match?" % namecat, SETTINGS['color']['warn'])
        except:
            logmsg += ' not loaded - format unknown'
            logging.error(logmsg)

            self.print_status("%s \nFormat unknown: not a catalog file..." % filepath, SETTINGS['color']['warn'])



    def update_obs(self):
        """
        Update the observability of the observables, and update the display model

        .. note:: Works only on the non hidden observables

        .. note:: Assumes all the hidden=False observables are in the model - no more, no less - but this should ALWAYS be the case

        """

        # refresh the observables observability flags that have hidden == False
        run.refresh_status(self.currentmeteo, self.observables)
        for o in self.observables:
            if o.hidden is False:
                o.compute_observability(self.currentmeteo, cloudscheck=self.cloudscheck, verbose=False)


        # load the display model and the current header
        obs_model = self.listObs.model()
        headers, i, go_on = [], 0, True
        while go_on:
            h = obs_model.horizontalHeaderItem(i)  # will return None if there's no header...
            if not h:
                go_on = False
            else:
                headers.append(h.data(0))
                i += 1

        observability_index = headers.index("Obs")
        moondist_index = headers.index("M")
        sundist_index = headers.index("S")
        airmass_index = headers.index("A")
        wind_index = headers.index("W")
        clouds_index = headers.index("C")


        # we use the obs name as a reference to update the model
        model_names = [obs_model.item(i).data(0) for i in range(obs_model.rowCount())]


        # compute observability and refresh the model
        for o in self.observables:
            if o.hidden is False:

                name, alpha, delta, observability, obsprogram, moondist, sundist, airmass, wind, clouds = self.get_standard_items(o)

                # make sur we update the correct observable in the model...
                obs_index = model_names.index(o.name)
                obs_model.setItem(obs_index, observability_index, QtGui.QStandardItem(str(o.observability)))
                obs_model.setItem(obs_index, moondist_index, moondist)
                obs_model.setItem(obs_index, sundist_index, sundist)
                obs_model.setItem(obs_index, airmass_index, airmass)
                obs_model.setItem(obs_index, wind_index, wind)
                obs_model.setItem(obs_index, clouds_index, clouds)
                logging.debug("observable %s updated" % o.name)
            else:
                logging.debug("observable %s hidden, status not updated" % o.name)


        # refresh the display
        self.listObs.setModel(obs_model)

        msg = "Observability refreshed"
        logging.info(msg)
        self.print_status(msg, color=SETTINGS['color']['success'])


    def update_and_display_model(self):
        """
        Update the current model according to observables status and display it.

        .. note::This function DOES NOT update the observability. To do this, use :meth:`~main.update_obs()`

        :param obs_model: QStandardItemModel
        :return:
        """

        # load the current display model
        obs_model = self.listObs.model()

        model_names = [obs_model.item(i).data(0) for i in range(obs_model.rowCount())]

        # these are the obs we want to display
        obs_names = [o.name for o in self.observables if o.hidden == False]


        """
        3 cases:
        
        1) name is in obs_names and model_names --> we keep
        2) name is in obs_names only --> we add to model using get_standard_items
        3) name is in model_names only --> we remove from model
        
        """

        toadd = [n for n in obs_names if not n in model_names]
        toremove = [n for n in model_names if not n in obs_names]


        # Adding missing obs:
        for o in [o for o in self.observables if o.name in toadd]:
            assert o.hidden is False

            # create the QStandardItem objects
            name, alpha, delta, observability, obsprogram, moondist, sundist, airmass, wind, clouds = self.get_standard_items(o)

            obs_model.appendRow([name, alpha, delta, observability, obsprogram, sundist, moondist, airmass, wind, clouds])

            logging.info("Added %s to the model" % o.name)

        # Removing superfluous obs:
        for o in [o for o in self.observables if o.name in toremove]:
            assert o.hidden is True

            # todo: stupid loop, optimize that
            currentnames = [obs_model.item(i).data(0) for i in range(obs_model.rowCount())]
            toremoveindex = currentnames.index(o.name)
            obs_model.removeRow(toremoveindex)


        # refresh the display
        self.listObs.setModel(obs_model)

        msg = "Observability refreshed"
        logging.info(msg)
        self.print_status(msg, color=SETTINGS['color']['success'])


    def check_obs_status(self, obs_model):
        """
        Reads the observables model and return the check states and corresponding names

        :param obs_model: observables model

        :return: states of model observables
        """

        #0 is not checked, 1 is partially checked, 2 is checked --> 0 or 2 for us
        #obs_model = self.listObs.model()

        states = [obs_model.item(i, 0).checkState() for i in range(obs_model.rowCount())]
        names = [obs_model.item(i, 0).data(0) for i in range(obs_model.rowCount())]

        states = [0 if s == 0 else 1 for s in states]

        return states, names


    def hide_observables(self):
        """
        Hide observables according to the criteria selected by the user in the gui.

        """

        checked = self.toggleCheckedObs.isChecked()
        unchecked = self.toggleUncheckedObs.isChecked()
        airmass = self.toggleAirmassObs.isChecked()
        moondist = self.toggleMoondistObs.isChecked()
        sundist = self.toggleSundistObs.isChecked()
        observability = self.toggleObservabilityObs.isChecked()
        clouds = self.toggleCloudsObs.isChecked()
        alphamin = self.toggleAlphaMinObs.isChecked()
        alphamax = self.toggleAlphaMaxObs.isChecked()
        deltamin = self.toggleDeltaMinObs.isChecked()
        deltamax = self.toggleDeltaMaxObs.isChecked()


        obs_model = self.listObs.model()


        # reset hidden to False for all observables
        for o in self.observables:
            o.hidden = False

        # checked/unchecked
        states, names = self.check_obs_status(obs_model)
        if checked:
            for i, s in enumerate(states):
                if not s:
                    # hide from self
                    self.observables[[o.name for o in self.observables].index(names[i])].hidden = True

        if unchecked:
            for i, s in enumerate(states):
                if s:
                    # hide from self
                    self.observables[[o.name for o in self.observables].index(names[i])].hidden = True

        # other criterias
        criteria = []

        if airmass:
            criteria.append({"id": "airmass", "max":  self.airmassMaxObs.value()})

        if moondist:
            criteria.append({"id": "moondist", "min": self.moondistMinObs.value()})

        if sundist:
            criteria.append({"id": "sundist", "min": self.sundistMinObs.value()})

        if observability:
            criteria.append({"id": "obs", "min": 0})

        if clouds:
            criteria.append({"id": "clouds", "min": 0})

        # alpha
        if alphamin and alphamax:
            if self.alphaMinObs.isValid and self.alphaMaxObs.isValid:
                criteria.append({"id": "alphaboth", "min": self.alphaMinObs.text(), "max": self.alphaMaxObs.text()})
            elif self.alphaMinObs.isValid and not self.alphaMaxObs.isValid:
                criteria.append({"id": "alphamin", "min": self.alphaMinObs.text()})
                self.toggleAlphaMaxObs.setChecked(False)
                logging.warning("Alpha max field not valid - I discard it...")
            elif not self.alphaMinObs.isValid and self.alphaMaxObs.isValid:
                criteria.append({"id": "alphamax", "max": self.alphaMaxObs.text()})
                self.toggleAlphaMinObs.setChecked(False)
                logging.warning("Alpha min field not valid - I discard it...")
            else:
                self.toggleAlphaMinObs.setChecked(False)
                self.toggleAlphaMaxObs.setChecked(False)
                logging.warning("Alpha min and max fields not valid - I discard them...")
        elif alphamin and not alphamax:
            if self.alphaMinObs.isValid:
               criteria.append({"id": "alphamin", "min": self.alphaMinObs.text()})
            else:
                self.toggleAlphaMinObs.setChecked(False)
                logging.warning("Alpha min field not valid - I discard it...")

        elif not alphamin and alphamax:
            if self.alphaMaxObs.isValid:
                criteria.append({"id": "alphamax", "max": self.alphaMaxObs.text()})
            else:
                self.toggleAlphaMaxObs.setChecked(False)
                logging.warning("Alpha max field not valid - I discard it...")

        if deltamin and deltamax:
            if self.deltaMinObs.isValid and self.deltaMaxObs.isValid:
                criteria.append({"id": "deltaboth", "min": self.deltaMinObs.text(), "max": self.deltaMaxObs.text()})
            elif self.deltaMinObs.isValid and not self.deltaMaxObs.isValid:
                criteria.append({"id": "deltamin", "min": self.deltaMinObs.text()})
                self.toggleDeltaMaxObs.setChecked(False)
                logging.warning("Delta max field not valid - I discard it...")
            elif not self.deltaMinObs.isValid and self.deltaMaxObs.isValid:
                criteria.append({"id": "deltamax", "max": self.deltaMaxObs.text()})
                self.toggleDeltaMinObs.setChecked(False)
                logging.warning("Delta min field not valid - I discard it...")
            else:
                self.toggleDeltaMinObs.setChecked(False)
                self.toggleDeltaMaxObs.setChecked(False)
                logging.warning("Delta min and max fields not valid - I discard them...")
        elif deltamin and not deltamax:
            if self.deltaMinObs.isValid:
               criteria.append({"id": "deltamin", "min": self.deltaMinObs.text()})
            else:
                self.toggleDeltaMinObs.setChecked(False)
                logging.warning("Delta min field not valid - I discard it...")

        elif not deltamin and deltamax:
            if self.deltaMaxObs.isValid:
                criteria.append({"id": "deltamax", "max": self.deltaMaxObs.text()})
            else:
                self.toggleDeltaMaxObs.setChecked(False)
                logging.warning("Delta max field not valid - I discard it...")


        run.hide_observables(self.observables, criteria)

        # ALWAYS update the display after changing the hidden flag
        self.update_and_display_model()


    def unhide_observables(self):
        """
        Set the hidden flag of all the observables to False
        """

        for o in self.observables:
            o.hidden = False

        # ALWAYS update the display after changing the hidden flag
        self.update_and_display_model()



    def listObs_selectall(self):
        """
        When prompted, this method either select all observable or deselect them
        """
        
        obs_model = self.listObs.model()
                
        if self.listObs_check_state == 0:
            out_state = 2
        else:
            out_state = 0
        
        for ii in range(obs_model.rowCount()):
            obs_model.item(ii, 0).setCheckState(out_state)
            
        self.listObs_check_state = out_state
    
    def listObs_plot_targets(self):
        """
        Plots the selected targets in the visbility and all sky.


        .. note:: The user can select in which plot they want to see the target (2 checkboxes in the config tab).
        
        .. note:: displayed in all sky only if delta time between obs_time and all sky last refresh is smaller than `showallskytargets` (in global settings) - OR if debug mode.
        """
        
        obs_model = self.listObs.model()
        
        if obs_model is None:
            logging.debug("Nothing to plot: no obs loaded")
            return 
            
        status, names = self.check_obs_status(self.listObs.model())
        d = [names[i] for i, s in enumerate(status) if s==1]
        
        alphas = []
        deltas = []
        are_obs = []
        as_xs = []
        as_ys = []
        ord_names = []
        
        for target in self.observables:
            
            if target.name not in d:
                continue
            
            ord_names.append(target.name)
            
            az, elev = self.currentmeteo.get_AzAlt(target.alpha, target.delta, self.currentmeteo.time)
            as_x, as_y = self.currentmeteo.allsky.station.get_image_coordinates(az.radian, elev.radian)
            
            alphas.append(target.alpha.value)
            deltas.append(target.delta.value)
            as_xs.append(as_x)
            as_ys.append(as_y)
            are_obs.append(target.observability)
            
        #-------- Plots on visibility layer
        
        self.visibilitytool_draw_exec() 
        if self.configShowTargetsVisibilityValue.checkState() == 2:
            # This is not the most perfect code ever, however if drawing on another layer, it's hard to read the coordinates of the mouse in the plot
            # for the show_coordinate in all_sky, so by passing.
            # (however visibilitytool_draw_exec is fast...)
        
            self.visibilitytool.show_targets(alphas, deltas, ord_names, meteo=self.currentmeteo)
        
            logging.debug("Plotted {} targets in visibility".format(len(d)))
        
        #-------- Plots on all sky layer
        
        self.allskylayerTargets.erase()
        if self.configShowTargetsAllSkyValue.checkState() == 2:
            
            if not self.allsky_debugmode and (self.currentmeteo.allsky.last_im_refresh is None or np.abs(self.currentmeteo.time - self.currentmeteo.allsky.last_im_refresh).to(u.s).value / 60. > float(SETTINGS['validity']['showallskytargets'])):
                logging.debug("Not showing targets on All Sky, delta time too large")
                return
            
            self.allskylayerTargets.show_targets(as_xs, as_ys, ord_names)
            
            logging.debug("Plotted {} targets in All Sky".format(len(d)))


    def weather_display(self):
        """
        Prompts a weather report update and displays the results in the `station` tab.
        """
        
        if not self.currentmeteo.lastest_weatherupdate_time is None and (Time.now() - self.currentmeteo.lastest_weatherupdate_time).to(u.s).value < float(SETTINGS['validity']['weatherreportfrequency']):
            logging.info("Last weather report was downloaded more recently than {} seconds ago, I don't download it again".format(SETTINGS['validity']['weatherreportfrequency']))
            draw_wind = False
        else:
            self.currentmeteo.updateweather()
            draw_wind = True
        
        self.weather_reached_limit = False
        self.weather_reached_warn = False
        
        self.weatherWindSpeedValue.setText(str('{:2.1f}'.format(self.currentmeteo.windspeed)))
        if float(self.currentmeteo.location.get("weather", "windLimitLevel")) <= self.currentmeteo.windspeed:
            self.weatherWindSpeedValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['limit']))
            self.weather_reached_limit = True
        elif float(self.currentmeteo.location.get("weather", "windWarnLevel")) <= self.currentmeteo.windspeed:
            self.weatherWindSpeedValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['warn']))
            self.weather_reached_warn = True
        else:
            self.weatherWindSpeedValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['nominal']))
        
        self.weatherWindDirectionValue.setText(str('{:3d}'.format(int(self.currentmeteo.winddirection))))
        
        self.weatherTemperatureValue.setText(str('{:2.1f}'.format(int(self.currentmeteo.temperature))))
        
        self.weatherHumidityValue.setText(str('{:3d}'.format(int(self.currentmeteo.humidity))))
        if float(self.currentmeteo.location.get("weather", "humidityLimitLevel")) <= self.currentmeteo.humidity:
            self.weatherHumidityValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['limit']))
            self.weather_reached_limit = True
        elif float(self.currentmeteo.location.get("weather", "humidityWarnLevel")) <= self.currentmeteo.humidity:
            self.weatherHumidityValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['warn']))
            self.weather_reached_warn = True
        else:
            self.weatherHumidityValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['nominal']))
        
        if draw_wind:
            self.allsky_redisplay()
        
        self.weatherLastUpdateValue.setText("Last update: {}".format(str(self.currentmeteo.lastest_weatherupdate_time).split('.')[0]))
        
        self.does_warn_station()

    def site_display(self):
        """
        Computes and displays information about the site and the position of the bright objects in the `station` tab.
        """
        
        self.siteLocationValue.setText(str('Lat={:s}\tLon={:s}\tElev={:s} m'.format(self.currentmeteo.location.get("location", "longitude"), self.currentmeteo.location.get("location", "latitude"), self.currentmeteo.location.get("location", "elevation"))))
        
        obs_time = self.currentmeteo.time
        
        #-------------------------------------------------------- Bright objects now
        
        sunAz, sunAlt = self.currentmeteo.get_sun(obs_time)
        sunAlt = sunAlt.to(u.degree).value
        sunAz = sunAz.to(u.degree).value
        
        _, sunAltp1 = self.currentmeteo.get_sun(obs_time + TimeDelta(10.0*60., format='sec'))
        sunAltp1 = sunAltp1.to(u.degree).value
        sundAlt = sunAltp1 - sunAlt
        
        if sundAlt > 0:
            sunState = "rising"
        else:
            sunState = "declining"
        
        self.sunCoordinatesValues.setText(str('RA={:s}  DEC={:s}'.format(self.currentmeteo.sun.ra.__str__(), self.currentmeteo.sun.dec.__str__())))
        self.sunAltazValue.setText(str('{:2.1f}° ({:s})\t{:2.1f}°'.format(sunAlt, sunState, sunAz)))
        
        self.station_reached_limit = False
        self.station_reached_warn = False
        
        if sunAlt > -6:
            self.sunAltazValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['limit']))
            self.station_reached_limit = True
        elif sunAlt > -12:
            self.sunAltazValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['warn']))
            self.station_reached_warn = True
        else:
            self.sunAltazValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['nominal']))
        
        moonAz, moonAlt = self.currentmeteo.get_moon(obs_time)
        moonAlt = moonAlt.to(u.degree).value
        moonAz = moonAz.to(u.degree).value
        
        _, moonAltp1 = self.currentmeteo.get_moon(obs_time + TimeDelta(10.0*60., format='sec'))
        moonAltp1 = moonAltp1.to(u.degree).value
        moondAlt = moonAltp1 - moonAlt
        
        if moondAlt > 0:
            moonState = "rising"
        else:
            moonState = "declining"
        
        self.moonCoordinatesValues.setText(str('RA={:s}  DEC={:s}'.format(self.currentmeteo.moon.ra.__str__(), self.currentmeteo.moon.dec.__str__())))
        self.moonAltazValue.setText(str('{:2.1f}° ({:s})\t{:2.1f}°'.format(moonAlt, moonState, moonAz)))
        
        self.brightLastUpdateValue.setText("computed for {}".format(str(obs_time).split('.')[0]))
        
        self.does_warn_station()

        
        #-------------------------------------------------------- Night here only (we change the obs_time so this must the last things to run!)
        
        cobs_time = copy.copy(obs_time)
        #cobs_time = Time('2018-02-08 01:00:00', format='iso', scale='utc')
        cobs_time.format = 'iso'
        cobs_time.out_subfmt = 'date'
        
        ref_time = Time('%s 12:00:00' % cobs_time, format='iso', scale='utc') #5h UT is approx. the middle of the night
        
        is_after_midday = (cobs_time-ref_time).value > 0
        
        if is_after_midday:
            day_before = copy.copy(cobs_time)
            night_date = cobs_time
            day_after = night_date + TimeDelta(1, format="jd")
        else:
            day_after = cobs_time
            night_date = cobs_time - TimeDelta(1, format="jd")
            day_before = cobs_time - TimeDelta(1, format="jd")
            
        sunrise, sunset = self.currentmeteo.get_twilights(night_date, twilight='civil')
        self.nightStartCivilValue.setText(str('{:s}'.format(str(sunset))))
        self.nightEndCivilValue.setText(str('{:s}'.format(str(sunrise))))
        
        sunrise, sunset = self.currentmeteo.get_twilights(night_date, twilight='nautical')
        self.nightStartNauticalValue.setText(str('{:s}'.format(str(sunset))))
        self.nightEndNauticalValue.setText(str('{:s}'.format(str(sunrise))))
        
        sunrise, sunset = self.currentmeteo.get_twilights(night_date, twilight='astronomical')
        self.nightStartAstroValue.setText(str('{:s}'.format(str(sunset))))
        self.nightEndAstroValue.setText(str('{:s}'.format(str(sunrise))))
        
        self.nightLastUpdateValue.setText("for night {} to {}".format(str(day_before).split('.')[0], str(day_after).split('.')[0]))

    def allsky_refresh(self):
        """
        Starts a refresh of the all sky by erasing the image and starting a new thread to get the new image and analyse it.
        """
        
        self.print_status("Refreshing All Sky...", SETTINGS['color']['warn'])
        
        self.allskylayer.erase()
        
        self.threadAllskyUpdate.start()
        
    def allsky_redisplay(self):
        """
        Calls the drawing of the all sky in the widget. (including the wind)
        """
        
        if self.configCloudsShowLayersValue.checkState() == 0:
            plot_analysis = False
        else:
            plot_analysis = True
        
        self.allsky.display(self.currentmeteo, plot_analysis=plot_analysis)
        self.allSkyUpdateValue.setText("Image update: {}".format(str(self.currentmeteo.allsky.last_im_refresh).split('.')[0]))
        
        self.allsky.display_wind_limits(self.currentmeteo)
        self.allSkyUpdateWindValue.setText("Wind update: {}".format(str(self.currentmeteo.lastest_weatherupdate_time).split('.')[0]))
        
        msg = "Drawn All Sky."
        logging.debug(msg)
        
    def visibilitytool_draw_exec(self):
        """
        Actually calls to draw the visibility. (and does not handle the target plot) 
        
        .. note:: if there is a too large delta time between weather report and obs_time, does not display weather info (threshold defined in global settings, `validity`/`weatherreport`)
        """
        
        airmass = self.visibilityAirmassValue.value()
        anglemoon = self.visibilityMoonAngleValue.value()
        
        if self.currentmeteo.lastest_weatherupdate_time is None or np.abs((self.currentmeteo.time - self.currentmeteo.lastest_weatherupdate_time).to(u.s).value / 60.) > float(SETTINGS['validity']['weatherreport']):
            check_wind = False
            logging.info("Visibility is not considering the wind, too much difference between date weather report and obs time")
        else:
            check_wind = True
        
        self.visibilitytool.visbility_draw(meteo=self.currentmeteo, airmass=airmass, anglemoon=float(anglemoon), check_wind=check_wind)
        
        logging.debug("Drawn visibility with airmass={:1.1f}, anglemoon={:d}d".format(airmass, anglemoon))
        
    def visibilitytool_draw(self):
        """
        Method to prompt the drawing of the visibility and plots the selected targets in the visibility tool.
        """
    
        self.visibilitytool_draw_exec()
        self.listObs_plot_targets()
        
    def auto_refresh(self):
        """
        Auto-refresh of the weather report and the all sky.
        
        .. note:: the user can choose in the config tab the frequency of the update and if to update the all sky and the weather report 
        """
        
        logging.info("Auto-refresh")
        self.print_status("Auto-refresh started...", SETTINGS['color']['warn'])
        
        if self.configCloudsAutoRefreshValue.checkState() == 2:
            self.allsky_refresh()
        if self.configWindAutoRefreshValue.checkState() == 2:
            self.weather_display()
        if self.configWindAutoRefreshValue.checkState() == 2 and self.configCloudsAutoRefreshValue.checkState() == 0:
            self.allsky_redisplay()
        
        if self.currentmeteo.lastest_weatherupdate_time is None or (Time.now() - self.currentmeteo.lastest_weatherupdate_time).to(u.s).value / 60. > float(SETTINGS['validity']['weatherreport']):
            self.allSkyUpdateWindValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['warn']))
            self.weatherLastUpdateValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['warn']))
        else:
            self.allSkyUpdateWindValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['nominal']))
            self.weatherLastUpdateValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['nominal']))
            
        
        if self.currentmeteo.allsky.last_im_refresh is None or (Time.now() - self.currentmeteo.allsky.last_im_refresh).to(u.s).value / 60. > float(SETTINGS['validity']['allsky']):
            self.allSkyUpdateValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['warn']))
        else:
            self.allSkyUpdateValue.setStyleSheet("QLabel { color : %s; }" % format(SETTINGS['color']['nominal']))

        self.print_status("Auto-refresh done.", SETTINGS['color']['nominal'])


class MyLogger(logging.Handler):
    """
    Class that inherits from `logging.Handler` to overload the `emit` method, just to handle better (i.e. not crash) when logging in a text box from multiple threads.
    """
    
    def __init__(self, logWriter):
        """
        Constructor.
        
        :param logWriter: an instance of the logWriter class
        """
        super().__init__()
        self.logWriter = logWriter

    def emit(self, record):
        #todo: Add what a record is in doc
        """
        This is called each time there is a new logging record. Basically reads the record, formats it and sends it to the logWritter for display.
        """
        msg = self.format(record)
        self.logWriter.set_msg(msg)

class LogWriter(QtCore.QThread):
    """
    A class in a different thread to handle the logging events correctly. Otherwise (and because we display the log in a textbox), pouet crashes.
    """
    
    dataSent = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(LogWriter, self).__init__(parent)
        
    def set_msg(self, msg):
        """
        records a message and sends it to the GUI for display.

        :param msg: Text to be displayed
        """
        self.dataSent.emit(msg)


class AllSkyView(FigureCanvas):
    """
    Class to draw data in the AllSkyView widget, including the analysed image, the selected targets and the mouse-over-visibility position.
    """

    def __init__(self, meteo, parent=None, width=4.66, height=3.5):
        """
        Constructor.
        
        :param meteo: a meteo instance, needed to get the default size of the all sky image
        :param parent: the parent widget
        :param width: width of the figure
        :param height: height of the figure
        """

        self.figure = Figure(figsize=(width, height))
        self.figure.patch.set_facecolor("None")
        
        self.figure.subplots_adjust(wspace=0.)
        self.figure.subplots_adjust(bottom=0.)
        self.figure.subplots_adjust(top=1.)
        self.figure.subplots_adjust(right=1.)
        self.figure.subplots_adjust(left=0.0)

        self.axis = self.figure.add_subplot(111)
        
        FigureCanvas.__init__(self, self.figure)
        self.setParent(parent)

        self.axis.axis('off')
        
        self.axis.patch.set_facecolor("None")
        
        FigureCanvas.setStyleSheet(self, "background-color:transparent;")

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        self.imx = meteo.allsky.station.params['image_x_size']
        self.imy = meteo.allsky.station.params['image_y_size']
        
    def erase(self):
        """
        Erases everything in the axis. To be called often, before every redraw or if a failure is detected, before showing error message
        """
        
        self.axis.clear()
        
        self.axis.scatter([0,self.imy],[0,self.imx], c='None', s=1)
        
        self.axis.set_ylim([self.imy, 0])
        self.axis.set_xlim([0, self.imx])

        self.axis.patch.set_facecolor("None")
        self.axis.axis('off')
        
        self.draw()
        
    def show_coordinates(self, x, y, color='k'):
        """
        When called, this highlights the a position in the all sky by displaying a reticule.
        
        :param x: allsky image x coordinate
        :param y: allsky image y coordinate
        :param color: color of the reticule
        """
        
        self.erase()
        
        self.axis.axhline(y, color='k', c=color)
        self.axis.axvline(x, color='k', c=color)

        self.draw()
        
    def show_targets(self, xs, ys, names):
        """
        Displays targets in the all sky
        
        :param xs: list of allsky x image coordinate
        :param ys: list of allsky y image coordinate
        :param names: list of the names
        """
        
        self.erase()
        
        self.axis.scatter(xs, ys, c='k', s=4)
        
        for x, y, name in zip(xs, ys, names):
            self.axis.annotate('{}'.format(name), xy=(x+6, y+1),
                               horizontalalignment='left', verticalalignment='center', size=8)
        
        self.draw()
            
    def error_image(self, startup=False):
        """
        Error image to display if there's an error while loading or processing the image
        
        :param startup: if `True` shows a message saying that the user should try to reload manually
        """
        
        self.axis.clear()
        self.axis.plot([-1,1],[-1,1], lw=4, c=SETTINGS['color']['nominal'])
        self.axis.plot([-1,1],[1,-1], lw=4, c=SETTINGS['color']['nominal'])
        
        self.axis.annotate('No connection to All Sky Server', xy=(0, -0.8), rotation=0,
                               horizontalalignment='center', verticalalignment='center', color=SETTINGS['color']['nominal'], fontsize=10)
        
        if startup:
            self.axis.annotate('Looks like you should refresh manually.', xy=(0, -0.9), rotation=0,
                               horizontalalignment='center', verticalalignment='center', color=SETTINGS['color']['nominal'], fontsize=8)
        
        self.axis.set_axis_off()
        self.draw()

    def display(self, meteo, plot_analysis=True):
        """
        Big method to draw the all sky and its analysis.
        
        :param meteo: the meteo instance to get the last refresh of the image (and if couldn't download for a while [in global settings/`validity`/`allsky`] displays an error message)
        :param plot_analysis: if `True` shows the analysis layer, if `False` only the orginal all sky image
        
        .. note:: if there is a processing error of the image and the method cannot plot it, it will call `AllSkyView.error_image()` with `startup=True`, i.e. for the user to manually refresh
        
        """

        self.axis.clear()

        allsky = meteo.allsky

        if meteo.allsky.last_im_refresh is None or (Time.now() - meteo.allsky.last_im_refresh).to(u.s).value / 60. > float(SETTINGS['validity']['allsky']):
            self.error_image()
            logging.warning("No All Sky image, by-passing")
            return

        rest = allsky.im_masked
        if not plot_analysis:
            self.axis.imshow(allsky.im_original, vmin=0, vmax=255, cmap=plt.get_cmap('Greys_r'))
            self.axis.set_ylim([np.shape(rest)[0], 0])
            self.axis.set_xlim([0, np.shape(rest)[1]])

            self.axis.set_axis_off()
            self.draw()
            return

        try:
            self.axis.imshow(rest, vmin=0, vmax=255, cmap=plt.get_cmap('Greys_r'))
            self.axis.imshow(allsky.observability_map.T, cmap=plt.get_cmap('RdYlGn'), alpha=0.2)
        except:
            meteo.allsky.last_im_refresh = None
            self.error_image(startup=True)
            logging.error("Something went wrong with the All Sky image, try again...")
            return
        # self.draw()

        theta_coordinates = np.deg2rad(np.arange(0, 360, 15))

        r0 = allsky.station.params['r0']
        cx = allsky.station.params['cx']
        cy = allsky.station.params['cy']
        north = allsky.station.params['north']
        deltatetha = allsky.station.params['deltatetha']

        coordinatesx = np.cos(north + theta_coordinates) * r0 + cx
        coordinatesy = np.sin(north + theta_coordinates) * r0 + cy

        northx, northy = allsky.station.get_image_coordinates(np.deg2rad(0), np.deg2rad(24))
        eastx, easty = allsky.station.get_image_coordinates(np.deg2rad(90), np.deg2rad(20))

        self.axis.annotate('N', xy=(northx, northy), rotation=deltatetha,
                           horizontalalignment='center', verticalalignment='center')

        self.axis.annotate('E', xy=(eastx, easty), rotation=deltatetha,
                           horizontalalignment='center', verticalalignment='center')

        altshow = [15, 30, 45, 60, 75, 90]
        for angle in np.deg2rad(altshow):
            rr = allsky.station.get_radius(angle)

            # if angle >= np.pi/2: print rr/330.
            self.figure.gca().add_artist(plt.Circle((cx, cy), rr, color='k', fill=False, alpha=0.3))

            textx = np.cos(north + np.deg2rad(180)) * (rr - 2) + cx
            texty = np.sin(north + np.deg2rad(180)) * (rr - 2) + cy
            self.axis.annotate('%d' % (90 - np.ceil(np.rad2deg(angle))), xy=(textx, texty), rotation=deltatetha,
                               # prefered_direction['dir'],
                               horizontalalignment='left', verticalalignment='center', size=10)

        # plt.plot([cx, northx], [cy, northy], lw=2, color='k')
        for ccx, ccy in zip(coordinatesx, coordinatesy):
            self.axis.plot([cx, ccx], [cy, ccy], lw=1, color='k', alpha=0.3)
        self.axis.set_ylim([np.shape(rest)[0], 0])
        self.axis.set_xlim([0, np.shape(rest)[1]])

        self.axis.set_axis_off()
        self.draw()

    def display_wind_limits(self, meteo):
        """
        Displays the wind limit if needed (according to the setting in config/{name}.cfg / weather / wind*Level)
        
        :param meteo: to get the weather and the parameters of the allsky
        
        .. note::If the wind is below the warn limit, does nothing, if above hatches in orange the region 90deg away from the wind and if above limit hatches all the image in red.
        """

        params = meteo.allsky.station.params

        r0 = params['r0']
        cx = params['cx']
        cy = params['cy']
        north = params['north']

        wpl = float(meteo.location.get("weather", "windWarnLevel"))
        wsl = float(meteo.location.get("weather", "windLimitLevel"))
        WD = meteo.winddirection
        WS = meteo.windspeed
        WDd = WD
        WD = np.deg2rad(WD)

        if WS is not None and WS > wpl:
            wdcoordinatesx = np.cos(north - WD) * r0 + cx
            wdcoordinatesy = np.sin(north - WD) * r0 + cy
            Nd = np.rad2deg(north)  # + 90.

            if WS > wsl:
                cw = SETTINGS['color']['limit']
                self.axis.add_patch(Wedge([cx, cy], r0, Nd - WDd, Nd - WDd + 360, fill=False, hatch='//', edgecolor=cw))
                self.axis.annotate('WIND LIMIT\nREACHED', xy=(cx, cy), rotation=0,
                                   horizontalalignment='center', verticalalignment='center', color=cw, fontsize=35)
            elif WS > wpl:
                cw = SETTINGS['color']['warn']
                wtcoordinatesx = np.cos(north - WD) * r0 / 2. + cx
                wtcoordinatesy = np.sin(north - WD) * r0 / 2. + cy

                self.axis.add_patch(
                    Wedge([cx, cy], r0, -90 + Nd - WDd, 90 + Nd - WDd, fill=False, hatch='//', edgecolor=cw))
                self.axis.annotate('Pointing limit!', xy=(wtcoordinatesx, wtcoordinatesy), rotation=0,
                                   horizontalalignment='center', verticalalignment='center', color=cw, fontsize=25)

            self.axis.plot([cx, wdcoordinatesx], [cy, wdcoordinatesy], lw=3, color=cw)

        self.draw()

class AirmassView(FigureCanvas):
    """
    Classes to handle the display of the airmass view
    """

    def __init__(self, parent=None, width=6, height=5):
        """
        Constructor
        
        :param parent: parent widget
        :param width: width of the matplotlib figure
        :param height: height of the matplotlib figure
        """

        self.figure = Figure(figsize=(width, height))
        self.figure.patch.set_facecolor("None")

        self.figure.subplots_adjust(wspace=0.)
        self.figure.subplots_adjust(bottom=0.02)
        self.figure.subplots_adjust(top=0.98)

        self.axis = self.figure.add_subplot(111, projection="polar")

        FigureCanvas.__init__(self, self.figure)
        self.parent = parent

        self.setParent(parent)
        
        self.axis.patch.set_facecolor("None")
        FigureCanvas.setStyleSheet(self, "background-color:transparent;")
        
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
    def show(self, target, meteo):
        """
        Draws the airmass by calling :meth:`~plots.plot_airmass_on_sky()`

        :param target: an observable instance
        :param meteo: the meteo instance (used for the obs_time)
        """
        
        self.axis.clear()
        plots.plot_airmass_on_sky(target, meteo, ax=self.axis)
        
        self.draw()
        
class SkychartView(FigureCanvas):
    """
    Handles the GUI of the Sky Chart (:meth:`~plots.plot_target_on_sky()`)
    """

    def __init__(self, target, parent=None, width=6, height=5):
        """
        Constructor
        
        :param parent: parent widget
        :param width: width of the matplotlib figure
        :param height: height of the matplotlib figure
        
        Note that we take by default the following values:
        - `northisup = True`
        - `eastisright = False`
        - `survey = 'DSS'`
        - `boxsize = 10` This is in arcmin, but give a float only, it is converted by `plots.plot_target_on_sky`
        - `cmap = 'Greys'`
        
        .. warning:: the default values are hard-coded this could prove to be wrong in certain cases -> monitor!
        """

        self.figure = Figure(figsize=(width, height))
        self.figure.patch.set_facecolor("None")

        self.figure.subplots_adjust(wspace=0.)
        self.figure.subplots_adjust(bottom=0.02)
        self.figure.subplots_adjust(top=0.98)

        FigureCanvas.__init__(self, self.figure)
        self.parent = parent

        self.setParent(parent)
        
        FigureCanvas.setStyleSheet(self, "background-color:transparent;")
        
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        self.northisup = True
        self.eastisright = False
        self.survey = 'DSS'
        self.boxsize = 10 # arcmin (defined in plots.plot_target_on_sky)
        self.cmap = "Greys"
        
        self.target = target
        
    def flipNorth(self):
        """
        Flips the image vertically
        """
        
        logging.debug("Sky Chart: flipping North")
        
        if self.northisup:
            self.northisup = False
        else:
            self.northisup = True
            
        self.show()
        
    def flipEast(self):
        """
        Flips the image horizontally
        """
        
        logging.debug("Sky Chart: flipping East")
                      
        if self.eastisright:
            self.eastisright = False
        else:
            self.eastisright = True
            
        self.show()
        
    def invertColors(self):
        """
        Inverts the colormap
        """
        
        logging.debug("Sky Chart: inverting cmap")
        
        if self.cmap == "Greys":
            self.cmap = "Greys_r"
        else:
            self.cmap = "Greys"
            
        self.show()
        
    def show_takeawhile(self):
        """
        Writes a text asking the user to be patient. Downloading can be slow, even with a fast connection
        """
        
        self.axis.clear()
        self.axis.annotate("This can take a while...", xy=(0.5, 0.5), xycoords="axes fraction", ha="center")
        self.axis.patch.set_facecolor("None")
        self.axis.axis('off')
        self.axis.figure.canvas.draw()
        QtWidgets.QApplication.processEvents()

    def changeSurvey(self, value):
        #todo: define what value is in the doc
        """
        Change the images from one survey to another
        """
        
        self.show_takeawhile()

        logging.debug("Sky Chart: changing image from {} to {}".format(self.survey, value))
        
        self.survey = value

        self.show()
        
        
    def changeBoxSize(self, value):
        # todo: define what value is in the doc
        """
        Change the size of the image
        
        .. todo:: This calls a new Skyview, maybe we can only change the size of the window and only download when necessary
        """
        #TODO: see todo in description. That is above. Learn to read. Damn!
        
        self.show_takeawhile()
        
        logging.debug("Sky Chart: changing size from {} to {}".format(self.boxsize, value))
        
        self.boxsize = value
        
        self.show()
        
    def show(self):
        """
        Draws the sky chart image
        """
        
        ax = plots.plot_target_on_sky(self.target, figure=self.figure, northisup=self.northisup, eastisright=self.eastisright, boxsize=self.boxsize, survey=self.survey, cmap=self.cmap)
        self.axis = ax
        self.axis.patch.set_facecolor("None")
        self.axis.figure.canvas.draw()



class VisibilityView(FigureCanvas):
    """
    Class to handle the visibility widget
    """


    def __init__(self, parent=None, width=4.5, height=visibility_height):
        """
        Constructor
        
        :param parent: parent widget
        :param width: width of the matplotlib figure
        :param height: height of the matplotlib figure
        """
        
        self.figure = Figure(figsize=(width, height))
        self.figure.patch.set_facecolor("None")

        self.figure.subplots_adjust(wspace=0.)
        self.figure.subplots_adjust(bottom=0.24)
        self.figure.subplots_adjust(top=0.93)
        self.figure.subplots_adjust(right=0.9)
        self.figure.subplots_adjust(left=0.13)

        gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1])
        self.axis = self.figure.add_subplot(gs[0])
        self.cax = self.figure.add_subplot(gs[1])

        FigureCanvas.__init__(self, self.figure)
        self.parent = parent

        self.setParent(parent)
        
        self.axis.patch.set_facecolor("None")
        
        FigureCanvas.setStyleSheet(self, "background-color:transparent;")

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        
    def show_targets(self, xs, ys, names, meteo):
        # todo: remove meteo from method param, as it seems to be useless (to be tested...that's why we need to push often and to have CI working !
        """
        Displays targets in the all sky
        
        :param xs: list of allsky x image coordinate
        :param ys: list of allsky y image coordinate
        :param names: list of the names
        
        .. warning:: this is done in the same frame as the visibility plot, so each time the user clics on targets to display, the visibility should be re-drawn.
        """
        
        self.axis.scatter(xs, ys, color='k', s=2)
        for x, y, name in zip(xs, ys, names):
            self.axis.annotate('{}'.format(name), xy=(x-0.2, y), color='k',
                               horizontalalignment='left', verticalalignment='center', size=7)
            
            
        self.draw()
        
    def visbility_draw(self, meteo, airmass, anglemoon, check_wind=True):
        """
        Draws the visibility plot
        
        :param meteo: to get the obs_time and the station params
        :param airmass: airmass max criterion
        :param anglemoon: min moon angle allowed
        :param check_wind: checks in meteo the current wind and compare this to the value in the station setting?
        
        .. note:: if above wind warning: displays the region 90deg away from the wind in orange. If above limit whole plot in red
        """

        self.axis.clear()
        self.cax.clear()

        ras, decs = util.grid_points()
        ra_g, dec_g = np.meshgrid(ras, decs)
        sep = np.zeros_like(ra_g)
        vis = np.zeros_like(ra_g)
        wind = np.zeros_like(ra_g) * np.nan

        tel_lat, tel_lon, tel_elev = meteo.get_telescope_params()

        observer = ephem.Observer()
        obs_time = meteo.time
        observer.date = obs_time.iso
        observer.lat = tel_lat.to_string(unit=u.degree, decimal=True)
        observer.lon = tel_lon.to_string(unit=u.degree, decimal=True)

        observer.elevation = tel_elev

        moon = ephem.Moon()
        moon.compute(observer)

        wpl = float(meteo.location.get("weather", "windWarnLevel"))
        wsl = float(meteo.location.get("weather", "windLimitLevel"))
        WD = meteo.winddirection
        WS = meteo.windspeed

        do_plot_contour = False
        for i, ra in enumerate(ras):
            for j, dec in enumerate(decs):
                star = ephem.FixedBody()
                star._ra = ra
                star._dec = dec
                star.compute(observer)

                if util.elev2airmass(el=star.alt + 0, alt=observer.elevation) < airmass:
                    vis[j, i] = 1
                    s = ephem.separation((moon.ra, moon.dec), (ra, dec)) + 0.

                    if np.rad2deg(s) - 0.5 > anglemoon:  # Don't forget that the angular diam of the Moon is ~0.5 deg
                        sep[j, i] = np.rad2deg(s)
                        do_plot_contour = True

                    else:
                        sep[j, i] = np.nan

                    if check_wind and WS >= wsl:
                        wind[j, i] = 1.
                        cw = SETTINGS['color']['limit']
                        #ct = 'WIND LIMIT REACHED'
                        #cts = 35
                    elif check_wind and WS >= wpl:
                        cw = SETTINGS['color']['warn']
                        #ct = 'Pointing limit!'
                        #cts = 20
                        ws = ephem.separation((star.alt, np.deg2rad(WD)), (star.alt, star.az))
                        if ws < np.pi / 2.:
                            wind[j, i] = 1.
                else:
                    sep[j, i] = np.nan
                    vis[j, i] = np.nan

            del star

        #########################################################

        ra_g = ra_g / 2 / np.pi * 24
        dec_g = dec_g / np.pi * 180
        v = np.linspace(anglemoon, 180, 100, endpoint=True)
        self.axis.contourf(ra_g, dec_g, vis, cmap=plt.get_cmap("Greys"))

        if do_plot_contour:
            CS = self.axis.contour(ra_g, dec_g, sep, levels=[50, 70, 90], colors=['yellow', 'red', 'k'], inline=1)
            self.axis.clabel(CS, fontsize=9, fmt='%d°')
            CS = self.axis.contourf(ra_g, dec_g, sep, v, )

            t = np.arange(anglemoon, 190, 10)
            tl = ["{:d}°".format(int(tt)) for tt in t]
            cbar = self.figure.colorbar(CS, ax=self.axis, cax=self.cax, ticks=t)
            cbar.ax.set_yticklabels(tl, fontsize=9)

        if check_wind and WS > wpl:
            cmap = LinearSegmentedColormap.from_list('mycmap', [(0., 'red'),
                                                                (1, cw)]
                                                     )

            cs = self.axis.contourf(ra_g, dec_g, wind, hatches=['//'],
                                    cmap=cmap, alpha=0.5)
            #self.axis.annotate(ct, xy=(12, 75), rotation=0,
            #                   horizontalalignment='center', verticalalignment='center', color=cw, fontsize=cts)

        for tick in self.axis.get_xticklabels():
            tick.set_rotation(70)
        self.axis.set_xlabel('Right ascension', fontsize=9, )
        self.axis.set_ylabel('Declination', fontsize=9, )
        
        
        self.axis.set_title("%s - Moon sep %d deg - max airmass %1.1f" % (str(obs_time).split('.')[0], \
                                                                          anglemoon, airmass), fontsize=9)
        
        self.axis.set_xticks(np.linspace(0, 24, 25))
        self.axis.set_yticks(np.linspace(-90, 90, 19))
        
        self.finish_plot(tel_lat)
        
    def finish_plot(self, tel_lat):
        # todo: define what tel_lat is in doc
        """
        helper to finish the plot correctly. 
        """

        self.axis.set_xlim([0, 24])
        lat = float(tel_lat.to_string(unit=u.degree, decimal=True))
        self.axis.set_ylim([np.max([lat - 90, -90]), np.min([lat + 90, 90])])

        self.axis.grid()
        self.axis.invert_xaxis()

        self.draw()
        
class ObsModel(QtCore.QAbstractTableModel):
    #todo: Is that used somewhere? looks like not...test what happens when removing it.
    def __init__(self, parent, *args):
        
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        
    def rowCount(self, parent):
        return len(self.mylist)
    
class ThreadAllskyUpdate(QtCore.QThread):
    """
    Class to handle the all sky update in a new thread
    """
    allskyUpdate = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super(ThreadAllskyUpdate, self).__init__(parent)
        self.parent = parent

    def run(self):
        """
        We should not directly update the GUI allsky, so we get it from the parent (at its current state) and returns it by emitting a signal
        """
        
        logging.debug("threadAllsky firing up.")
        
        allskycopy = copy.copy(self.parent.currentmeteo.allsky)
        
        allskycopy.update(float(SETTINGS['validity']['allskyfrequency']))

        logging.info("Updated All Sky")
        
        logging.debug("threadAllsky done.")
        
        self.allskyUpdate.emit([allskycopy])
    

def main():
    app = QtWidgets.QApplication(sys.argv)  # A new instance of QApplication
    app.setStyle(QtWidgets.QStyleFactory.create('WindowsXP'))
    form = POUET()                 # We set the form to be our ExampleApp (design)
    form.show()                         # Show the form
    app.exec_()

if __name__ == '__main__':
    main()
