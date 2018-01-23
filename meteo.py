"""
Define the Meteo class and related functions

Meteo is an object containing all the external weather condition (wind speed and direction, temperature, moon position, clouds pattern,...)
It is the only object that interact outside POUET, i.e. communicate with website to get the meteo,...

Observables interact only with Meteo to get their constaints (position to the moon, angle to wind, ...)
"""

import astropy.coordinates.angles as angles
from astropy.time import Time
import urllib2
import re
import ephem
import util
import analyse_AllSky.analyse_allsky as cam

class Meteo:
	"""
	Class to hold the meteorological conditions of the current night

	Typically, a Meteo object is created when POUET starts, and then update itself every XX minutes
	"""

	def __init__(self, name='emptymeteo', date=None, moonaltitude=None, moonazimuth=None, 
			winddirection=None, windspeed=None, check_clouds=True):

		self.name = name
		self.date = date
		self.moonalt = moonaltitude
		self.moonaz = moonazimuth
		self.winddirection = winddirection
		self.windspeed = windspeed		
		
		self.check_clouds = check_clouds
		if check_clouds:
			self.allsky = cam.Analyse_AllSky(location="LaSilla")

		self.update()


	def __str__(self):
		return "Define me, dumbass !!"

	def updatedate(self):
		pass

	def	updatemoonpos(self, obs_time=Time.now()):
		Az, Alt = get_moon(obs_time=obs_time)
		self.moonalt = Alt
		self.moonaz = Az


	def updatewind(self):
		WD, WS = get_wind()
		self.winddirection = WD
		self.windspeed = WS


	def update(self, obs_time=Time.now(), minimal=False):
		"""
		minimal=True update only the moon position. Useful for predictions (as you can't predict the clouds or winds, no need to refresh them)
		"""
		self.updatedate()
		self.updatemoonpos(obs_time=obs_time)
		if not minimal:
			self.updatewind()
			if self.check_clouds: self.allsky.update()

	def is_cloudy(self, az, elev):
		return self.allsky.is_observable(az, elev)

def get_wind(url_weather="http://www.ls.eso.org/lasilla/dimm/meteo.last"):

	#todo: add a "no connection" message if page is not reachable instead of an error
	WS=[]
	WD=[]
	data=urllib2.urlopen(url_weather).read()
	data=data.split("\n") # then split it into lines
	for line in data:
		if re.match( r'WD', line, re.M|re.I):
			WD.append(int(line[20:25])) # AVG
		if re.match( r'WS', line, re.M|re.I):
			WS.append(float(line[20:25])) # AVG


	WD = WD[0] # WD is chosen between station 1 or 2 in EDP pour la Silla.
	WS = WS[2] # next to 3.6m telescope --> conservative choice.

	return WD, WS


def get_moon(obs_time=Time.now()):

	lat, lon, elev = util.get_telescope_params()

	observer = ephem.Observer()
	observer.date = obs_time.iso
	observer.lat, observer.lon, observer.elevation = lat.degree, lon.degree, elev

	moon = ephem.Moon()
	moon.compute(observer)

	# Warning, ass-coding here: output of moon.ra is different from moon.ra.__str__()... clap clap clap
	alpha = angles.Angle(moon.ra.__str__(), unit="hour")
	delta = angles.Angle(moon.dec.__str__(), unit="degree")

	# return Az, Alt as Angle object
	return util.get_AzAlt(alpha, delta, obs_time)
