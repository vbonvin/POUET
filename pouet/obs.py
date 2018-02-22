"""
Define the Observable class, the standard object of pouet, and related functions
"""

from numpy import cos, rad2deg, isnan, arange
import numpy as np
import os, sys
import copy as pythoncopy
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import angles, angle_utilities
import matplotlib.pyplot as plt
import importlib

import util

import logging
logger = logging.getLogger(__name__)


class Observable:
	"""
	Class to hold a specific target from any observational progamm

	Unvariable parameters are defined at initialisation

	Variable parameters (distance to moon, azimuth, observability,...) are undefined until associated methods are called
	"""

	def __init__(self, name='emptyobservable', obsprogram=None, attributes=None, alpha=None, delta=None, 
				minangletomoon=None, maxairmass=None, exptime=None):


		self.name = name
		self.obsprogram = obsprogram

		if not self.obsprogram == None:
			try:
				module_name = "obsprogram.prog{}".format(self.obsprogram)
				print(self.obsprogram, module_name)
				program = importlib.import_module(module_name, package=None)
				self.minangletomoon = program.minangletomoon
				self.maxairmass = program.maxairmass
				self.exptime = program.exptime
				self.program = program
			except SyntaxError:
				self.program = None
				raise SyntaxError("I could not find the prog%s.py definition file in obsprogram/" % self.obsprogram)

		self.alpha = angles.Angle(alpha, unit="hour")
		self.delta = angles.Angle(delta, unit="degree")

		if not minangletomoon is None: self.minangletomoon = minangletomoon
		if not maxairmass is None: self.maxairmass = maxairmass
		if not exptime is None: self.exptime = exptime
		self.cloudfree = None
	
		self.attributes = attributes
		self.hidden = False  # a hidden observable should not be updated
		#self.observability = observability



	def __str__(self):

		# not very elegant

		msg = "="*30+"\nName:\t\t%s\nProgram:\t%s\nAlpha:\t\t%s\n" \
				  "Delta:\t\t%s\n" %(self.name, self.obsprogram, self.alpha.hour, self.delta.degree)

		try:
			msg+= "Altitude:\t%s\n"%self.altitude.degree
		except AttributeError:
			msg+= "Altitude:\tNone\n"

		try:	# let's behave like real people and use a correct iso system

			msg+= "Azimuth:\t%s\n"%self.azimuth.degree
		except AttributeError:
			msg+= "Azimuth:\tNone\n"

		try:
			msg+= "Airmass:\t%s\n"%self.airmass
		except AttributeError:
			msg+= "Airmass:\tNone\n"


		return msg


	def copy(self):
		"""
		:return: Observable: a python deep copy of the current observable
		"""

		return pythoncopy.deepcopy(self)


	def compute_angletomoon(self, meteo):
		"""
		Computes the distance to the moon

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand
		:return: None
		"""

		moonalt, moonaz = meteo.moonalt, meteo.moonaz
		alt, az = self.altitude, self.azimuth
		separation = angle_utilities.angular_separation(moonaz, moonalt, az, alt) # Warning, separation is in radian!!

		angletomoon = angles.Angle(separation.value, unit="radian")
		self.angletomoon = angletomoon


	def compute_angletosun(self, meteo):
		"""
		Computes distance to the Sun

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand
		:return: None
		"""

		sunalt, sunaz = meteo.sunalt, meteo.sunaz
		alt, az = self.altitude, self.azimuth
		separation = angle_utilities.angular_separation(sunaz, sunalt, az, alt) # Warning, separation is in radian!!

		angletosun = angles.Angle(separation.value, unit="radian")
		self.angletosun = angletosun


	def compute_angletowind(self, meteo):
		"""
		Computes the angle to wind

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand

		:return: None
		"""

		winddirection = meteo.winddirection
		if winddirection < 0 or winddirection > 360:
			self.angletowind = None
			return
			
		try:
			angletowind = abs(winddirection-self.azimuth.degree)
			self.angletowind = angles.Angle(angletowind, unit='degree')
		except AttributeError:
			raise AttributeError("%s has no azimuth! \n Compute its azimuth first !")
		
	def compute_altaz(self, meteo):
		"""
		Computes altitude and azimuth of the observable.

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand

		:return: None
		"""
		azimuth, altitude = meteo.get_AzAlt(self.alpha, self.delta, obs_time=meteo.time)
		self.altitude = altitude
		self.azimuth = azimuth


	def compute_airmass(self, meteo):
		"""
		Computes altitude and azimuth of the observable.

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand

		:return: None
		"""

		self.airmass = util.elev2airmass(self.altitude.radian, meteo.elev)



	def is_cloudfree(self, meteo):
		"""
		Computes whether the pointing direction is cloudy according to the altaz coordinates in memory

		:param meteo: a Meteo object, whose cloudmap attribute has been actualized beforehand

		todo: instead of taking altaz coordinates in memory, shouldn't we use meteo.time to recompute altaz on the fly?
		
		:return: None
		
		:note: is_cloudfree is actualized with 0: cloudy or 1: no clouds. If unavailable, returns 2: connection error, if error during computation of observability from map: 3
		"""

		ERROR_CONN = 2.
		ERROR_COMPUTE = 3.

		xpix, ypix = meteo.allsky.station.get_image_coordinates(self.azimuth.value, self.altitude.value)
		
		if meteo.cloudmap is None:
			self.cloudfree = ERROR_CONN
			logger.debug("No cloud map in meteo object")
			return
		
		try:
			xpix = int(np.round(xpix))
			ypix = int(np.round(ypix))
		except ValueError:
			self.cloudfree = ERROR_COMPUTE
		
		if self.cloudfree != ERROR_COMPUTE:
			try:
				self.cloudfree = np.round(meteo.cloudmap[xpix, ypix], 3) # Otherwise some 1.0000002 errors arise...
			except IndexError:
				self.cloudfree = ERROR_COMPUTE

		if self.cloudfree == ERROR_COMPUTE: 
			logger.warning("Computation error in clouds")
			
		self.cloudfree = float(self.cloudfree)


	def update(self, meteo):
		"""
		Update the observable parameters according to the meteo object passed: altitude, azimuth, angle to wind, airmass, angle to moon and angle to sun.

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand
		:return: None
		"""

		self.compute_altaz(meteo)
		self.compute_angletowind(meteo)
		self.compute_airmass(meteo)
		self.compute_angletomoon(meteo)
		self.compute_angletosun(meteo)


	def compute_observability(self, meteo, cwvalidity=30, displayall=True, cloudscheck=True, verbose=True, future=False):
		"""
		Update the status using :meth:`~obs.Observable.update`. Compute the observability, a value between 0 and 1 that tells if the target can be observed at a given time. Also define flags for each parameter (moon, wind, etc...)

		The closer to 1 the better
		0 is impossible to observe

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand

		:param displayall: boolean

		"""

		logger.info("current time is %s"  % meteo.time)
		self.update(meteo=meteo)
		observability = 1  # by default, we can observe

		if np.abs(meteo.time - Time.now()).to(u.s).value / 60. > cwvalidity: future=True


		# Let's start with a simple yes/no version
		# We add a small message to display if it's impossible to observe:
		msg = ''
		warnings = ''

		### General conditions:
		# Each condition has an associated bool flag to tell if it is respected or not
		# Not respected conditions decrease the overall observability by a given amount
		# todo: configure the observability amount decrease in the obsprogram files.

		# check the	moondistance:
		self.obs_moondist = True
		if self.angletomoon.degree < self.minangletomoon:
			observability -= 0.2
			self.obs_moondist = False
			msg += '\nMoonDist:%0.1f' % self.angletomoon.degree

		# high airmass
		self.obs_highairmass = True
		if self.airmass > 1.5:
			self.obs_highairmass = False
			observability -= 0.3
			msg += '\nAirmass:%0.2f' % self.airmass

		# check the airmass:
		self.obs_airmass = True
		if self.airmass > self.maxairmass:
			self.obs_airmass = False
			observability = 0
			msg += '\nAirmass:%0.2f' % self.airmass


		# check the wind:
		self.obs_wind, self.obs_wind_info = True, True
		if not future:
			if meteo.windspeed > 0. and meteo.windspeed < 100. and self.angletowind is not None:
				if self.angletowind.degree < 90 and meteo.windspeed >= float(meteo.location.get("weather", "windWarnLevel")):
					self.obs_wind = False
					observability = 0
					msg += '\nWA:%0.1f/WS:%0.1f' % (self.angletowind.degree, meteo.windspeed)

				if meteo.windspeed >= float(meteo.location.get("weather", "windLimitLevel")):
					self.obs_wind = False
					observability = 0
					msg += '\nWS:%s' % meteo.windspeed
			else:
				self.obs_wind_info = False
				warnings += '\nNo wind info'
		else:
			self.obs_wind_info = False


		# check the clouds
		self.obs_clouds, self.obs_clouds_info = True, True
		if not future:
			if cloudscheck and observability > 0:
				self.is_cloudfree(meteo)
				if self.cloudfree < 0.5 :
					self.obs_clouds = False
					warnings += '\nWarning ! It might be cloudy'
				elif self.cloudfree <= 1.:
					msg += '\nSeems to be cloud-free'
				else:
					self.obs_clouds_info = False
					warnings += '\nNo cloud info'
			else:
				self.obs_clouds_info = False
				warnings += '\nNo cloud info'
		else:
			self.obs_clouds_info = False
		

		# check the internal observability flag
		self.obs_internal = True
		if hasattr(self, 'internalobs'):
			if self.internalobs == 0:
				self.obs_internal = False
				observability = self.internalobs
				msg += '\nSpreadsheet NO'


		### Program specific conditions:
		pobs, pmsg, pwarn = self.program.observability(self.attributes, meteo.time)
		if pobs == 0: observability = 0
		msg += pmsg
		warnings += pwarn

		# Finally, add the eventuel comment:
		if hasattr(self, 'comment'):
			msg += '\n %s' % self.comment

		if verbose:
			to_print = "%s | %s\nalpha=%s, delta=%s\naz=%0.2f, alt=%0.2f%s" % (self.name, meteo.time.iso, self.alpha, self.delta, rad2deg(self.azimuth.value), rad2deg(self.altitude.value), msg)
			if observability == 1:
				print((util.hilite(to_print, True, True)))
				if not warnings == '': print((util.hilite(warnings, False, False)))
				print(("="*20))
			else:
				if displayall:
					print((util.hilite(to_print, False, False)))
					if not warnings == '': print((util.hilite(warnings, False, False)))
					print(("="*20))
				else:
					pass

		self.observability = observability


