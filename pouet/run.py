"""
High-level functions around meteo and obs
Running the script should provide a minimal text output
"""

import os, sys, inspect
from astropy.time import Time
import obs, meteo, plots, util
import importlib
import logging

global SETTINGS
herepath = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
SETTINGS = util.readconfig(os.path.join(herepath, "config/settings.cfg"))

logger = logging.getLogger(__name__)

def startup(name='LaSilla', cloudscheck=True, debugmode=False):
    """
    Initialize meteo
    :return: Meteo object
    """
    logger.debug("Loading a new meteo...")
    currentmeteo = meteo.Meteo(name=name, cloudscheck=cloudscheck, debugmode=debugmode)

    return currentmeteo


def refresh_status(meteo, observables=None, minimal=False, obs_time=None):
    """
    Refresh the status

    :param observables:
    :param obs_time:
    :return:
    """
    logger.debug("Refreshing the observables status...")
    # update meteo
    if obs_time == None:
        obs_time = meteo.time

    meteo.update(obs_time, minimal=minimal)

    if observables:
        #todo: does using a tuple instead of a list speed up the update process? we should find out !!
        [obs.update(meteo) for obs in observables if obs.hidden == False]


def retrieve_obsprogramlist():
    """
    Return a list of existing obsprogram in the obsprogram folder, minus the default obsprogram
    :return: list of exising obsprogram, minus the default one.

    .. warning:: path to obsprogram folder is hardcoded. This is wrong and should be changed!
    """
    logger.debug("Revrieving obsprograms...")
    obsprogramlist = []
    #todo: obsprogram path is hardcoded, this is wrong!
    files = [f for f in os.listdir(os.path.join(herepath,'obsprogram')) if 'prog' in f and '.py'in f and not 'pyc' in f and not "default" in f]
    for f in files:
        name = f.split('prog')[1].split('.py')[0]
        program = importlib.import_module("obsprogram.prog{}".format(name), package=None)
        obsprogramlist.append({"name": name, "program": program})

    return obsprogramlist


