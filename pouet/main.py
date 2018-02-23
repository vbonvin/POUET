"""
Launch the application, link POUET functions to the design
"""


from PyQt5 import QtCore, QtGui, QtWidgets, uic
import os, sys
import obs, run, util, plots
import meteo as meteomodule
import design
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
#logging.basicConfig(format='%(asctime)s | %(name)s(%(funcName)s): %(message)s', level=logging.DEBUG)
#logger = logging.getLogger(__name__)


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
        #self.checkObsStatus.clicked.connect(self.check_obs_status)
        self.configAutoupdateFreqValue.valueChanged.connect(self.set_timer_interval)
        self.configTimenow.clicked.connect(self.set_configTimeNow)
        self.configUpdate.clicked.connect(self.do_update)
        self.visibilityDraw.clicked.connect(self.visibilitytool_draw)
        self.configDebugModeValue.clicked.connect(self.set_debug_mode)
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
        
        # testing stuff at startup...

        
        self.load_obs(filepath='../cats/2m2lenses_withobsprogram.pouet')

        obs_model = self.listObs.model()
        print(obs_model.rowCount())
        #sys.exit()

        
        
    @QtCore.pyqtSlot(str)
    def on_threadlog(self, msg):
        self.viewLogs.appendPlainText(msg)
        
    @QtCore.pyqtSlot(list)
    def on_threadAllskyUpdate(self, sample):
        
        self.currentmeteo.allsky = sample[0]
        
        self.allskylayer.erase()
        
        self.allsky_redisplay()
        
        self.print_status("All Sky refresh done.")
        
        
    def init_warn_station(self):
        
        self.station_reached_limit = False
        self.station_reached_warn = False
        self.weather_reached_limit = False
        self.weather_reached_warn = False
        
    def does_warn_station(self):
        
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
        
        if tab is None:
            tab = self.weather
            
        self.tabWidget.tabBar().setTabTextColor(self.tabWidget.indexOf(tab), QtGui.QColor(color))

    def on_visibilitytoolmotion(self, event):
        
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
            
            self.plot_show = uic.loadUi("dialogPlots.ui")
            
            
            self.plot_show.setWindowTitle("Airmass for {}".format(target.name))
            
            amv = AirmassView(parent=self.plot_show.widget)
            amv.show(target, self.currentmeteo)
            
            self.plot_show.open()
            
            #####################################################
            
            self.skychart_show = uic.loadUi("dialogSkyChart.ui")
            
            
            self.skychart_show.setWindowTitle("Sky chart for {}".format(target.name))
            
            skychart = SkychartView(parent=self.skychart_show.widget)
            skychart.show(target)
            
            self.skychart_show.open()

    def print_status(self, msg, color=None):
        
        if color is None:
            color = SETTINGS['color']['nominal']
            
        self.statusLabel.setText(msg)
        self.statusLabel.setStyleSheet('color: {}'.format(color))
        QtWidgets.QApplication.processEvents()
        
    def set_timer_interval(self):

        interval = self.configAutoupdateFreqValue.value() * 1000 * 60
        self.timer.setInterval(interval)
        logging.debug("Set auto-refresh to {} min".format(self.configAutoupdateFreqValue.value()))
        
    def set_configTimeNow(self):
        
        #get current date and time
        now = QtCore.QDateTime.currentDateTimeUtc()

        #set current date and time to the object
        self.configTime.setDateTime(now)
        
    def save_Time2obstime(self):
        
        self.currentmeteo.time = Time(self.configTime.dateTime().toPyDateTime(), scale="utc")
        logging.debug("obs_time is now set to {:s}".format(str(self.currentmeteo.time)))
        
    def set_debug_mode(self):
        
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

        
    def do_update(self):

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

        :param o:
        :return:
        """


        # Initial params
        name = QtGui.QStandardItem(o.name)
        name.setCheckable(True)
        alpha = QtGui.QStandardItem(o.alpha.to_string(unit=u.hour, sep=':'))
        delta = QtGui.QStandardItem(o.delta.to_string(unit=u.degree, sep=':'))
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
            wind.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['warn'])), role=QtCore.Qt.BackgroundRole)

        # Clouds
        clouds = QtGui.QStandardItem()
        if o.obs_clouds_info:
            clouds.setData(str("{:1.1f}".format(o.cloudfree)), role=QtCore.Qt.DisplayRole)
            if o.obs_clouds:
                clouds.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['success'])), role=QtCore.Qt.BackgroundRole)
            else:
                clouds.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['limit'])), role=QtCore.Qt.BackgroundRole)
        else:
            clouds.setData(str(FLAG), role=QtCore.Qt.DisplayRole)
            clouds.setData(QtGui.QBrush(QtGui.QColor(SETTINGS['color']['warn'])), role=QtCore.Qt.BackgroundRole)



        return name, alpha, delta, observability, obsprogram, moondist, sundist, airmass, wind, clouds




    def load_obs(self, filepath=None):

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

        Works only on the non hidden observables

        Assumes all the hidden=False observables are in the model - no more, no less - but this should ALWAYS be the case

        :return: None
        """

        # refresh the observables observability flags that have hidden == True
        run.refresh_status(self.currentmeteo, self.observables)
        for o in self.observables:
            if o.hidden == False:
                o.compute_observability(self.currentmeteo, cloudscheck=True, verbose=False)


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
        for  o in self.observables:
            if o.hidden == False:

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

        This function DOES NOT update the observability. To do this, use to update_obs()

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
        Hide observables according to a given criterion.

        :return: None
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
            airmassmin, airmassmax = self.airmassMinObs.value(), self.airmassMaxObs.value()
            criteria.append({"id": "airmass", "min": airmassmin, "max": airmassmax})

        if moondist:
            criteria.append({"id": "moondist", "min": self.moondistMinObs.value()})

        if sundist:
            criteria.append({"id": "sundist", "min": self.sundistMinObs.value()})

        if observability:
            criteria.append({"id": "obs", "min": 0})

        if clouds:
            criteria.append({"id": "clouds", "min": 0})

        if alphamin and alphamax:
            criteria.append({"id": "alphaboth", "min": self.alphaMinObs.value(), "max": self.alphaMaxObs.value()})

        """
        elif alphamin and not alphamax:
            criteria.append({"id": "alphamin", "min": self.alphaMinObs.value()})
        elif alphamax and not alphamin:
            criteria.append({"id": "alphamax", "max": self.alphaMaxObs.value()})
        """



        run.hide_observables(self.observables, criteria)

        # ALWAYS update the display after changing the hidden flag
        self.update_and_display_model()


    def unhide_observables(self):

        for o in self.observables:
            o.hidden = False

        # ALWAYS update the display after changing the hidden flag
        self.update_and_display_model()



    def listObs_selectall(self):
        
        obs_model = self.listObs.model()
                
        if self.listObs_check_state == 0:
            out_state = 2
        else:
            out_state = 0
        
        for ii in range(obs_model.rowCount()):
            obs_model.item(ii, 0).setCheckState(out_state)
            
        self.listObs_check_state = out_state
    
    def listObs_plot_targets(self):
        
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
        
        self.weatherLastUpdateValue.setText(str(self.currentmeteo.lastest_weatherupdate_time).split('.')[0])
        
        self.does_warn_station()

    def site_display(self):
        
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
        
        self.brightLastUpdateValue.setText(str(obs_time).split('.')[0])
        
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
        
        self.nightLastUpdateValueBefore.setText(str(day_before).split('.')[0])
        self.nightLastUpdateValueAfter.setText(str(day_after).split('.')[0])

    def allsky_refresh(self):
        
        self.print_status("Refreshing All Sky...", SETTINGS['color']['warn'])
        
        self.allskylayer.erase()
        
        self.threadAllskyUpdate.start()
        
    def allsky_redisplay(self):
        
        if self.configCloudsShowLayersValue.checkState() == 0:
            plot_analysis = False
        else:
            plot_analysis = True
        
        self.allsky.display(self.currentmeteo, plot_analysis=plot_analysis)
        self.allSkyUpdateValue.setText(str(self.currentmeteo.allsky.last_im_refresh).split('.')[0])
        
        self.allsky.display_wind_limits(self.currentmeteo)
        self.allSkyUpdateWindValue.setText("Wind update: {}".format(str(self.currentmeteo.lastest_weatherupdate_time).split('.')[0]))
        
        msg = "Drawn All Sky."
        logging.debug(msg)
        
    def visibilitytool_draw_exec(self):
        
        airmass = self.visibilityAirmassValue.value()
        anglemoon = self.visibilityMoonAngleValue.value()
        
        if self.currentmeteo.lastest_weatherupdate_time is None or np.abs((self.currentmeteo.time - self.currentmeteo.lastest_weatherupdate_time).to(u.s).value / 60.) > float(SETTINGS['validity']['weatherreport']):
            check_wind = False
            logging.info("Visibility is not considering the wind, too much difference between date weather report and obs time")
        else:
            check_wind = True
        
        self.visibilitytool.visbility_draw(obs_time=self.currentmeteo.time, meteo=self.currentmeteo, airmass=airmass, anglemoon=float(anglemoon), check_wind=check_wind)
        
        logging.debug("Drawn visibility with airmass={:1.1f}, anglemoon={:d}d".format(airmass, anglemoon))
        
    def visibilitytool_draw(self):
    
        self.visibilitytool_draw_exec()
        self.listObs_plot_targets()
        
    def auto_refresh(self):
        
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
    
    def __init__(self, logWriter):
        super().__init__()
        self.logWriter = logWriter

    def emit(self, record):
        msg = self.format(record)
        self.logWriter.set_msg(msg)

