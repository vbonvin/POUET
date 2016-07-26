#!/usr/bin/env python
#-*- coding:utf-8 -*-
import ephem
import numpy as np
import pylab as plt
import meteo

<<<<<<< HEAD
from datetime import datetime

from matplotlib import gridspec
=======
import time
from datetime import datetime

>>>>>>> 615eba1cb5c5e7981da440389f7052361227d4fe
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt4 import QtGui, QtCore
import CoordinatesAwayFromMoon as vm

class MatplotlibWidget(QtGui.QWidget):
	def __init__(self, parent=None):
		super(MatplotlibWidget, self).__init__(parent)

		self.figure = Figure()
<<<<<<< HEAD
		self.figure.patch.set_facecolor((0.95,0.94,0.94,1.))
		gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1]) 
		self.axis = self.figure.add_subplot(gs[0])
		self.cax = self.figure.add_subplot(gs[1])
		self.canvas = FigureCanvasQTAgg(self.figure)

		self.axis.axis('off')
		self.cax.axis('off')
=======
		self.canvas = FigureCanvasQTAgg(self.figure)

		self.axis = self.figure.add_subplot(111)
>>>>>>> 615eba1cb5c5e7981da440389f7052361227d4fe

		self.layoutVertical = QtGui.QVBoxLayout(self)
		self.layoutVertical.addWidget(self.canvas)

class ThreadSample(QtCore.QThread):
	newSample = QtCore.pyqtSignal()

	def __init__(self, parent=None):
		super(ThreadSample, self).__init__(parent)

	def run(self):
<<<<<<< HEAD
=======
		print (time.strftime("%d/%m/%Y %H:%M:%S : refresh"))
		#urllib.urlretrieve("http://allsky-dk154.asu.cas.cz/raw/AllSkyCurrentImage.JPG", "current.JPG")
		#im, rest = util.loadallsky("current.JPG", return_complete=True)
		#x, y = self.allskyanalyse_allsky.detect_stars(im)
		#observability = self.allsky.update()#analyse_allsky.get_observability(im, x, y)

>>>>>>> 615eba1cb5c5e7981da440389f7052361227d4fe
		self.newSample.emit()

class MyWindow(QtGui.QWidget):
	def __init__(self, parent=None):
		super(MyWindow, self).__init__(parent)
<<<<<<< HEAD
		
		self.setWindowTitle('Visible coordinates (La Silla)')

		self.time = '%s' % datetime.utcnow()
		self.time = self.time[:-7]
		self.airmass = vm.airmass
		self.moon_cutoff = vm.min_moon_separation

		self.pushButtonPlot = QtGui.QPushButton(self)
		self.pushButtonPlot.setText("Plot")
		self.pushButtonPlot.resize(100,30)
		self.pushButtonPlot.move(680, 10)
		self.pushButtonPlot.clicked.connect(self.on_pushButtonPlot_clicked)

		
		self.label_time = QtGui.QLabel(self)
		self.qle_time = QtGui.QLineEdit(self)
		self.qle_time.move(125, 10)
		self.qle_time.resize(160,30)
		self.qle_time.setText(self.time)
		self.label_time.move(6, 10)
		self.label_time.resize(150,30)
		self.label_time.setText('Current UTC date')
=======

		self.time = '%s' % datetime.utcnow()
		self.time = self.time[:-7]
		self.airmass = 1.5
		self.moon_cutoff = 30

		self.pushButtonPlot = QtGui.QPushButton(self)
		self.pushButtonPlot.setText("Plot")
		self.pushButtonPlot.clicked.connect(self.on_pushButtonPlot_clicked)
		
		self.label_time = QtGui.QLabel(self)
		self.qle_time = QtGui.QLineEdit(self)
		self.qle_time.move(70, 10)
		self.qle_time.resize(160,30)
		self.qle_time.setText(self.time)
		self.label_time.move(6, 10)
		self.label_time.setText('UTC date')
>>>>>>> 615eba1cb5c5e7981da440389f7052361227d4fe
		self.qle_time.setAlignment(QtCore.Qt.AlignLeft)
		
		self.label_am = QtGui.QLabel(self)
		self.qle_am = QtGui.QLineEdit(self)