def hide_observables(observables, criteria):
    """
    Hide the observables not matching the given criteria

    :param observables: list of :meth:`~obs.Observable`
    :param criteria: list of dictionnaries. Each dict contains an "id" and associated keywords used for the hiding. See :meth:'~main.hide_observables'.

    """
    logger.debug("Hiding observables...")
    for c in criteria:
        for o in observables:
            if c["id"] == "matchname":
                if c["pattern"].strip() not in o.name:
                    o.hidden = True
            elif c["id"] == "airmass":
                if  o.airmass > c["max"]:
                    o.hidden = True
            elif c["id"] == "moondist":
                if o.angletomoon.degree < c["min"]:
                    o.hidden = True
            elif c["id"] == "sundist":
                if o.angletosun.degree < c["min"]:
                    o.hidden = True
            elif c["id"] == "windangle":
                if o.angletowind.degree < c["min"]:
                    o.hidden = True
            elif c["id"] == "observability":
                if o.observability <= c["min"]:
                    o.hidden = True
            elif c["id"] == "clouds":
                if o.cloudfree is not None and o.cloudfree <= c["min"]:
                    o.hidden = True
                elif o.cloudfree is None:
                    o.hidden = True

            elif c["id"] == "alphaboth":
                if o.alpha.to_string(sep=":", pad=True) <= c["min"] or o.alpha.to_string(sep=":", pad=True) >= c["max"]:
                    o.hidden = True
            elif c["id"] == "alphamin":
                if o.alpha.to_string(sep=":", pad=True) <= c["min"]:
                    o.hidden = True
            elif c["id"] == "alphamax":
                if o.alpha.to_string(sep=":", pad=True) >= c["max"]:
                    o.hidden = True

            elif c["id"] == "deltaboth":

                delta = o.delta.to_string(sep=":", pad=True).split(".")[0]

                # we start with the easy cases where max < min
                if len(c["max"]) > len(c["min"]):
                    o.hidden = True
                elif len(c["max"]) == 8 and len(c["min"]) == 8 and c["min"] > c["max"]:
                    o.hidden = True
                elif len(c["max"]) == 9 and len(c["min"]) == 9 and c["min"] < c["max"]:
                    o.hidden = True

                elif len(delta) == 8:  # then obs is positive
                    if len(c["min"]) == 8 and len(c["max"]) == 8:
                        # all positive, standard comparison
                        if delta <= c["min"] or delta >= c["max"]:
                            o.hidden = True
                    elif len(c["max"]) == 8 and len(c["min"]) == 9:
                        #  obs is positive, min is negative --> ignore it
                        if delta >= c["max"]:
                            o.hidden = True
                    elif len(c["max"]) == 9 and len(c["min"]) == 9:
                        # obs is positive, constraint are negative --> hide obs
                        o.hidden = True

                elif len(delta) == 9:  # then obs is negative
                    if len(c["min"]) == 8 and len(c["max"]) == 8:
                        # obs negative, constraint positive --> hide obs
                        o.hidden = True
                    elif len(c["min"]) == 9 and len(c["max"]) == 8:
                        # max constrain is positive, ignore it
                        if delta >= c["min"]:
                            o.hidden = True
                    elif len(c["max"]) == 9 and len(c["min"]) == 9:
                        # all negative, inverted comparison:
                        if delta <= c["max"] or delta >= c["min"]:
                            o.hidden = True

            elif c["id"] == "deltamin":
                delta = o.delta.to_string(sep=":", pad=True).split(".")[0]

                if len(delta) == 8:  # then obs is positive
                    if len(c["min"]) == 8:
                        # all positive, standard comparison
                        if o.delta.to_string(sep=":", pad=True) <= c["min"]:
                            o.hidden = True
                    elif len(c["min"]) == 9:
                        # constrain negative, ignore it
                        pass

                elif len(delta) == 9:  # then obs is negative
                    if len(c["min"]) == 8:
                        # cmin bigger than obs, hide it
                        o.hidden = True
                    elif len(c["min"]) == 9:
                        # both negative, inverse comparison
                        if o.delta.to_string(sep=":", pad=True) >= c["min"]:
                            o.hidden = True

            elif c["id"] == "deltamax":
                delta = o.delta.to_string(sep=":", pad=True).split(".")[0]

                if len(delta) == 8:  # then obs is positive
                    if len(c["max"]) == 8:
                        # all positive, standard comparison
                        if o.delta.to_string(sep=":", pad=True) >= c["max"]:
                            o.hidden = True
                    elif len(c["max"]) == 9:
                        # cmax smaller than obs, hide it
                        o.hidden = True

                elif len(delta) == 9:  # then obs is negative
                    if len(c["max"]) == 8:
                        # cmax bigger than obs, ignore it
                        pass
                    elif len(c["max"]) == 9:
                        # both negative, inverse comparison
                        if o.delta.to_string(sep=":", pad=True) <= c["max"]:
                            o.hidden = True

            else:
                pass
    logger.info("Observables hidden.")


"""
if __name__ == "__main__":

    logging.basicConfig(format='PID %(process)06d | %(asctime)s | %(levelname)s: %(name)s(%(funcName)s): %(message)s', level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    logger.critical("This should say Python >= 3.0: {}".format(sys.version))

    # initialize meteo
    currentmeteo = meteo.Meteo(name='LaSilla', cloudscheck=False, debugmode=False)

    # load a catalogue of observables
    observables = obs.rdbimport("../cats/2m2lenses.rdb", obsprogramcol=None, obsprogram='lens')

    #sys.exit()
    obs_night = Time("2018-02-12 01:00:00", format='iso', scale='utc')
    #plots.shownightobs(observable=observables[0], meteo=currentmeteo, obs_night="2018-02-12", savefig=False, verbose=True)

    # show current status of all observables
    obs.showstatus(observables, currentmeteo, displayall=True)

    # update meteo at now
    currentmeteo.update(obs_time=Time.now())

    # newtime
    # todo create a new time object, play with it
"""