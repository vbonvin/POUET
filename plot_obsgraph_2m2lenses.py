"""
Piece of code around pouet function to plot observability plots for selected lenses from the 2m2 catalog.

Could in theory be used for any catalog that has objects with coordinates
"""
import numpy as np
import obs, meteo
import util
import sys, os
from astropy.time import Time


# Load test meteo, will be used for predictions in obs.shownightobs()
currentmeteo = util.readpickle("meteotest.pkl")

# Load observables
observables = obs.rdbimport("2m2lenses.rdb", obsprogram='lens')
observables = [o for o in observables if o.name == "2M1134-2103"]

#["HE0047-1756", "2M1134-2103", "WFI2033-4723", "J0832+0404", "J1226-0006", "PSJ1606-2333"]]

# Set exptime manually
for o in observables:
	o.exptime = 30.0*60.0


# Set the nights for which you want to plot
startnight = "2017-12-06 01:00:00"
endnight = "2018-03-31 01:00:00"

starttime = Time(startnight, format='iso', scale='utc').mjd
endtime = Time(endnight, format='iso', scale='utc').mjd

days = np.arange(starttime, endtime, 1)
obs_nights = [Time(d, format='mjd', scale='utc').iso[:10] for d in days]

# And make the plots
refairmasses = [o.maxairmass for o in observables]
for obs_night in obs_nights:
	print "="*30
	print obs_night

	# loose airmass constraints for early december for 3 objects !!
	if (obs_night >= "2017-11-28" and obs_night <"2017-12-20"):
		for o in [o for o in observables if o.name in ("2M1134-2103", "WFI2033-4723")]:
			o.maxairmass = 1.5


	for observable in observables:
		obs.shownightobs(observable=observable, meteo=currentmeteo, obs_night=obs_night, savefig=True, dirpath="/home/vivien/work/2m2_planning/observability", verbose=False)

	# reset the airmass to original reference
	for o, ram in zip(observables, refairmasses):
		o.maxairmass = ram

		#obs.shownightobs(observable=observable, meteo=currentmeteo, obs_night=obs_night, savefig=False, dirpath="/home/vivien/work/2m2_planning/observability", verbose=False)


