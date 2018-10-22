"""
Define the Observable class, the standard object of pouet, and related functions
"""

from numpy import cos, rad2deg, isnan, arange
import numpy as np
import os, sys, inspect
import copy as pythoncopy
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import angles, angle_utilities, SkyCoord
import astropy.table
import importlib
import util

import logging
logger = logging.getLogger(__name__)

global SETTINGS
herepath = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
SETTINGS = util.readconfig(os.path.join(herepath, "config/settings.cfg"))


class Observable:
	"""
	Class to hold a specific target from any observational progamm

	Unvariable parameters are defined at initialisation

	Variable parameters (distance to moon, azimuth, observability,...) are undefined until associated methods are called
	"""
	def __init__(self, name='emptyobservable', obsprogram=None, attributes=None, alpha=None, delta=None, minangletomoon=None, maxairmass=None, exptime=None):
		"""
		Constructor

		An observable is the basic building bloc of POUET. It stores all the values of a target that are needed to compute its observability at a given time from a given position


		:param name: string, name of the observable
		:param obsprogram: string, related to one of the existing programs defined in :any:'obsprogram'
		:param attributes: any type of extra information about the target you want to store
		:param alpha: Right Ascension angle, in hours HH:MM:ss
		:param delta: Declination angle, in degree DD:MM:ss
		:param minangletomoon: float, minimum angle in the sky plane to the moon below which the target is not to be observed
		:param maxairmass: float, maximum airmass below which the target is not to be observed
		:param exptime: float, expected exposure time of the target
		"""
		self.name = name
		self.obsprogram = obsprogram

		if not self.obsprogram == None:
			try:
				module_name = "obsprogram.prog{}".format(self.obsprogram)
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

	def __str__(self):
		"""
		:return: message printing the current altitude, azimuth and airmass of the target, if defined.

		.. note:: to have these values defined, you must first call :meth:'~obs.Observable.compute_altaz' and :meth:'~obs.Observable.compute_airmass', using a :py:'meteo.Meteo' object
		"""

		msg = "="*30+"\nName:\t\t%s\nProgram:\t%s\nAlpha:\t\t%s\n" \
				  "Delta:\t\t%s\n" %(self.name, self.obsprogram, self.alpha.hour, self.delta.degree)

		try:
			msg += "Altitude:\t%s\n"%self.altitude.degree
		except AttributeError:
			msg += "Altitude:\tNone\n"

		try:
			msg += "Azimuth:\t%s\n"%self.azimuth.degree
		except AttributeError:
			msg += "Azimuth:\tNone\n"

		try:
			msg += "Airmass:\t%s\n"%self.airmass
		except AttributeError:
			msg += "Airmass:\tNone\n"

		return msg

	def copy(self):
		"""
		:return: an, observable, python deep copy of the current observable
		"""
		return pythoncopy.deepcopy(self)

	def compute_angletomoon(self, meteo):
		"""
		Computes the distance to the moon

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand
		"""
		if SETTINGS["misc"]["singletargetlogs"] == "True":
			logger.debug("Computing angletomoon for {}...".format(self.name))
		moonalt, moonaz = meteo.moonalt, meteo.moonaz
		alt, az = self.altitude, self.azimuth
		separation = angle_utilities.angular_separation(moonaz, moonalt, az, alt) # Warning, separation is in radian!!

		angletomoon = angles.Angle(separation.value, unit="radian")
		self.angletomoon = angletomoon

	def compute_angletosun(self, meteo):
		"""
		Computes the distance to the Sun

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand
		"""
		if SETTINGS["misc"]["singletargetlogs"] == "True":
			logger.debug("Computing angletosun for {}...".format(self.name))
		sunalt, sunaz = meteo.sunalt, meteo.sunaz
		alt, az = self.altitude, self.azimuth
		separation = angle_utilities.angular_separation(sunaz, sunalt, az, alt) # Warning, separation is in radian!!

		angletosun = angles.Angle(separation.value, unit="radian")
		self.angletosun = angletosun

	def compute_angletowind(self, meteo):
		"""
		Computes the angle to wind

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand
		"""
		if SETTINGS["misc"]["singletargetlogs"] == "True":
			logger.debug("Computing angletowind for {}...".format(self.name))
		winddirection = meteo.winddirection
		if winddirection < 0 or winddirection > 360:
			self.angletowind = None
			return
		
		try:
			winddirection = angles.Angle(winddirection, unit='degree')
			self.angletowind = angle_utilities.angular_separation(winddirection, 0., self.azimuth, 0.)
			self.angletowind = angles.Angle(self.angletowind, unit="radian")
		except AttributeError:
			logger.error("{} has no azimuth! \n Compute its azimuth first !".format(self.name))
			raise AttributeError("%s has no azimuth! \n Compute its azimuth first !")

	def compute_altaz(self, meteo):
		"""
		Computes the altitude and azimuth of the observable.

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand

		"""
		if SETTINGS["misc"]["singletargetlogs"] == "True":
			logger.debug("Computing Altitude and Azimuth for {}...".format(self.name))
		azimuth, altitude = meteo.get_AzAlt(self.alpha, self.delta, obs_time=meteo.time)
		self.altitude = altitude
		self.azimuth = azimuth

	def compute_airmass(self, meteo):
		"""
		Computes the airmass of the observable.

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand

		"""
		if SETTINGS["misc"]["singletargetlogs"] == "True":
			logger.debug("Computing airmass for {}...".format(self.name))
		self.airmass = util.elev2airmass(self.altitude.radian, meteo.elev)

	def is_cloudfree(self, meteo):
		"""
		Computes whether the pointing direction is cloudy according to the altaz coordinates in memory

		:param meteo: a Meteo object, whose cloudmap attribute has been actualized beforehand

		todo: instead of taking altaz coordinates in memory, shouldn't we use meteo.time to recompute altaz on the fly?

		.. note:: is_cloudfree is actualized with 0: cloudy or 1: no clouds. If unavailable, returns 2: connection error, if error during computation of observability from map: 3
		"""

		# TODO: the cloud status should be done in a status function of the meteo object, not here! This will also allow a cleaner log writing.

		if SETTINGS["misc"]["singletargetlogs"] == "True":
			logger.debug("Computing cloud coverage for {}...".format(self.name))
		ERROR_CONN = 2.
		ERROR_COMPUTE = 3.

		xpix, ypix = meteo.allsky.station.get_image_coordinates(self.azimuth.value, self.altitude.value)
		
		if meteo.cloudmap is None:
			self.cloudfree = ERROR_CONN
			if SETTINGS["misc"]["singletargetlogs"] == "True":
				logger.warning("No cloud map in meteo object")
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
			if SETTINGS["misc"]["singletargetlogs"] == "True":
				logger.warning("Computational error in clouds")
			return

		self.cloudcover = 1.-np.floor(float(self.cloudfree)*10.)/10.

	def update(self, meteo):
		"""
		Update the observable parameters according to the meteo object passed: altitude, azimuth, angle to wind, airmass, angle to moon and angle to sun.

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand
		"""
		if SETTINGS["misc"]["singletargetlogs"] == "True":
			logger.debug("Updating parameters for {}...".format(self.name))
		self.compute_altaz(meteo)
		self.compute_angletowind(meteo)
		self.compute_airmass(meteo)
		self.compute_angletomoon(meteo)
		self.compute_angletosun(meteo)


	def compute_observability(self, meteo, cwvalidity=30, cloudscheck=True, verbose=True, displayall=True, future=False):
		"""
		Update the status using :meth:`~obs.Observable.update`. Compute the observability param, a value between 0 and 1 that tells if the target can be observed at a given time. Also define flags for each parameter (moon, wind, etc...)

		The closer to 1 the better
		0 is impossible to observe

		:param meteo: a Meteo object, whose time attribute has been actualized beforehand
		:param cwvalidity: float, current weather validity: time (in minutes) after/before which the allsky cloud coverage and wind are not taken into account in the observability, effectively setting the future variable to True
		:param verbose: boolean, displaying the status of the observable according to the present function
		:param displayall: boolean, if verbose is True, then print also the targets that are not observable.
		:param future: boolean, if set to True then cloud coverage and wind are note taken into account in the observability.
		"""
		if SETTINGS["misc"]["singletargetlogs"] == "True":
			logger.debug("Computing observability for {}...".format(self.name))
			logger.info("Current time is %s" % meteo.time)
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
			observability *= 0.8
			self.obs_moondist = False
			msg += '\nMoonDist:%0.1f' % self.angletomoon.degree

		# high airmass
		self.obs_highairmass = True
		if self.airmass > 1.5:
			self.obs_highairmass = False
			observability *= 0.7
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
		self.obs_clouds, self.obs_clouds_info = cloudscheck, True
		if not future:
			if cloudscheck:
				self.is_cloudfree(meteo)
				if self.cloudfree <= 0.5 :
					self.obs_clouds = False
					warnings += '\nWarning ! It might be cloudy'
					observability = 0
				elif self.cloudfree <= 0.9:
					self.obs_clouds = False
					msg += '\nCould be cloud-free'
					observability *= self.cloudfree
				elif self.cloudfree <= 1.:
					msg += '\nShould be cloud-free'
				else:
					self.obs_clouds_info = False
					warnings += '\nNo cloud info'
					#print("no cloud info")
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

		to_print = "%s | %s\nalpha=%s, delta=%s\naz=%0.2f, alt=%0.2f%s" % (self.name, meteo.time.iso, self.alpha, self.delta, rad2deg(self.azimuth.value), rad2deg(self.altitude.value), msg)
		if verbose:
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
		else:
			# then we send the print message to the logger
			if SETTINGS["misc"]["singletargetlogs"] == "True":
				logger.info(to_print)
		self.observability = observability


