#!/usr/bin/env python
#-*- coding:utf-8 -*-

import analyse_allsky
import util
import pylab as plt
import time
import numpy as np

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt4 import QtGui, QtCore

class MatplotlibWidget(QtGui.QWidget):
	def __init__(self, parent=None):
		super(MatplotlibWidget, self).__init__(parent)

		self.figure = Figure()
		self.canvas = FigureCanvasQTAgg(self.figure)

		self.axis = self.figure.add_subplot(111)

		self.layoutVertical = QtGui.QVBoxLayout(self)
		self.layoutVertical.addWidget(self.canvas)

class ThreadSample(QtCore.QThread):
	newSample = QtCore.pyqtSignal(list)

	def __init__(self, parent=None):
		super(ThreadSample, self).__init__(parent)
		self.allsky = analyse_allsky.Analyse_AllSky()

	def run(self):
		print (time.strftime("%d/%m/%Y %H:%M:%S : refresh"))
		#urllib.urlretrieve("http://allsky-dk154.asu.cas.cz/raw/AllSkyCurrentImage.JPG", "current.JPG")
		#im, rest = util.loadallsky("current.JPG", return_complete=True)
		#x, y = self.allskyanalyse_allsky.detect_stars(im)
		observability = self.allsky.update()#analyse_allsky.get_observability(im, x, y)

		self.newSample.emit([self.allsky.im_original, observability])

class MyWindow(QtGui.QWidget):
	def __init__(self, parent=None):
		super(MyWindow, self).__init__(parent)

		self.pushButtonPlot = QtGui.QPushButton(self)
		self.pushButtonPlot.setText("Start / refresh (auto-refresh every 2 min)")
		self.pushButtonPlot.clicked.connect(self.on_pushButtonPlot_clicked)

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

	@QtCore.pyqtSlot()
	def on_pushButtonPlot_clicked(self):
		self.matplotlibWidget.axis.clear()
		self.threadSample.start()

	@QtCore.pyqtSlot(list)
	def on_threadSample_newSample(self, sample):
		observability = sample[1]
		rest = sample[0]
		
		self.matplotlibWidget.figure.tight_layout()

		self.matplotlibWidget.axis.imshow(rest, vmin=0, vmax=255, cmap=plt.get_cmap('Greys_r'))
		self.matplotlibWidget.axis.imshow(observability, cmap=plt.get_cmap('RdYlGn'), alpha=0.2)
		
		#theta_coordinates = np.deg2rad([-146,0,45,90,0,180,170,190,200,0, 270, 315])
		theta_coordinates = np.deg2rad(np.arange(0,360,15))
	
		params = util.get_params(location="LaSilla")

		ff = params['ff']
		k1 = params['k1']
		k2 = params['k2']
		r0 = params['r0']
		cx = params['cx']
		cy = params['cy']
		north = params['north']
		deltatetha = params['deltatetha']
		
		coordinatesx = np.cos(north + theta_coordinates) * r0 + cx
		coordinatesy = np.sin(north + theta_coordinates) * r0 + cy
		
		northx, northy = util.get_image_coordinates(np.deg2rad(0), np.deg2rad(24))
		eastx, easty = util.get_image_coordinates(np.deg2rad(90), np.deg2rad(20))

		self.matplotlibWidget.axis.annotate('N', xy=(northx, northy), rotation=deltatetha,
		  horizontalalignment='center', verticalalignment='center')
		
		self.matplotlibWidget.axis.annotate('E', xy=(eastx, easty), rotation=deltatetha,
		  horizontalalignment='center', verticalalignment='center')

		altshow = [15, 30, 45, 60, 75, 90]
		for angle in np.deg2rad(altshow):
			rr = util.get_radius(angle, ff, k1, k2, r0)
		
			#if angle >= np.pi/2: print rr/330.
			self.matplotlibWidget.figure.gca().add_artist(plt.Circle((cx,cy),rr,color='k', fill=False))
		
			textx = np.cos(north + np.deg2rad(180)) * (rr - 2) + cx
			texty = np.sin(north + np.deg2rad(180)) * (rr - 2) + cy
			self.matplotlibWidget.axis.annotate('%d' % (90-np.ceil(np.rad2deg(angle))), xy=(textx, texty), rotation=deltatetha,#prefered_direction['dir'],
			  horizontalalignment='left', verticalalignment='center', size=10)
		
		#plt.plot([cx, northx], [cy, northy], lw=2, color='k')
		for ccx, ccy in zip(coordinatesx, coordinatesy):
			self.matplotlibWidget.axis.plot([cx, ccx], [cy, ccy], lw=1, color='k')
		self.matplotlibWidget.axis.set_ylim([np.shape(rest)[0], 0])
		self.matplotlibWidget.axis.set_xlim([0, np.shape(rest)[1]])
		
		self.matplotlibWidget.axis.set_axis_off()
		self.matplotlibWidget.canvas.draw()

if __name__ == "__main__":
	import sys

	app = QtGui.QApplication(sys.argv)
	app.setApplicationName('Cloud Monitor')

	main = MyWindow()
	main.resize(666, 666)
	main.show()

	sys.exit(app.exec_())