"""
High-level functions around meteo and obs
Running the script should provide a minimal text output
"""

import os, sys
from astropy.time import Time
import obs, meteo, plots
import importlib

import logging
logger = logging.getLogger(__name__)

def startup(name='LaSilla', cloudscheck=True, debugmode=False):
    """
	Initialize meteo

    :return:
    """

    currentmeteo = meteo.Meteo(name=name, cloudscheck=cloudscheck, debugmode=debugmode)

    return currentmeteo


def refresh_status(meteo, observables=None, minimal=False, obs_time=None):
    """
    Refresh the status

    :param observables:
    :param obs_time:
    :return:
    """

    # update meteo
    if obs_time == None:
        obs_time = meteo.time

    meteo.update(obs_time, minimal=minimal)

    if observables:
        [obs.update(meteo) for obs in observables]


def retrieve_obsprogramlist():
    obsprogramlist = []
    files = [f for f in os.listdir('obsprogram') if 'prog' in f and not 'pyc' in f]
    for f in files:
        name = f.split('prog')[1].split('.py')[0]
        program = importlib.import_module("obsprogram.prog{}".format(name), package=None)
        obsprogramlist.append({"name": name, "program": program})

    return obsprogramlist




if __name__ == "__main__":


    import logging

    logging.basicConfig(format='PID %(process)06d | %(asctime)s | %(levelname)s: %(name)s(%(funcName)s): %(message)s',
                        level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    logger.critical("This should say Python >= 3.0: {}".format(sys.version))

    # initialize meteo
    currentmeteo = meteo.Meteo(name='LaSilla', cloudscheck=False, debugmode=False)

    # load a catalogue of observables
    observables = obs.rdbimport("../cats/2m2lenses.rdb", obsprogramcol=None, obsprogram='lens')

    observables = [o for o in observables if o.name == "PSJ1606-2333"]

    obs_night = Time("2018-02-12 01:00:00", format='iso', scale='utc')
    #plots.shownightobs(observable=observables[0], meteo=currentmeteo, obs_night="2018-02-12", savefig=False, verbose=True)


    # show current status of all observables
    obs.showstatus(observables, currentmeteo, displayall=True)

    # update meteo at now
    currentmeteo.update(obs_time=Time.now())

    # newtime
    # todo create a new time object, play with it