class LogWriter(QtCore.QThread):
    dataSent = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(LogWriter, self).__init__(parent)
        self.msg = None
        
    def set_msg(self, msg):
        self.msg = msg
        self.dataSent.emit(self.msg)


class AllSkyView(FigureCanvas):

    def __init__(self, meteo, parent=None, width=4.66, height=3.5):

        self.figure = Figure(figsize=(width, height))
        self.figure.patch.set_facecolor("None")
        #self.figure.patch.set_facecolor((0.95, 0.94, 0.94, 1.))
        
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
        self.axis.clear()
        
        self.axis.scatter([0,self.imy],[0,self.imx], c='None', s=1)
        
        self.axis.set_ylim([self.imy, 0])
        self.axis.set_xlim([0, self.imx])

        self.axis.patch.set_facecolor("None")
        self.axis.axis('off')
        
        self.draw()
        
    def show_coordinates(self, x, y, color='k'):
        
        self.erase()
        
        self.axis.axhline(y, color='k', c=color)
        self.axis.axvline(x, color='k', c=color)

        self.draw()
        
    def show_targets(self, xs, ys, names):
        
        self.erase()
        
        self.axis.scatter(xs, ys, c='k', s=4)
        
        for x, y, name in zip(xs, ys, names):
            self.axis.annotate('{}'.format(name), xy=(x+6, y+1),
                               horizontalalignment='left', verticalalignment='center', size=8)
        
        self.draw()
            
    def error_image(self, startup=False):
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
        Should this call some other function elsewhere? Maybe
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

    def __init__(self, parent=None, width=6, height=5):

        self.figure = Figure(figsize=(width, height))
        self.figure.patch.set_facecolor("None")

        self.figure.subplots_adjust(wspace=0.)
        self.figure.subplots_adjust(bottom=0.02)
        self.figure.subplots_adjust(top=0.98)
        #self.figure.subplots_adjust(right=0.9)
        #self.figure.subplots_adjust(left=0.13)

        #gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1])
        self.axis = self.figure.add_subplot(111, projection="polar")
        #self.cax = self.figure.add_subplot(gs[1])

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
        
        self.axis.clear()
        plots.plot_airmass_on_sky(target, meteo, ax=self.axis)
        
        self.draw()
        