<<<<<<< HEAD
		self.qle_am.move(420, 10)
		self.qle_am.resize(30,30)
		self.qle_am.setText('%1.1f' % self.airmass)
		self.label_am.move(330, 10)
		self.label_am.setText('Max. airmass')
		self.qle_am.setAlignment(QtCore.Qt.AlignLeft)
		
		self.label_ac = QtGui.QLabel(self)
		self.qle_ac = QtGui.QLineEdit(self)
		self.qle_ac.move(590, 10)
		self.qle_ac.resize(30,30)
		self.qle_ac.setText('%2d' % self.moon_cutoff)
		self.label_ac.move(490, 10)
		self.label_ac.setText('Min separation')
		self.qle_ac.resize(30,30)
		self.qle_ac.setAlignment(QtCore.Qt.AlignLeft)

		self.hbox = QtGui.QHBoxLayout(self)
		hbox = QtGui.QHBoxLayout()
		hbox.addWidget(self.qle_am)
		self.setLayout(hbox)
		
		self.matplotlibWidget = MatplotlibWidget(self)
		self.matplotlibWidget.move(-9,40)
		self.matplotlibWidget.resize(800,600)
		hbox.addWidget(self.matplotlibWidget)

		self.threadSample = ThreadSample(self)
		self.threadSample.newSample.connect(self.on_threadSample_newSample)
=======
		self.qle_am.move(340, 10)
		self.qle_am.resize(30,30)
		self.qle_am.setText('%1.1f' % self.airmass)
		self.label_am.move(250, 10)
		self.label_am.setText('Max. airmass')
		self.qle_am.setAlignment(QtCore.Qt.AlignLeft)
		
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(120000) #trigger every 2 minutes.
		self.timer.timeout.connect(self.on_pushButtonPlot_clicked)

		self.matplotlibWidget = MatplotlibWidget(self)

		self.layoutVertical = QtGui.QVBoxLayout(self)
		self.layoutVertical.addWidget(self.pushButtonPlot)
		self.layoutVertical.addWidget(self.matplotlibWidget)

		self.threadSample = ThreadSample(self)
		self.threadSample.newSample.connect(self.on_threadSample_newSample)
		#self.threadSample.finished.connect(self.on_threadSample_finished)
>>>>>>> 615eba1cb5c5e7981da440389f7052361227d4fe

	@QtCore.pyqtSlot()
	def on_pushButtonPlot_clicked(self):
		self.time = '%s' % datetime.utcnow()
		self.matplotlibWidget.axis.clear()
		self.threadSample.start()

	@QtCore.pyqtSlot(list)
	def on_threadSample_newSample(self):
		
<<<<<<< HEAD
		self.time = str(self.qle_time.text())
		self.moon_cutoff = int(self.qle_ac.text())
		self.airmass = float(self.qle_am.text())

		self.matplotlibWidget.axis.clear()
		self.matplotlibWidget.cax.clear()
=======
		print self.qle_time.text()

		self.matplotlibWidget.axis.clear()
