import matplotlib.pyplot as plt
import matplotlib as mpl
import astropy.units as u
from astropy.time import Time
from astropy.wcs import WCS
import numpy as np
import os, sys

import util

def plot_airmass_on_sky(target, meteo, ax=None):
	"""
	 Plots the airmass evolution on the sky of a given target at a given time.

	 :param target: a `pouet.obs.Observable` class instance
	 :param meteo: a `pouet.meteo.Meteo` class instance
	 :param ax: the matplotlib axis to plot on. If None, then plot on a new figure
	 """

	delta_ts = np.linspace(-5, 5, 101)
	assert 0 in delta_ts
	index_zero = np.where(delta_ts == 0)[0][0]

	obs_time = meteo.time
	obs_times = obs_time + delta_ts * u.hour

	if ax is None:
		plt.figure()
		ax = plt.gca(projection='polar')

	plt.subplots_adjust(right=0.98)
	plt.subplots_adjust(left=0.02)

	airmasses = []
	azimuths = []
	altitudes = []
	times = []

	for currenttime in obs_times:

		azimuth, altitude = meteo.get_AzAlt(target.alpha, target.delta, obs_time=currenttime)

		if altitude.degree > 0:
			azimuths.append(azimuth.radian)
			altitudes.append(90. - altitude.degree)
			airmasses.append(util.elev2airmass(altitude.value, meteo.elev))
			times.append(currenttime)
		else:
			azimuths.append(np.nan)
			altitudes.append(np.nan)
			airmasses.append(np.nan)
			times.append(np.nan)

	# More axes set-up.
	# Position of azimuth = 0 (data, not label).
	ax.set_theta_zero_location('N')

	# Direction of azimuth increase. Clockwise is -1
	north_to_east_ccw = True
	if north_to_east_ccw is False:
		ax.set_theta_direction(-1)

	# Plot target coordinates.
	sp = ax.scatter(azimuths, altitudes, c=airmasses, s=20, vmin=1, vmax=2.0,
	                cmap=plt.get_cmap("coolwarm"))  # , alpha=0.7) # previous cmap: YlGn_r

	# Airmass colobar
	cbar = plt.colorbar(sp, pad=.1, ax=ax, shrink=0.9)
	cbar.set_label("Airmass")

	ax.set_title(
		"Airmass between {} and {} for {}".format(util.time2hhmm(obs_times[0]), util.time2hhmm(obs_times[-1]),
		                                          target.name), \
		fontsize=10, y=1.08)

	# Now plot for obs_time, and add some time ticks
	degree_sign = u'\N{DEGREE SIGN}'
	ax.scatter(azimuths[index_zero], altitudes[index_zero], marker="x", c='darkorange')
	str_time = util.time2hhmm(obs_times[index_zero])
	ax.annotate(str_time, xy=(azimuths[index_zero], altitudes[index_zero]), fontsize=12, ha="center", va="top",
	            color="darkorange")

	for ele in [15, 30, 45, 60, 75]:
		if ele < 40:
			fmt = "{:1.2f}"
		else:
			fmt = "{:1.1f}"

		ax.annotate('{:d}{:s}'.format(ele, degree_sign), xy=(np.deg2rad(-23), ele), fontsize=8, color="grey",
		            ha='center',
		            va='bottom', rotation=-25)
		ax.annotate(fmt.format(util.elev2airmass(np.deg2rad(90. - ele), meteo.elev)), xy=(np.deg2rad(23), ele),
		            fontsize=8,
		            color="grey", ha='center', va='bottom', rotation=25)

	ax.annotate("Airmass", xy=(np.deg2rad(23), 88), fontsize=8, color="grey", ha='center', va='bottom', rotation=25)
	ax.annotate('0' + degree_sign + ' Alt', xy=(np.deg2rad(-23), 89), fontsize=8, color="grey", ha='center',
	            va='bottom',
	            rotation=-23)

	for ii in range(np.size(airmasses)):

		if not ii % 20 == 0:
			continue

		str_time = util.time2hhmm(obs_times[ii])
		ax.annotate(str_time, xy=(azimuths[ii], altitudes[ii]), fontsize=12, ha="left", va="baseline", color="k")
		ax.scatter(azimuths[ii], altitudes[ii], marker=".", c='darkorange', s=2)
	ax.set_rlim(1, 90)

	r_labels = ['', '', '', '', '', '', '', ]
	ax.set_rgrids(range(0, 105, 15), r_labels)

	# Redraw the figure for interactive sessions.
	ax.figure.canvas.draw()


