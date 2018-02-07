"""
Initialize a new session
"""

import sys
from astropy.time import Time

import obs, meteo

import logging 
logging.basicConfig(format='PID %(process)06d | %(asctime)s | %(levelname)s: %(name)s(%(funcName)s): %(message)s',level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.critical("This should say Python >= 3.0: {}".format(sys.version))

# initialize meteo
currentmeteo = meteo.Meteo(name='LaSilla', cloudscheck=True, debugmode=False)

# load a catalogue of observables
observables = obs.rdbimport("2m2lenses.rdb", obsprogram='lens')

# show current status of all observables
obs.showstatus(observables, currentmeteo, displayall=False)

# update meteo at now
currentmeteo.update(obs_time=Time.now())

def refresh_status(observables, meteo, obs_time=Time.now()):
    """
    TBW

    :param observables:
    :param obs_time:
    :return:
    """

    # update meteo
    meteo.update(obs_time, minimal=True if obs_time !=Time.now() else False)
    return [obs.update(meteo, obs_time) for obs in observables]



# newtime
#todo create a new time object, play with it
