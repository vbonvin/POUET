"""
Define the Observable class, the standard object of pouet, and related functions
"""

from numpy import cos, rad2deg, isnan
import os, sys
import copy as pythoncopy
import util
import astropy.time as asti
from astropy.coordinates import angles, angle_utilities


class Observable:
	"""
	Class to hold a specific target from any observational progamm

	Unvariable parameters are defined at initialisation

	Variable parameters (distance to moon, azimuth, observability,...) are undefined until associated methods are called
	"""

	def __init__(self, name='emptyobservable', obsprogram=None, obj=None, alpha=None, delta=None, 
				minangletomoon=None, maxairmass=None, exptime=None):


		self.name = name
		self.obsprogram = obsprogram
		
		try:
			exec("import obsprogram.prog%s as program" % (self.obsprogram))
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
	
		self.obj = obj
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

	def getangletomoon(self, meteo):
		"""
		Compute the distance to the moon

		:param meteo:
		:return:
		"""

		moonalt, moonaz = meteo.moonalt, meteo.moonaz
		alt, az = self.altitude, self.azimuth
		separation = angle_utilities.angular_separation(moonaz, moonalt, az, alt) # Warning, separation is in radian!!

		angletomoon = angles.Angle(separation.value, unit="radian")

		self.angletomoon = angletomoon




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
			self.angletowind = angles.Angle(angletowind, unit='degree')


		except AttributeError:
			raise AttributeError("%s has no azimuth! \n Compute its azimuth first !")

	def getaltaz(self, obs_time=asti.Time.now()):
		"""
		Actualize altitude and azimuth of the observable at the given observation time.

		:param obs_time: time of observation. Default = current execution time
		:return: actualise altitude and azimuth for obs_time, and return them
		"""
		azimuth, altitude = util.get_AzAlt(self.alpha, self.delta, obs_time=obs_time)
		self.altitude = altitude
		self.azimuth = azimuth


	def getairmass(self):

		"""
		Compute the airmass using the altitude. We cap the maximum value at 10.

		:return: actualize airmass and return it
		"""

		#TODO : see how the computation belows varies regarding Euler computation (in CoordinatesAwayFromMoon)

		try:
			zenith = angles.Angle(90-self.altitude.degree, unit="degree")
			airmass = 1.0/cos(zenith.radian)
			if airmass < 0 or airmass > 10:
				airmass = 10
			self.airmass = airmass


		except AttributeError:
			raise AttributeError("%s has no altitude! \n Compute its altutide first !")

	def update(self, meteo, obs_time=asti.Time.now()):

		self.getaltaz(obs_time=obs_time)
		self.getangletowind(meteo)
		self.getairmass()
		self.getangletomoon(meteo)

	def getobservability(self, meteo, obs_time=asti.Time.now(), displayall=True, check_clouds=True, limit_cloud_validity=1800):
		"""
		Return the observability, a value between 0 and 1 that tells if the target can be observed at a given time

		The closer to 1 the better
		0 is impossible to observe
		"""

		self.update(meteo=meteo, obs_time=obs_time)
		observability = 1 # by default, we can observe

		# Let's start with a simple yes/no version
		# We add a small message to display if it's impossible to observe:
		msg = ''
		warnings = ''

		### General conditions:
		# check the airmass:
		if self.airmass > self.maxairmass:
			observability = 0
			msg += '\nAirmass:%0.2f' % self.airmass

		# check the	moondistance:
		if self.angletomoon.degree < self.minangletomoon:
			observability = 0
			msg += '\nMoonDist:%0.1f' % self.angletomoon.degree

		# check the wind:
		if self.angletowind.degree < 90 and meteo.windspeed > 15:
			observability = 0
			msg += '\nWA:%0.1f/WS:%0.1f' % (self.angletowind.degree, meteo.windspeed)

		if meteo.windspeed > 20:
			observability = 0
			msg += '\nWS:%s' % meteo.windspeed
		
		if check_clouds:
			time_since_last_refresh = (obs_time - meteo.allsky.last_im_refresh)
			print obs_time
			print meteo.allsky.last_im_refresh
			time_since_last_refresh = time_since_last_refresh.value * 86400. # By default it's in days
			print type(time_since_last_refresh.value)
			exit()
			if time_since_last_refresh < limit_cloud_validity:
				clouds = meteo.is_cloudy(self.azimuth.value, self.altitude.value)
				if clouds < 0.5 :
					warnings += '\nWarning ! It might be cloudy'
				elif isnan(clouds):
					warnings += '\nWarning ! No cloud info'

		# check the internal observability flag
		if hasattr(self, 'internalobs'):
			if self.internalobs == 0:
				observability = self.internalobs
				msg += '\nSpreadsheet NO'


		### Program specific conditions:
		po, pmsg, pwarn = self.program.observability(self.obj, obs_time)
		if po == 0: observability = 0
		msg += pmsg
		warnings += pwarn
		## Bebop
		# check the phases. time is obs_time
		if self.obsprogram == 'bebop':
			time = obs_time.mjd
			phase = util.takeclosest(self.phases, 'phase', time)
			if phase['phase'] < 0.03 or phase['phase'] > 0.97:
				observability = 0
			msg += '\nPhase = %.2f' % phase['phase']  # we display the phase anyway

		#sys.exit()

		# Finally, add the eventuel comment:
		if hasattr(self, 'comment'):
			msg += '\n %s' % self.comment

		to_print = "%s\nalpha=%s, delta=%s\naz=%0.2f, alt=%0.2f%s" % (self.name, self.alpha, self.delta, 
			rad2deg(self.azimuth.value), rad2deg(self.altitude.value), msg)
		if observability == 1:
			print util.hilite(to_print, True, True)
			if not warnings == '': print util.hilite(warnings, False, False)
			print "="*20
		else:
			if displayall:
				print util.hilite(to_print, False, False)
				if not warnings == '': print util.hilite(warnings, False, False)
				print "="*20
			else:
				pass

		self.observability = observability


def showstatus(observables, meteo, obs_time=asti.Time.now(), displayall=True, check_clouds=True):
	"""
	Using a list of observables, print their observability at the given obs_time. The moon position 
	and all observables are updated according to the given obs_time. The wind is always taken at 
	the current time.

	displayall = True allows all the targets to be displayed, even if they cannot be observed
	"""

	# NO, we keep meteo update outside obs functions !
	#meteo.update(obs_time=obs_time)
	for observable in observables:
		observable.getobservability(meteo=meteo, obs_time=obs_time, displayall=displayall, 
								check_clouds=check_clouds)

	
def rdbimport(filepath, namecol=1, alphacol=2, deltacol=3, startline=1, obsprogram="None", verbose=False):
	"""
	Import an rdb catalog into a list of observables
	THIS SHOULD BE IN UTIL !!
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
			minangletomoon = 30
			maxairmass = 1.5
			exptime = 35*60 #approx 35 minutes per lens
			observables.append(Observable(name=name, obsprogram=obsprogram, alpha=alpha, delta=delta, 
							minangletomoon=minangletomoon, maxairmass=maxairmass, exptime=exptime))

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



def rdbexport():
	"""
	Export a (sorted) list of observables as an rdb catalogue, to be read by edp
	THIS SHOULD BE IN UTIL !
	"""
	pass