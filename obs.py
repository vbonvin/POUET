"""
Define the Observable class, the standard object of pouet, and related functions
"""

from numpy import cos, rad2deg, isnan, arange
import os, sys
import copy as pythoncopy
import util
from astropy.time import Time
from astropy.coordinates import angles, angle_utilities

import matplotlib.pyplot as plt


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
	
		self.attributes = attributes
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

	def getaltaz(self, obs_time=Time.now()):
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

	def update(self, meteo, obs_time=Time.now()):

		self.getaltaz(obs_time=obs_time)
		self.getangletowind(meteo)
		self.getairmass()
		self.getangletomoon(meteo)

	def getobservability(self, meteo, obs_time=None, displayall=True, check_clouds=True, limit_cloud_validity=1800, verbose=True):
		"""
		Return the observability, a value between 0 and 1 that tells if the target can be observed at a given time

		The closer to 1 the better
		0 is impossible to observe
		"""
		# Otherwise we kept weird stuff because of the initialisation
		if obs_time is None: obs_time = Time.now()

		self.update(meteo=meteo, obs_time=obs_time)
		observability = 1 # by default, we can observe

		# Let's start with a simple yes/no version
		# We add a small message to display if it's impossible to observe:
		msg = ''
		warnings = ''

		### General conditions:


		# check the	moondistance:
		if self.angletomoon.degree < self.minangletomoon:
			observability -= 0.2
			msg += '\nMoonDist:%0.1f' % self.angletomoon.degree

		# check the airmass:
		if self.airmass > self.maxairmass:
			observability = 0
			msg += '\nAirmass:%0.2f' % self.airmass


		# check the wind:
		if self.angletowind.degree < 90 and meteo.windspeed > 15:
			observability = 0
			msg += '\nWA:%0.1f/WS:%0.1f' % (self.angletowind.degree, meteo.windspeed)

		if meteo.windspeed > 20:
			observability = 0
			msg += '\nWS:%s' % meteo.windspeed

		if check_clouds:
			time_since_last_refresh = (obs_time - meteo.allsky.last_im_refresh)
			time_since_last_refresh = time_since_last_refresh.value * 86400. # By default it's in days
			
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
		pobs, pmsg, pwarn = self.program.observability(self.attributes, obs_time)
		if pobs == 0: observability = 0
		msg += pmsg
		warnings += pwarn

		# Finally, add the eventuel comment:
		if hasattr(self, 'comment'):
			msg += '\n %s' % self.comment

		if verbose:
			to_print = "%s | %s\nalpha=%s, delta=%s\naz=%0.2f, alt=%0.2f%s" % (self.name, obs_time.iso, self.alpha, self.delta, rad2deg(self.azimuth.value), rad2deg(self.altitude.value), msg)
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


def showstatus(observables, meteo, obs_time=None, displayall=True, check_clouds=True):
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
								check_clouds=check_clouds, verbose=True)


def shownightobs(observable, meteo=None, obs_night=None, savefig=False, dirpath=None, verbose=False):
	"""
	Plot the observability of one observable along the night
	"""

	# list of times between nautical twilights
	times = util.get_nighthours(obs_night)

	mymeteo = pythoncopy.deepcopy(meteo) # as we don't want to affect the current meteo, we make a copy that we update with the time

	obss = []
	moonseps = []
	for time in times:
		mymeteo.update(obs_time=time, minimal=True) # This is the ONLY function in obs that updates the meteo !!
		observable.getobservability(meteo=mymeteo, obs_time=time, displayall=True, check_clouds=False, verbose=verbose)
		observable.getairmass()
		obss.append(observable.observability)
		moonseps.append(observable.angletomoon.degree)


	# create the x ticks labels every hour
	Time('%s 05:00:00' % obs_night, format='iso', scale='utc')
	hstart=22
	hend=12
	nhbm = 24-hstart  # number of hours before midnight...
	myhours = []
	for hour in arange(nhbm)[::-1]:
		myhours.append(24-(hour+1))
	for hour in arange(hend+1):
		myhours.append(hour)

	myhours = ["%02i:00:00" % h for h in myhours]
	mytimes = [Time('%s %s' % (obs_night, h), format='iso', scale='utc') for h in myhours[:nhbm]]

	for h in myhours[nhbm:]:
		t = Time('%s %s' % (obs_night, h), format='iso', scale='utc')
		t = Time(t.mjd + 1, format='mjd', scale='utc')
		mytimes.append(t)

	tmin, tmax = times[0].mjd, times[-1].mjd
	xmax=len(obss)
	xs = [(t.mjd-tmin)*xmax/(tmax-tmin) for t in mytimes]
	labels = [str(h[:5]) for h in myhours]

	starttimes = []
	stoptimes = []
	if 1 in obss:
		starttimes.append(times[obss.index(1)])
		stoptimes.append(times[::-1][obss[::-1].index(1)])

	if 0.8 in obss:
		starttimes.append(times[obss.index(0.8)])
		stoptimes.append(times[::-1][obss[::-1].index(0.8)])

	if not 1 in obss and not 0.8 in obss:
			print "%s is not observable tonight !" % observable.name
			return

	starttime = min(starttimes)
	stoptime = max(stoptimes)

	# shift the start and stoptime if needed
	if starttime.mjd > stoptime.mjd - (observable.exptime/60./1440.):
		starttime = Time(stoptime.mjd - (observable.exptime/60./1440.), format='mjd', scale='utc')

	if stoptime.mjd < starttime.mjd + (observable.exptime/60./1440.):
		stoptime = Time(starttime.mjd + (observable.exptime/60./1440.), format='mjd', scale='utc')

	starttime = starttime.iso
	stoptime = stoptime.iso


	msg = ''
	plt.figure(figsize=(8,1.3))
	plt.subplots_adjust(left=0.02, right=0.98, bottom=0.45, top=0.7)
	ax = plt.subplot(1, 1, 1)
	xticks = arange(len(obss))
	plt.xticks(xs, labels, fontsize=16)
	# green, everything is fine
	if 1 in obss:
		plt.axvspan(obss.index(1), len(obss)-obss[::-1].index(1), color='chartreuse')
	# blue, problem with moon sep
	if 0.8 in obss:
		plt.axvspan(obss.index(0.8), len(obss)-obss[::-1].index(0.8), color='royalblue')
		msg += "Moonsep = %i" % int(min(moonseps))
	plt.axis([min(xticks), max(xticks), 0.0, 1.0])
	ax.get_yaxis().set_visible(False)
	plt.xlabel('UT', fontsize=18)
	if msg != '':
		plt.annotate(msg, xy=(0, -1.5),  xycoords='axes fraction', fontsize=14, color="royalblue")
	plt.suptitle(observable.name+" ("+starttime.split(" ")[1][:5]+" --> "+stoptime.split(" ")[1][:5]+")", fontsize=25, y=0.93)

	if savefig:
		assert dirpath != None
		if not os.path.isdir(os.path.join(dirpath, obs_night)):
			os.mkdir(os.path.join(dirpath, obs_night))
		path = os.path.join(dirpath, obs_night, observable.name+'.png')
		plt.savefig(path)
		print "Plot saved on %s" % path
	else:
		plt.show()



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
			observables.append(Observable(name=name, obsprogram=obsprogram, alpha=alpha, delta=delta, minangletomoon=minangletomoon, maxairmass=maxairmass, exptime=exptime))

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