def showstatus(observables, meteo, displayall=True, cloudscheck=True):
	"""
	print the observability of a list of observables according to a given meteo.

	:param observables: list of observables, :meth:'~obs.Observable'
	:param displayall: boolean, if set to True then display the status of all the targets, even those which are not visible.
	:param cloudscheck: boolean, if set to True then use the cloud coverage in the observability computation.
	"""
	for observable in observables:
		observable.compute_observability(meteo=meteo, displayall=displayall,cloudscheck=cloudscheck, verbose=True)


#todo: refactor rdbimport and rdbexport to pouetimport and pouetexport
def rdbimport(filepath, namecol=1, alphacol=2, deltacol=3, obsprogramcol=4, obsprogram=None):

	"""
	Import an rdb catalog into a list of observables

	Must be compatible with astropy Table reader (i.e. a header line, then an empty/blank/comment line, then each obs in a dedicated line, attributes separater by a tab or a space)

	:param filepath: path to the file you want to import. Must be a text file, format is not important.
	:param namecol: integer, index of the column containing the names
	:param alphacol: integer, index of the column containing the right ascension
	:param deltacol: integer, index of the column containing the declination
	:param obsprogramcol: integer, index of the column containing the obs program. If not provided, use the provided obsprogram instead.
	:param obsprogram: which :any:'obsprogram.__init__' is to be used as a default if nothing is provided from the imported file.

	.. note:: providing an obsprogramcol overloads the given obsprogram, as long as there is a valid field in the rdb obsprogramcol. You can use both to load a catalogue that has only part of its programcol defined.
	"""
	logger.debug("Reading \"%s\"..." % (os.path.basename(filepath)))

	# data_start = 2 is to deal with the rdb file... (ascii.rdb doesn't work good)
	rdbtable = astropy.table.Table.read(filepath, format="ascii", data_start=2)

	colnames = rdbtable.colnames

	observables = []
	for line in rdbtable :

		name = str(line[colnames[namecol-1]])
		alpha = str(line[colnames[alphacol-1]])
		delta = str(line[colnames[deltacol-1]])

		if obsprogramcol:
			try:
				obsprogram = str(line[colnames[obsprogramcol-1]])
				assert(len(obsprogram) > 0)
				#todo: this is not robust against a column with incoherent obsprogram, or with a line without obsprogram. We do not want to load default config under the hood if an obsprogram is wrongly or not given. Maybe we could, but nevertheless warn the user about it in a dedicated popup ?
			except:
				logger.debug('nothing in obsprogramcol - using provided default instead')


		observables.append(Observable(name=name, obsprogram=obsprogram, alpha=alpha, delta=delta))
	logger.info("Imported \"%s\"..." % (os.path.basename(filepath)))
	return observables