class SkychartView(FigureCanvas):

    def __init__(self, parent=None, width=6, height=5):

        self.figure = Figure(figsize=(width, height))
        self.figure.patch.set_facecolor("None")

        self.figure.subplots_adjust(wspace=0.)
        self.figure.subplots_adjust(bottom=0.02)
        self.figure.subplots_adjust(top=0.98)

        #self.axis = plt.gca()#projection=wcs)
        #self.axis = self.figure.add_subplot(111)

        FigureCanvas.__init__(self, self.figure)
        self.parent = parent

        self.setParent(parent)
        
        
        FigureCanvas.setStyleSheet(self, "background-color:transparent;")
        
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
    def show(self, target):
        
        #self.axis = self.figure.add_subplot(111)
        #self.axis.clear()

        ax = plots.plot_target_on_sky(target, figure=self.figure, northisup=True, eastisright=False, boxsize=None, survey='DSS')
        #self.axis.plot([0,0],[1,1])
        self.axis = ax
        self.axis.patch.set_facecolor("None")
        self.axis.figure.canvas.draw()

class VisibilityView(FigureCanvas):

    def __init__(self, parent=None, width=4.5, height=4):

        self.figure = Figure(figsize=(width, height))
        self.figure.patch.set_facecolor("None")

        self.figure.subplots_adjust(wspace=0.)
        self.figure.subplots_adjust(bottom=0.23)
        self.figure.subplots_adjust(top=0.95)
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
        
        self.axis.scatter(xs, ys, color='k', s=2)
        for x, y, name in zip(xs, ys, names):
            self.axis.annotate('{}'.format(name), xy=(x-0.2, y), color='k',
                               horizontalalignment='left', verticalalignment='center', size=7)
            
            
        #tel_lat, _, _ = meteo.get_telescope_params()
        
        #self.finish_plot(tel_lat)
        self.draw()
        
    def visbility_draw(self, obs_time, meteo, airmass, anglemoon, check_wind=True):

        self.axis.clear()
        self.cax.clear()

        ras, decs = util.grid_points()
        ra_g, dec_g = np.meshgrid(ras, decs)
        sep = np.zeros_like(ra_g)
        vis = np.zeros_like(ra_g)
        wind = np.zeros_like(ra_g) * np.nan

        tel_lat, tel_lon, tel_elev = meteo.get_telescope_params()

        observer = ephem.Observer()
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

        self.axis.set_xlim([0, 24])
        lat = float(tel_lat.to_string(unit=u.degree, decimal=True))
        self.axis.set_ylim([np.max([lat - 90, -90]), np.min([lat + 90, 90])])

        self.axis.grid()
        self.axis.invert_xaxis()

        self.draw()
        
class ObsModel(QtCore.QAbstractTableModel):
    
    def __init__(self, parent, *args):
        
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        
    def rowCount(self, parent):
        return len(self.mylist)
    
class ThreadAllskyUpdate(QtCore.QThread):
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
    global SETTINGS
    SETTINGS = util.readconfig("config/settings.cfg")
    form = POUET()                 # We set the form to be our ExampleApp (design)
    form.show()                         # Show the form
    app.exec_()                         # and execute the app

if __name__ == '__main__':
    main()