def shownightobs(observable, meteo, obs_night=None, savefig=False, dirpath=None, verbose=False):
	"""
	Plot the observability of one observable along the night


	#todo: add the option to be returned in an Axes object instead of plotting
	"""

	if not obs_night:
		meteo.time.format = 'iso'
		hour = int(meteo.time.value.split()[1][:2])
		if hour < 12:
			obs_night = Time(meteo.time.mjd - 1, format='mjd', scale='utc')
		else:
			obs_night = Time(meteo.time.mjd, format='mjd', scale='utc')
		obs_night.format = 'iso'
		obs_night = obs_night.value.split()[0]

	# list of times between nautical twilights
	times = meteo.get_nighthours(obs_night)

	#mymeteo = pythoncopy.deepcopy(meteo) # as we don't want to affect the current meteo, we make a copy that we update with the time


	mymeteo = meteo

	obss = []
	moonseps = []
	airmasses = []
	for time in times:
		mymeteo.update(obs_time=time, minimal=True)
		observable.compute_observability(meteo=mymeteo, displayall=True, cloudscheck=False, verbose=verbose)
		observable.compute_airmass(mymeteo)
		obss.append(observable.observability)
		moonseps.append(observable.angletomoon.degree)
		airmasses.append(observable.airmass)


	# create the x ticks labels every hour
	Time('%s 05:00:00' % obs_night, format='iso', scale='utc')
	hstart=22
	hend=12
	nhbm = 24-hstart  # number of hours before midnight...
	myhours = []
	for hour in np.arange(nhbm)[::-1]:
		myhours.append(24-(hour+1))
	for hour in np.arange(hend+1):
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

	# todo: this needs to be improved.
	if 1 in obss:
		starttimes.append(times[obss.index(1)])
		stoptimes.append(times[::-1][obss[::-1].index(1)])

	if 0.8 in obss:
		starttimes.append(times[obss.index(0.8)])
		stoptimes.append(times[::-1][obss[::-1].index(0.8)])

	if 0.7 in obss:
		starttimes.append(times[obss.index(0.7)])
		stoptimes.append(times[::-1][obss[::-1].index(0.7)])

	if 0.5 in obss:
		starttimes.append(times[obss.index(0.5)])
		stoptimes.append(times[::-1][obss[::-1].index(0.5)])

	if not 1 in obss and not 0.8 in obss and not 0.7 in obss and not 0.5 in obss:
			print(("%s is not observable tonight !" % observable.name))
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



	plt.figure(figsize=(8,1.3))
	plt.subplots_adjust(left=0.02, right=0.98, bottom=0.45, top=0.7)
	ax = plt.subplot(1, 1, 1)
	xticks = np.arange(len(obss))
	plt.xticks(xs, labels, fontsize=16)
	# green, everything is fine
	if 1 in obss:
		plt.axvspan(obss.index(1), len(obss)-obss[::-1].index(1), color='chartreuse')
	# blue, problem with moon sep, airmass or both. #todo: code that better
	if 0.8 in obss:
		color = "royalblue"
		plt.axvspan(obss.index(0.8), len(obss)-obss[::-1].index(0.8), color=color)
		msg = "Moonsep = %i" % int(min(moonseps))
		plt.annotate(msg, xy=(0, -1.5),  xycoords='axes fraction', fontsize=14, color=color)
	if 0.7 in obss:
		color = "royalblue"
		plt.axvspan(obss.index(0.7), len(obss)-obss[::-1].index(0.7), color=color)
		msg = "Airmass > 1.5"
		plt.annotate(msg, xy=(0, -1.5),  xycoords='axes fraction', fontsize=14, color=color)

	if 0.5 in obss:
		color = "indianred"
		plt.axvspan(obss.index(0.5), len(obss)-obss[::-1].index(0.5), color='indianred')
		msg = "Moonsep = %i, Airmass > 1.5" % int(min(moonseps))
		plt.annotate(msg, xy=(1.0, -1.5), ha="right",  xycoords='axes fraction', fontsize=14, color=color)

	plt.axis([min(xticks), max(xticks), 0.0, 1.0])
	ax.get_yaxis().set_visible(False)
	plt.xlabel('UT', fontsize=18)

	plt.suptitle(observable.name+" ("+starttime.split(" ")[1][:5]+" --> "+stoptime.split(" ")[1][:5]+")", fontsize=25, y=0.93)

	if savefig:
		assert dirpath != None
		if not os.path.isdir(os.path.join(dirpath, obs_night)):
			os.mkdir(os.path.join(dirpath, obs_night))
		path = os.path.join(dirpath, obs_night, observable.name+'.png')
		plt.savefig(path)
		print(("Plot saved on %s" % path))
	else:
		plt.show()
		
		
