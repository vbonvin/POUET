"""
Define the METEO class and related functions

Meteo is an object containing all the external weather condition (wind speed and direction, temperature, moon position, clouds pattern,...)
It is the only object that interact outside POUET, i.e. communicate with website to get the meteo,...

Observables interact only with Meteo to get their constaints (position to the moon, angle to wind, ...)

.. warning:: Do *NOT* call this `site.py` otherwise it clashes with some weird Python system package.
"""

import astropy.coordinates.angles as angles
from astropy.time import Time
from datetime import datetime, timedelta
#todo: using requests instead of urllib, that has versioning issues ?
#import urllib.request, urllib.error, urllib.parse
import ephem
import numpy as np
import os, sys, inspect


import util, clouds

import logging
logger = logging.getLogger(__name__)


#todo: there are a lot of obs_time=Time.now() still in the code, it should be cleared from these!

class Meteo:
    """
    Class to hold the meteorological conditions of the current night and the location of the site

    Typically, a Meteo object is created when POUET starts, and then update itself every XX minutes
    """
    def __init__(self, name='uknsite', time=None, moonaltitude=None, moonazimuth=None, sunaltitude=None, sunazimuth=None, winddirection=-1, windspeed=-1, cloudscheck=True, fimage=None, debugmode=False):
        """
        :param name: string, name of the meteo object (typically the site where you are located, i.e. LaSilla. Must correspond to a .cfg file in :file:`config` that contains the location of the site. See :file:`config/LaSilla.cfg` for example.
        :param time: Astropy Time object. If None, use the current time as default
        :param moonaltitude: Astropy Angle object, altitude of the moon . If none, is computed using the site location when :meth:`~meteo.update` is called.
        :param moonazimuth: Astropy Angle object, azimuth of the moon . If none, is computed using the site location when :meth:`~meteo.update` is called.
        :param sunaltitude: Astropy Angle object, altitude of the Sun . If none, is computed using the site location when :meth:`~meteo.update` is called.
        :param sunazimuth: Astropy Angle object, azimuth of the Sun . If none, is computed using the site location when :meth:`~meteo.update` is called.
        :param winddirection: float, direction of the wind, in degree. If none, is computed using the site weather report when :meth:`~meteo.update` is called.
        :param windspeed: float, speed of the wind in m/s. If none, is computed using the site weather report when :meth:`~meteo.update` is called.
        :param cloudscheck: boolean. If True, uses :meth:`clouds.Clouds` to analyze an all-sky image and create a mapping of the clouds in the plane of the sky
        :param fimage: string, name of the filename of the all-sky image to analyse
        :param debugmode: boolean. If True, use dummy values for the wind and all-sky

        .. warning:: the moon and sun position, wind speed and angle default values provided at construction will be overwritten by :meth:`~meteo.update`

        """
        self.name = name
        self.location = util.readconfig(os.path.join(os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
, "config", "{}.cfg".format(name)))
        self.get_telescope_params()
        
        self.weatherReport = (util.load_station(name)).WeatherReport()

        self.time = time
        self.moonalt = moonaltitude
        self.moonaz = moonazimuth
        self.sunalt = sunaltitude
        self.sunaz = sunazimuth
        self.winddirection = winddirection
        self.windspeed = windspeed    
        self.temperature = 9999 
        self.humidity = -1
        self.lastest_weatherupdate_time = None
        self.debugmode = debugmode
        
        self.cloudscheck = cloudscheck
        self.cloudmap = None


        self.allsky = clouds.Clouds(name=name, fimage=fimage, debugmode=debugmode)

        self.update()

    def updatemoonpos(self, obs_time=Time.now()):
        """
        Updates the moon position in the sky with respect to the observer

        :param obs_time: Astropy Time object, time at which you want to compute the moon coordinates
        """
        logger.debug("Updating moon position...")
        Az, Alt = self.get_moon(obs_time=obs_time)
        self.moonalt = Alt
        self.moonaz = Az

    def updatesunpos(self, obs_time=Time.now()):
        """
        Updates the Sun position in the sky with respect to the observer

        :param obs_time: Astropy Time object, time at which you want to compute the Sun coordinates
        """
        logger.debug("Updating Sun position...")
        Az, Alt = self.get_sun(obs_time=obs_time)
        self.sunalt = Alt
        self.sunaz = Az

    def updateclouds(self):
        """
        Excecutes the clouds code in :meth:`~clouds.Clouds`, if map not available, saves None to cloudmap
        """
        logger.debug("Updating clouds coverage...")
        try:
            self.allsky.update()
            self.cloudmap = self.allsky.observability_map
        except:
            logger.warning("Could not retrieve cloud map")
            self.cloudmap = None

    def update(self, obs_time=Time.now(), minimal=False):
        """
        Update the time-dependent parameters: Sun and moon position, wind speed and direction, cloud coverage map. Wrapper around the :meth:`~meteo.updatemoonpos`, :meth:`~meteo.updatesunpos`, :meth:`~meteo.updateweather` and :meth:`~meteo.updateclouds`

        :param obs_time: Astropy Time object. If None, use the current time as default.
        :param minimal: boolean. If True, update only the moon and sun position. Useful for predictions where wind and cloud coverage cannot be estimated.
        """
        logger.debug("Starting meteo update...")
        self.time=obs_time
        self.updatemoonpos(obs_time=obs_time)
        self.updatesunpos(obs_time=obs_time)
        if not minimal:
            self.updateweather()
            if self.cloudscheck:
                self.updateclouds()

    def __str__(self, obs_time=Time.now()):
        # not very elegant
        msg = "="*30+"\nName:\t\t%s\nDate:\t%s\n" %(self.name, self.time)

        try:
            msg+= "Moon Altitude:\t%s\n"%self.moonalt.hour
        except AttributeError:
            msg+= "Moon Altitude:\tNone\n"

        try:  # let's behave like real people and use a correct iso system
            msg+= "Moon Azimuth:\t%s\n"%self.moonaz.degree
        except AttributeError:
            msg+= "Moon Azimuth:\tNone\n"

        try:
            msg+= "Sun Altitude:\t%s\n"%self.sunalt.hour
        except AttributeError:
            msg+= "Sun Altitude:\tNone\n"

        try:  # let's behave like real people and use a correct iso system
            msg+= "Sun Azimuth:\t%s\n"%self.sunaz.degree
        except AttributeError:
            msg+= "Sun Azimuth:\tNone\n"

        return msg

    def updateweather(self):
        """
        Updates the weather-related parameters from the site weather report.
        """
        logger.debug("Updating meteo from online weather report...")
        self.winddirection, self.windspeed, self.temperature, self.humidity = self.weatherReport.get(debugmode=self.debugmode)
        
        """
        self.winddirection = WD
        self.windspeed = WS
        self.temperature = Temps 
        self.humidity = RH
        """
        
        checkvals = np.array([self.winddirection, self.windspeed, self.temperature, self.humidity])
        li = np.where(checkvals == -9999)[0]
        
        if not len(li) == len(checkvals):
            self.lastest_weatherupdate_time = Time.now()
    
    def get_moon(self, obs_time=Time.now()):
        """
        Compute the altitude and azimuth of the moon at the given time

        :param obs_time:  Astropy Time object. If None, use the current time as default.
        :return: altitude and azimuth angles as Astropy Angle objects
        """
        logger.debug("Computing Moon coordinates...")
        observer = ephem.Observer()
        observer.date = obs_time.iso
        observer.lat, observer.lon, observer.elevation = self.lat.degree, self.lon.degree, self.elev
    
        self.moon = ephem.Moon()
        self.moon.compute(observer)
    
        # Warning, ass-coding here: output of moon.ra is different from moon.ra.__str__()... clap clap clap
        alpha = angles.Angle(self.moon.ra.__str__(), unit="hour")
        delta = angles.Angle(self.moon.dec.__str__(), unit="degree")
    
        # return Az, Alt as Angle object
        return self.get_AzAlt(alpha, delta, obs_time)
    
    
    def get_sun(self, obs_time=Time.now()):
        """
        Compute the altitude and azimuth of the moon at the given time

        :param obs_time:  Astropy Time object. If None, use the current time as default.
        :return: altitude and azimuth angles as Astropy Angle objects
        """
        logger.debug("Computing Sun coordinates...")
        observer = ephem.Observer()
        observer.date = obs_time.iso
        observer.lat, observer.lon, observer.elevation = self.lat.degree, self.lon.degree, self.elev
    
        self.sun = ephem.Sun()
        self.sun.compute(observer)
    
        # Warning, ass-coding here: output of sun.ra is different from sun.ra.__str__()... clap clap clap - again
        alpha = angles.Angle(self.sun.ra.__str__(), unit="hour")
        delta = angles.Angle(self.sun.dec.__str__(), unit="degree")
    
        # return Az, Alt as Angle object
        return self.get_AzAlt(alpha, delta, obs_time)
    
    def get_AzAlt(self, alpha, delta, obs_time=None, ref_dir=0):
    
        """
        #todo: can't we do it with astropy as well?
        idea from http://aa.usno.navy.mil/faq/docs/Alt_Az.php
    
        Compute the azimuth and altitude of a source at a given time (by default current time of execution), given its alpha and delta coordinates.

        :param alpha: Astrophy Angle object, right ascencion of the target you want to translate into altaz
        :param delta: Astrophy Angle object, declination of the target you want to translate into altaz
        :param obs_time: Astropy Time object. If None, use the current time as default.
        :param ref_dir: float, zero point of the azimuth. Default is 0, corresponding to North.
        :return: altitude and azimuth angles as Astropy Angle objects
        """
        if not obs_time:
            obs_time = self.time

        lat, lon, elev = self.lat, self.lon, self.elev
    
        # Untouched code from Azimuth.py
        D = obs_time.jd - 2451545.0
        GMST = 18.697374558 + 24.06570982441908*D
        epsilon= np.deg2rad(23.4393 - 0.0000004*D)
        eqeq= -0.000319*np.sin(np.deg2rad(125.04 - 0.052954*D)) - 0.000024*np.sin(2.*np.deg2rad(280.47 + 0.98565*D))*np.cos(epsilon)
        GAST = GMST + eqeq
        GAST -= np.floor(GAST/24.)*24.
    
        LHA = angles.Angle((GAST-alpha.hour)*15+lon.degree, unit="degree")
        if LHA > 0: LHA += angles.Angle(np.floor(LHA/360.)*360., unit="degree")
        else: LHA -= angles.Angle(np.floor(LHA/360.)*360., unit="degree")
    
        sina=np.cos(LHA.radian)*np.cos(delta.radian)*np.cos(lat.radian)+np.sin(delta.radian)*np.sin(lat.radian)
        Alt = angles.Angle(np.arcsin(sina),unit="radian")
    
        num = -np.sin(LHA.radian)
        den = np.tan(delta.radian)*np.cos(lat.radian)-np.sin(lat.radian)*np.cos(LHA.radian)
    
        Az = angles.Angle(np.arctan2(num,den), unit="radian")
        Az-=angles.Angle(ref_dir, unit="degree")
    
        # I changed this to get the same angle as the edp, using 0 (North) as reference
        if Az.degree < 0:
            Az+=angles.Angle(360, unit="degree")
    
        return Az, Alt
    
    def get_telescope_params(self):
        """
        Puts the latitude, longitude and elevation of the telescope from the config file into Astropy Angle objects

        :return: latitude, longitude and elevation of the telescope as Astropy Angle objects
        """
        logger.debug("Retrieving telescope parameters...")
        self.lat=angles.Angle(self.location.get("location", "latitude"))
        self.lon=angles.Angle(self.location.get("location", "longitude"))
        self.elev = float(self.location.get("location", "elevation"))
        
        return self.lat, self.lon, self.elev

    def get_nighthours(self, obs_night, twilight="nautical", nhours=100):
        """
        Computes a list of astropy Time objects, spanning to the different hours of the nights between twilights.

        :param obs_night: string formatted as YYYY-MM-DD. Night where the observations start.
        :param twilight: string, can be "civil", "nautical" or "astronomical", corresponding to Sun elevation of -6, -12 or -18 degree from the horizon, respectively.
        :param nhours: integer, number of hours you want in the list

        :return: list of Astropy Time objects, regularly spaced between twilights.

        """
        logger.debug("Determining night hours...")
        sunrise, sunset = self.get_twilights(obs_night, twilight)
        
        sunrise = sunrise.tuple()
        sunset = sunset.tuple()
    
        sunset_time = Time('%i-%02i-%02i %i:%i:%.03f' % sunset, format='iso', scale='utc').mjd
        sunrise_time = Time('%i-%02i-%02i %i:%i:%.03f' % sunrise, format='iso', scale='utc').mjd
    
        mjds = np.linspace(sunset_time, sunrise_time, num=nhours)
        times = [Time(mjd, format='mjd', scale='utc') for mjd in mjds]
    
        return times
    
    def get_twilights(self, obs_night, twilight="nautical"):
        """
        Computes the twilight times for a given night

        :param obs_night:  string formatted as YYYY-MM-DD. Night where the observations start.
        :param twilight: string, can be "civil", "nautical" or "astronomical", corresponding to Sun elevation of -6, -12 or -18 degree from the horizon, respectively.

        .. note:: The twilight times in PyEphem don't take into account the altitude ! See `https://github.com/brandon-rhodes/pyephem/issues/102`
        """
        logger.debug("Determining twilights times")
        lat, lon, elev = self.lat, self.lon, self.elev

        midnight = datetime.strptime('%s 23:59:59' % obs_night, "%Y-%m-%d %H:%M:%S")  # "UTC zero midnight"
        midnight = midnight - timedelta(hours=lon.hour)  # shift by longitude
    
        observer = ephem.Observer()
        observer.pressure = 0
        observer.date = midnight.strftime("%Y-%m-%d %H:%M:%S")
        observer.lat = str(lat.degree)
        observer.lon = str(lon.degree)
        observer.elevation = elev
        
        # TODO: could compensate the altitude by changing the horzion altitude, but seems hard from my current pt of view
        if twilight == "civil":
            observer.horizon = '-6.'
        elif twilight == "nautical":
            observer.horizon = '-12.'
        elif twilight == "astronomical":
            observer.horizon = '-18.'
        else:
            raise RuntimeError("Unknown twilight definition")
    
        sun = ephem.Sun()

        sunset = observer.previous_setting(sun)
        sunrise = observer.next_rising(sun)
    
        return sunrise, sunset

#todo: generalize get_sun and get_moon into a single get_distance_to_obj function.
