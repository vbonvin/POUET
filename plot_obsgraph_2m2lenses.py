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
observables = [o for o in observables if o.name in ["HE0047-1756", "DES2038-4008", "WFI2033-4723"]]

# Set exptime manually
for o in observables:
	o.exptime = 30.0*60.0


# Set the nights for which you want to plot
startnight = "2017-10-01 01:00:00"
endnight = "2017-12-01 01:00:00"

starttime = Time(startnight, format='iso', scale='utc').mjd
endtime = Time(endnight, format='iso', scale='utc').mjd

days = np.arange(starttime, endtime, 1)
obs_nights = [Time(d, format='mjd', scale='utc').iso[:10] for d in days]


# And make the plots
for obs_night in obs_nights:
	print "="*30
	print obs_night

	for observable in observables:
		obs.shownightobs(observable=observable, meteo=currentmeteo, obs_night=obs_night, savefig=True, dirpath="/home/vivien/work/2m2_planning/observability", verbose=False)