def showstatus(observables, meteo, obs_time=None, displayall=True, cloudscheck=True):
	"""
	Using a list of observables, print their observability at the given obs_time. The moon position 
	and all observables are updated according to the given obs_time. The wind is always taken at 
	the current time.

	displayall = True allows all the targets to be displayed, even if they cannot be observed
	"""

	# NO, we keep meteo update outside obs functions !
	# meteo.update(obs_time=obs_time)
	for observable in observables:
		observable.compute_observability(meteo=meteo, displayall=displayall,
								cloudscheck=cloudscheck, verbose=True)





def rdbimport(filepath, namecol=1, alphacol=2, deltacol=3, obsprogramcol=4, startline=1, obsprogram=None, verbose=False):

	"""
	Import an rdb catalog into a list of observables
	"""

	logger.debug("Reading \"%s\"..." % (os.path.basename(filepath)))
	rdbfile = open(filepath, "r")
	rdbfilelines = rdbfile.readlines()[startline:] # we directly "skip" the first lines of eventual headers
	rdbfile.close()

	observables = []
	for ind, line in enumerate(rdbfilelines) :

		if line[0] == "-" or line[0] == "#":
			continue

		if len(line.strip()) < 5:
			logger.debug("Skipping empty line %i : %s" % (ind+startline, repr(line)))
			continue

		elements = line.split()

		name = str(elements[namecol-1])
		alpha = str(elements[alphacol-1])
		delta = str(elements[deltacol-1])
		if obsprogramcol:
			try:
				obsprogram = str(elements[obsprogramcol-1])
				assert(len(elements) > 0)
				#todo: this is not robust against a column with incoherent obsprogram, or with a line without obsprogram. We do not want to load default config under the hood if an obsprogram is wrongly or not given. Maybe we could, but nevertheless warn the user about it in a dedicated popup ?
			except:
				logger.debug('nothing in obsprogramcol - using provided default instead')


		observables.append(Observable(name=name, obsprogram=obsprogram, alpha=alpha, delta=delta))

	return observables



def rdbexport(observables, filepath, namecol=1, alphacol=2, deltacol=3, obsprogramcol=4, verbose=False):
	"""
	Export a list of observables as an rdb catalogue, to be read again later
	"""

	pass


