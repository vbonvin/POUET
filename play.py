"""
playground
"""

import numpy as np
import obs, meteo, util
import sys, os
from astropy.time import Time
from astropy import units as u
import ephem
from astropy.coordinates import angles, angle_utilities

#currentmeteo = meteo.Meteo(name='LaSilla')
#bebop = 'BEBOP_Observing_Targets.xlsx'
#superwasp = '1SuperWASPv5.xlsx'
#observables = util.excelimport(bebop, obsprogram='bebop')
#observables = util.excelimport(superwasp, obsprogram='superwasp')
#obs.showstatus(observables, currentmeteo, displayall=False)
#sys.exit()


# initialize meteo
currentmeteo = meteo.Meteo(name='LaSilla', check_clouds=False)

# util.writepickle(currentmeteo, 'meteotest.pkl')
# currentmeteo = util.readpickle("meteotest.pkl")
# load a catalogue of observables
observables = obs.rdbimport("2m2lenses.rdb", obsprogram='lens')
# select only a few of them:
observables = [o for o in observables if o.name in ["HE0047-1756", "WFI2033-4723"]]

# show current status
#obs.showstatus(observables, currentmeteo, displayall=True)


for observable in observables:
	observable.update(currentmeteo)
	print observable.angletosun.degree


'''
#Az, Alt = util.get_AzAlt(observable.alpha, observable.delta)
print 'Azimuth star:\t', Az.to_string(unit=u.degree)
print 'Elevation star:\t%s' % Alt.to_string(unit=u.degree)
'''




sys.exit()

#argv = ['-a', '04h38m14.90s', '-d', '-12d17m14.4s']
#Azimuth.main(argv)

print '====================='

Az, Alt = util.get_AzAlt('04h38m14.90s', '-12d17m14.4s')

#Az, Alt = util.get_AzAlt(test.alpha, test.delta)
#print 'Azimuth star:\t', Az.to_string(unit=u.degree)
#print 'Elevation star:\t%s' % Alt.to_string(unit=u.degree)

print 'Azimuth star:\t', Az
print 'Elevation star:\t%s' % Alt