>>>>>>> 615eba1cb5c5e7981da440389f7052361227d4fe

		moon = ephem.Moon()
		vm.LaSilla.date=self.time
		moon.compute(vm.LaSilla)
		
		ras,decs=vm.grid_points()
		ra_g, dec_g = np.meshgrid(ras,decs)
		sep=np.zeros_like(ra_g)
		vis=np.zeros_like(ra_g)
		wind = np.zeros_like(ra_g) * np.nan
		
		check_wind = True
		try:
			WD, WS = meteo.get_wind()
		except :
			check_wind = False
			
		try:
			from analyse_AllSky.util import get_params
			wpl = get_params()['wind_pointing_limit']
			wsl = get_params()['wind_stopping_limit']
		except:
			wpl = 15.
			wsl = 20.
		
		for i,ra in enumerate(ras):
			for j,dec in enumerate(decs):
				star = ephem.FixedBody()
				star._ra = ra
				star._dec = dec
				star.compute(vm.LaSilla)
				if vm.Elev2Airmass(el=star.alt+0,lat=vm.LaSilla.lat,alt=vm.LaSilla.elevation)<self.airmass:
					vis[j,i]=1
					s = ephem.separation(vm.hpos(moon), (ra, dec))+0.
					if np.rad2deg(s)-0.5>self.moon_cutoff: # Don't forget that the angular diam of the Moon is ~0.5 deg
						sep[j,i]=np.rad2deg(s)
						
					else: sep[j,i]=np.nan
					
					if check_wind and WS >= wsl :
						wind[j,i]=1.
						cw = 'r'
						ct = 'WIND LIMIT REACHED'
						cts = 35
					elif check_wind and WS >= wpl :
						cw = 'darkorange'
						ct = 'Pointing limit!'
						cts = 20
						ws = ephem.separation((star.alt, np.deg2rad(WD)), (star.alt, star.az))
						if ws < np.pi/2.:
							wind[j,i]=1.
				else: 
					sep[j,i]=np.nan
					vis[j,i]=np.nan
		
			del star
			
		#########################################################
		
<<<<<<< HEAD
=======
		#self.matplotlibWidget.figure.tight_layout()
		
>>>>>>> 615eba1cb5c5e7981da440389f7052361227d4fe

		ra_g=ra_g/2/np.pi*24
		dec_g=dec_g/np.pi*180
		v = np.linspace(self.moon_cutoff, 180, 100, endpoint=True)
		self.matplotlibWidget.axis.contourf(ra_g,dec_g,vis,cmap=plt.cm.Greys)
		CS=self.matplotlibWidget.axis.contour(ra_g,dec_g, sep, levels=[50,70,90],colors=['yellow','red','k'],inline=1)
		self.matplotlibWidget.axis.clabel(CS,fontsize=10,fmt='%d')
		CS=self.matplotlibWidget.axis.contourf(ra_g,dec_g,sep,v,)
		t= np.arange(self.moon_cutoff, 190, 10)
<<<<<<< HEAD
		self.matplotlibWidget.figure.colorbar(CS,ax=self.matplotlibWidget.axis,cax=self.matplotlibWidget.cax, ticks=t)
=======
		self.matplotlibWidget.figure.colorbar(CS,ticks=t)
>>>>>>> 615eba1cb5c5e7981da440389f7052361227d4fe
		
		if check_wind and WS > wpl:
			cs = self.matplotlibWidget.axis.contourf(ra_g,dec_g, wind, hatches=['', '//'],
		                  cmap=plt.get_cmap('gray'), alpha=0.5#, n_levels=[0,0.5,1.]
		                  )
			self.matplotlibWidget.axis.annotate(ct, xy=(12, 75), rotation=0,
				  			horizontalalignment='center', verticalalignment='center', color=cw, fontsize=cts)
		self.matplotlibWidget.axis.set_xlim([0,24])
		self.matplotlibWidget.axis.set_ylim([-90,90])

		for tick in self.matplotlibWidget.axis.get_xticklabels():
			tick.set_rotation(70)
		self.matplotlibWidget.axis.set_xlabel('Right ascension')
		self.matplotlibWidget.axis.set_ylabel('Declination')
		
		
		
		self.matplotlibWidget.axis.set_xticks(np.linspace(0,24,25))
		self.matplotlibWidget.axis.set_yticks(np.linspace(-90,90,19))

		self.matplotlibWidget.axis.set_title("%s - Moon sep %d deg - max airmass %1.2f" % (vm.LaSilla.date,\
			 self.moon_cutoff, self.airmass))
		
		self.matplotlibWidget.axis.grid()

		#self.matplotlibWidget.axis.set_axis_off()
		self.matplotlibWidget.canvas.draw()


if __name__ == "__main__":
	import sys

	app = QtGui.QApplication(sys.argv)
	app.setApplicationName('Visible coordinates')

	main = MyWindow()
<<<<<<< HEAD
	main.resize(800, 650)
=======
	main.resize(666, 666)
>>>>>>> 615eba1cb5c5e7981da440389f7052361227d4fe
	main.show()

	sys.exit(app.exec_())