#!/usr/bin/env python
#-*- coding:utf-8 -*-

import detect_peaks
import util
import pylab as plt
#import time
import numpy as np

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import urllib
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

	def run(self):
		#print (time.strftime("%d/%m/%Y %H:%M:%S : refresh"))
		urllib.urlretrieve("http://allsky-dk154.asu.cas.cz/raw/AllSkyCurrentImage.JPG", "current.JPG")
		im, rest = util.loadallsky("current.JPG", return_complete=True)
		x, y = detect_peaks.detect_stars(im)
		observability = detect_peaks.get_observability(im, x, y)

		self.newSample.emit([rest, observability])

class MyWindow(QtGui.QWidget):
	def __init__(self, parent=None):
		super(MyWindow, self).__init__(parent)

		self.pushButtonPlot = QtGui.QPushButton(self)
		self.pushButtonPlot.setText("Start / refresh (automatic every 2 min)")
		self.pushButtonPlot.clicked.connect(self.on_pushButtonPlot_clicked)
		
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(120000) #trigger every minute.
		self.timer.timeout.connect(self.on_pushButtonPlot_clicked)

		self.matplotlibWidget = MatplotlibWidget(self)

		self.layoutVertical = QtGui.QVBoxLayout(self)
		self.layoutVertical.addWidget(self.pushButtonPlot)
		self.layoutVertical.addWidget(self.matplotlibWidget)

		self.threadSample = ThreadSample(self)
		self.threadSample.newSample.connect(self.on_threadSample_newSample)
		self.threadSample.finished.connect(self.on_threadSample_finished)

	@QtCore.pyqtSlot()
	def on_pushButtonPlot_clicked(self):
		self.samples = 0
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
		theta_coordinates = np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315])
	
		cx = 279.
		cy = 230.
		prefered_direction = {'dir':194.3, 'posx':297, 'posy':336}
		prefered_theta = np.arctan2(prefered_direction['posy']-cy, prefered_direction['posx']-cx)
		
		north = prefered_theta + np.deg2rad(prefered_direction['dir'])
		
		northx = np.cos(north) * 220 + cx
		northy = np.sin(north) * 220 + cy
		
		eastx = np.cos(north - np.pi/2.) * 220 + cx
		easty = np.sin(north - np.pi/2.) * 220 + cy
		
		coordinatesx = np.cos(north + theta_coordinates) * 330 + cx
		coordinatesy = np.sin(north + theta_coordinates) * 330 + cy
		
		deltatetha=180-prefered_direction['dir']+5
		self.matplotlibWidget.axis.annotate('N', xy=(northx, northy), rotation=deltatetha,
		  horizontalalignment='center', verticalalignment='center')
		
		self.matplotlibWidget.axis.annotate('E', xy=(eastx, easty), rotation=deltatetha,
		  horizontalalignment='center', verticalalignment='center')

		altshow = [15, 30, 45, 60, 75, 90]
		for angle in np.deg2rad(altshow):
			#r90 = 2.*0.71*np.sin(angle/2.) * 330
			k1 = 1.96263549291*0.945
			k2 = 0.6
			ff = 1
			rr = ff*k1*np.tan(k2 * angle / 2.) * 330
		
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

	@QtCore.pyqtSlot()
	def on_threadSample_finished(self):
		self.samples += 1
		if self.samples <= 2:
			self.threadSample.start()

if __name__ == "__main__":
	import sys

	app = QtGui.QApplication(sys.argv)
	app.setApplicationName('Cloud Monitor')

	main = MyWindow()
	main.resize(666, 666)
	main.show()

	sys.exit(app.exec_())