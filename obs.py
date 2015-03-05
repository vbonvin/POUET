"""
Define the Observable class, the standard object of pouet, and related functions
"""

from numpy import cos
import os,sys,glob
import copy as pythoncopy
import Azimuth
import util
import meteo
from astropy.time import Time
import astropy.coordinates.angles as angles

class Observable:
	"""
	Class to hold a specific target from any observational progamm

	Unvariable parameters are defined at initialisation

	Variable parameters (distance to moon, azimuth, observability,...) are undefined until associated methods are called
	"""

	def __init__(self, name='emptyobservable', obsprogram=None, alpha=None, delta=None, minmoondistance=None, maxairmass=None, exptime=None):

		self.name = name
		self.obsprogram = obsprogram

		self.alpha = angles.Angle(alpha, unit="hour")
		self.delta = angles.Angle(delta, unit="degree")

		self.moondistance = minmoondistance
		self.maxairmass = maxairmass
		self.exptime = exptime
	#self.observability = observability


	def __str__(self):


		# not very elegant

		msg = "="*30+"\nName:\t\t%s\nProgram:\t%s\nAlpha:\t\t%s\n" \
				  "Delta:\t\t%s\n" %(self.name, self.obsprogram, self.alpha.hour, self.delta.degree)

		try:
			msg+= "Altitude:\t%s\n"%self.altitude.degree
		except AttributeError:
			msg+= "Altitude:\tNone\n"

		try:
			msg+= "Azimuth:\t%s\n"%self.azimuth.degree
		except AttributeError:
			msg+= "Azimuth:\tNone\n"

		try:
			msg+= "Airmass:\t%s\n"%self.airmass
		except AttributeError:
			msg+= "Airmass:\tNone\n"


		return msg


	def copy(self):
		return pythoncopy.deepcopy(self)

	def getdistancetomoon(self, alphamoon, deltamoon):
		print "undefinded"
		distancetomoon = 0
		self.distancetomoon = distancetomoon
		return distancetomoon

	def getangletowind(self, meteo):
		"""
		Actualize the angle to wind, from the most recent meteo update and altitude and azimuth computed

		WARNING : you need to actualize the meteo and altaz by yourself before calling this function !

		TODO: implement a warning flag when the wind is above pointing limit...? or do it somewhere else ?

		:param meteo: a Meteo object, from where I get the wind

		:return: actualize angle to wind and return it
		"""

		winddirection = meteo.winddirection
		try:
			angletowind = abs(winddirection-self.azimuth.degree)
			self.angletowind = angletowind
			return angletowind

		except AttributeError:
			print "%s has no azimuth! \n Compute its azimuth first !"
			sys.exit()

	def getaltaz(self, obs_time=Time.now()):
		"""
		Actualize altitude and azimuth of the observable at the given observation time.

		:param obs_time: time of observation. Default = current execution time
		:return: actualise altitude and azimuth for obs_time, and return them
		"""
		azimuth, altitude = util.get_AzAlt(self.alpha, self.delta, obs_time=obs_time)
		self.altitude = altitude
		self.azimuth = azimuth
		return (azimuth, altitude)

	def getairmass(self):

		"""
		Compute the airmass using the altitude. We cap the maximum value at 10.

		:return: actualize airmass and return it
		"""
		try:
			zenith = angles.Angle(90-self.altitude.degree, unit="degree")
			airmass = 1.0/cos(zenith.radian)
			if airmass < 0 or airmass > 10:
				airmass = 10
			self.airmass = airmass
			return airmass

		except AttributeError:
			print "%s has no altitude! \n Compute its altutide first !"
			sys.exit()

	def update(self, meteo, obs_time=Time.now()):

		self.getaltaz(obs_time=obs_time)
		self.getangletowind(meteo)
		self.getairmass()


def rdbimport(filepath, namecol=1, alphacol=2, deltacol=3, startline=1, obsprogram="None", verbose=False):
	"""
	Import an rdb catalog into a list of observables
	"""

	if verbose : print "Reading \"%s\"..." % (os.path.basename(filepath))
	rdbfile = open(filepath, "r")
	rdbfilelines = rdbfile.readlines()[startline:] # we directly "skip" the first lines of eventual headers
	rdbfile.close()

	observables = []

	for ind, line in enumerate(rdbfilelines) :

		if line[0] == "-" or line[0] == "#":
			continue

		if len(line.strip()) < 5:
			print "Skipping empty line %i : %s" % (ind+startline, repr(line))
			continue

		elements = line.split()

		name = str(elements[namecol-1])
		alpha = str(elements[alphacol-1])
		delta = str(elements[deltacol-1])

		# This is the minimal stuff necessary to define an observable. Now, let's go into the per-obsprogram details

		if obsprogram not in ["lens", "transit", "bebop", "superwasp", "followup", "703", "714"]:
			observables.append(Observable(name=name, obsprogram=obsprogram, alpha=alpha, delta=delta))


		if obsprogram == "lens":
			minmoondistance = 30
			maxairmass = 1.5
			exptime = 35*60 #approx 35 minutes per lens
			observables.append(Observable(name=name, obsprogram=obsprogram, alpha=alpha, delta=delta, minmoondistance=minmoondistance, maxairmass=maxairmass, exptime=exptime))

		if obsprogram == "transit":
			pass

		if obsprogram == "bebop":
			pass

		if obsprogram == "superwasp":
			pass

		if obsprogram == "followup":
			pass

		if obsprogram == "703":
			pass

		if obsprogram == "714":
			pass

	return observables

def excelimport():
	"""
	Import an excel catalog(...) into a list of observables
	That one is going to be tricky...
	"""
	pass


def rdbexport():
	"""
	Export a (sorted) list of observables as an rdb catalogue, to be read by edp
	"""
	pass