def rdbexport(filepath, observables, append=False):
	"""
	Save a list of observables at a given filepath, respecting the formatting used when default importing with :meth:'obs.rdbimport'.

	:param filepath: string. Path of where the .pouet file is written
	:param observables: list of Observables to save
	:param append: boolean. If True, then the current observables are added to the existing list

	.. note:: append=True only works if the file you want to append to has the correct formatting. See headerline and headersubline in the source code.
	"""
	logger.debug("Saving observables...")
	headerline = "name\talpha\tdelta\tobsprogram\n"
	headersubline = "----\t-----\t-----\t----------\n"

	#todo: add a backup function

	# check that the base folder exists
	dirpath = os.path.dirname(os.path.abspath(filepath))
	if not os.path.isdir(dirpath):
		os.makedirs(dirpath)
		logger.info("Directory %s has been created" % dirpath)
		#raise ValueError('Directory %s does not exist' % dirpath)

	if not append:
		f = open(filepath, 'w')
		# write header
		f.write(headerline)
		f.write(headersubline)

	else:
		# check that the file exists
		if not os.path.isfile(filepath):
			f = open(filepath, 'w')
			# write header
			f.write(headerline)
			f.write(headersubline)

		else:
			# check that header lines corresponds to the standard template
			lines = open(filepath, 'r').readlines()[:2]
			if not lines[0] == headerline and lines[1] == headersubline:
				logger.error("Header format not standard")
				raise ValueError('Header format not standard')
			else:
				f = open(filepath, 'a')

	for o in observables:
		f.write("%s\t%s\t%s\t%s\n" % (o.name, o.alpha.to_string(unit=u.hour, sep=':', pad=True), o.delta.to_string(unit=u.degree, sep=':', pad=True), o.obsprogram))

	f.close()
	logger.info("List of observable saved under {}".format(filepath))
	return

	# astropy tables does not work (bug??), puts a line with "S" in the rdb file...
	"""
	names = ['----'] + [o.name for o in observables]
	alphas = ['-----'] + [o.alpha.to_string(unit=u.hour, sep=':', pad=True) for o in observables]
	deltas = ['-----'] + [o.delta.to_string(unit=u.degree, sep=':', pad=True) for o in observables]
	obsprograms = ['----------'] + [o.obsprogram for o in observables]

	towrite = astropy.table.Table({'name': names, 'alpha': alphas, 'delta': deltas, 'obsprogram': obsprograms})

	towrite.write(filepath, format="rdb", overwrite=True)
	"""