def plot_target_on_sky(target, figure=None, northisup=True, eastisright=False, boxsize=None, survey='DSS'):
	"""
	Uses astroquery (hopefully soon accessible from `astropy.vo`) to plot an image of the target
	"""
	
	from astroquery.skyview import SkyView
	from astropy.coordinates import SkyCoord
	
	
	skycoord = SkyCoord(target.alpha, target.delta)
	position = skycoord.icrs
	
	if boxsize is None: 
		boxsize = 10.*u.arcmin
	else: 
		boxsize *= 1.*u.arcmin

	hdu = SkyView.get_images(position=position, coordinates='icrs', survey=survey, radius=boxsize, grid=True)[0][0]
	wcs = WCS(hdu.header)
	
	if figure is None:
		ax = plt.gca(projection=wcs)
	else:
		ax = figure.gca(projection=wcs)
		
	image_data = hdu.data
	ax.imshow(image_data, cmap=plt.get_cmap("Greys"))
	
	
	imgsize = image_data.shape[0]
	inner_boundary = 0.02
	outer_boundary = 0.08

	lwr = 1.5
	cr = 'firebrick'
	alphar = 0.5

	ax.axvline(x=0.5*imgsize, ymin=0.5+inner_boundary, ymax=0.5+outer_boundary, lw=lwr, c=cr, alpha=alphar)
	ax.axhline(y=0.5*imgsize, xmin=0.5+inner_boundary, xmax=0.5+outer_boundary, lw=lwr, c=cr, alpha=alphar)
	
	arrowkwargs = {'width':0.5, 'headwidth':4, 'shrink':0.05, 'facecolor':cr, 'color':cr, 'alpha':alphar}
	
	if northisup:
		ax.invert_yaxis()
		ax.annotate('', xy=(0.85, 0.25), xytext=(0.85, 0.05), xycoords="axes fraction", textcoords="axes fraction",
            arrowprops=arrowkwargs,
            )
		ax.annotate('N', xy=(0.835, 0.255), xycoords="axes fraction", color=cr)
	else:
		ax.annotate('', xy=(0.85, 0.05), xytext=(0.85, 0.25), xycoords="axes fraction", textcoords="axes fraction",
            arrowprops=arrowkwargs,
            )
		ax.annotate('N', xy=(0.833, 0.02), xycoords="axes fraction", color=cr)
		
	if eastisright:
		ax.invert_xaxis()
		ax.annotate('', xy=(0.95, 0.15), xytext=(0.75, 0.15), xycoords="axes fraction", textcoords="axes fraction",
            arrowprops=arrowkwargs,
            )
		ax.annotate('E', xy=(0.95, 0.137), xycoords="axes fraction", color=cr)
	else:
		ax.annotate('', xy=(0.75, 0.15), xytext=(0.95, 0.15), xycoords="axes fraction", textcoords="axes fraction",
            arrowprops=arrowkwargs,
            )
		ax.annotate('E', xy=(0.72, 0.137), xycoords="axes fraction", color=cr)
	
	# Redraw the figure for interactive sessions.
	ax.figure.canvas.draw()
	
	
	return ax



if __name__ == "__main__":

	print("Welcome to demo mode")

	import meteo as meteomodule
	import obs

	currentmeteo = meteomodule.Meteo(name="LaSilla", cloudscheck=False, debugmode=True)
	currentmeteo.time = Time("2018-02-15 07:00:00.0")
	target = obs.Observable(name="2M1134-2103", obsprogram="lens",alpha="11:34:40.5", delta="-21:03:23")
	#target = obs.Observable(name="HE0435-1223", obsprogram="lens",alpha="04:38:14.9", delta="-12:17:14.4")
	
	plot_target_on_sky(target=target)
	plt.show()
	exit()

	plot_airmass_on_sky(target=target, meteo=currentmeteo)
	shownightobs(target, currentmeteo)

	plt.show()


