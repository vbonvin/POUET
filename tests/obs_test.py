"""
Testing script, v1
"""

import os, sys, logging, threading, time, runpy
from astropy.time import Time


path = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), '../pouet')
sys.path.append(path)


import clouds, main, meteo, obs, plots, run, util


logging.basicConfig(format='PID %(process)06d | %(asctime)s | %(levelname)s: %(name)s(%(funcName)s): %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.critical("This should say Python >= 3.0: {}".format(sys.version))
logger.info("I am in : ", os.getcwd())


# initialize meteo
currentmeteo = meteo.Meteo(name='LaSilla', cloudscheck=True, debugmode=True)
print(currentmeteo)
currentmeteo.get_nighthours(obs_night="2020-10-20", twilight="nautical")


# load a catalogue of observables
observables = obs.rdbimport(os.path.join(path, "../cats/2m2lenses_withobsprogram.pouet"), obsprogramcol=4, obsprogram='lens')
#observables = [o for o in observables if o.name == "PSJ1606-2333"]
for o in observables:
    print(o)

# show current status of all observables
obs.showstatus(observables, currentmeteo, displayall=True)
for o in observables:
    print(o)
    o.is_cloudfree(currentmeteo)
# update meteo at now
currentmeteo.update(obs_time=Time.now())

# newtime
# todo create a new time object, play with it



"""

#plots.shownightobs(observable=observables[0], meteo=currentmeteo, obs_night="2018-02-12", savefig=False, verbose=True)


# test graphical interface
SETTINGS = util.readconfig(os.path.join("pouet/config/settings.cfg"))
asfreq = float(SETTINGS['validity']['allskyfrequency']) * 60.0
wrfreq = float(SETTINGS['validity']['weatherreportfrequency'])

exectime = max(asfreq, wrfreq)*1.8
exectime_short = exectime/10.

try:
    t = threading.Thread(target=main.main)
    t.daemon = True
    t.start()
    time.sleep(exectime_short)
    t._stop()
except:
    pass
"""

