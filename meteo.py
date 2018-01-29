"""
Define the METEO class and related functions

Meteo is an object containing all the external weather condition (wind speed and direction, temperature, moon position, clouds pattern,...)
It is the only object that interact outside POUET, i.e. communicate with website to get the meteo,...

Observables interact only with Meteo to get their constaints (position to the moon, angle to wind, ...)

!!! DO NOT CALL THIS site.py OTHERWISE IT CLASHES WITH SOME WEIRD SYSTEM PACKAGE!!!!
"""

import astropy.coordinates.angles as angles
from astropy.time import Time
import urllib.request, urllib.error, urllib.parse
import re
import ephem
import numpy as np
import os 

import util
import clouds

import logging
logger = logging.getLogger(__name__)

class Meteo:
    """
    Class to hold the meteorological conditions of the current night and the location of the site

    Typically, a Site object is created when POUET starts, and then update itself every XX minutes
    """

    def __init__(self, name='uknsite', date=None, moonaltitude=None, moonazimuth=None, sunaltitude=None, sunazimuth=None,
            winddirection=None, windspeed=None, cloudscheck=True, fimage=None, debugmode=False):

        self.name = name
        self.location = util.readconfig(os.path.join("config", "{}.cfg".format(name)))
        
        self.date = date
        self.moonalt = moonaltitude
        self.moonaz = moonazimuth
        self.sunalt = sunaltitude
        self.sunaz = sunazimuth
        self.winddirection = winddirection
        self.windspeed = windspeed        
        
        self.cloudscheck = cloudscheck
        self.cloudmap = None
        if cloudscheck:
            self.allsky = clouds.Clouds(location=name, fimage=fimage, debugmode=debugmode)

        self.update()
        

    def updatedate(self):
        pass

    def updatemoonpos(self, obs_time=Time.now()):
        Az, Alt = self.get_moon(obs_time=obs_time)
        self.moonalt = Alt
        self.moonaz = Az

    def updatesunpos(self, obs_time=Time.now()):
        Az, Alt = self.get_sun(obs_time=obs_time)
        self.sunalt = Alt
        self.sunaz = Az

    def updatewind(self):
        WD, WS = self.get_wind()
        self.winddirection = WD
        self.windspeed = WS
        
    def updateclouds(self):
        """
        Excecutes the clouds code, if map not available, saves None to cloudmap
        """
    
        try:
            self.allsky.update()
            self.cloudmap = self.allsky.observability_map
        except:
            logger.warning("Could not retrive cloud map")
            self.cloudmap = None
        

    def update(self, obs_time=Time.now(), minimal=False):
        """
        minimal=True update only the moon and sun position. Useful for predictions (as you can't predict the clouds or winds, no need to refresh them)
        """
        self.updatedate()
        self.updatemoonpos(obs_time=obs_time)
        self.updatesunpos(obs_time=obs_time)
        if not minimal:
            self.updatewind()
            if self.cloudscheck:
                self.updateclouds()
            

    def __str__(self, obs_time=Time.now()):
        # not very elegant

        msg = "="*30+"\nName:\t\t%s\nDate:\t%s\n" %(self.name, self.date)

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

    def get_wind(self):
    
        #todo: add a "no connection" message if page is not reachable instead of an error
        WS=[]
        WD=[]
        try:
            data=urllib.request.urlopen(self.location.get("weather", "url")).read()
        except urllib.error.URLError:
            logger.warning("Cannot download weather data. Either you or the weather server is offline!")
            return np.nan, np.nan
        data = data.decode("utf-8")
        data=data.split("\n") # then split it into lines
        for line in data:
            if re.match( r'WD', line, re.M|re.I):
                WD.append(int(line[20:25])) # AVG
            if re.match( r'WS', line, re.M|re.I):
                WS.append(float(line[20:25])) # AVG
    
        # Remove out-of-band readings
        # WD is chosen between station 1 or 2 in EDP pour la Silla.
        # We take average
        WD = np.asarray(WD, dtype=np.float)
        WD = WD[WD < 360]
        WD = WD[WD > 0]
        WD = np.mean(WD)
        
        # WS should be either WS next to 3.6m or max
        # Remove WS > 99 m/s
        WS = np.asarray(WS, dtype=np.float)
        if WS[2] < 99:
            WS = WS[2]
        else:
            logger.warning("WARNING: Wind speed from 3.6m unavailable, using other readings in LaSilla")
            WS = np.asarray(WS, dtype=np.float)
            WS = WS[WS > 0]
            WS = WS[WS < 99]
            WS = np.mean(WS)
            
        return WD, WS
    
    
    def get_moon(self, obs_time=Time.now()):
    
        lat, lon, elev = self.get_telescope_params()
    
        observer = ephem.Observer()
        observer.date = obs_time.iso
        observer.lat, observer.lon, observer.elevation = lat.degree, lon.degree, elev
    
        moon = ephem.Moon()
        moon.compute(observer)
    
        # Warning, ass-coding here: output of moon.ra is different from moon.ra.__str__()... clap clap clap
        alpha = angles.Angle(moon.ra.__str__(), unit="hour")
        delta = angles.Angle(moon.dec.__str__(), unit="degree")
    
        # return Az, Alt as Angle object
        return self.get_AzAlt(alpha, delta, obs_time)
    
    
    def get_sun(self, obs_time=Time.now()):
    
        lat, lon, elev = self.get_telescope_params()
    
        observer = ephem.Observer()
        observer.date = obs_time.iso
        observer.lat, observer.lon, observer.elevation = lat.degree, lon.degree, elev
    
        sun = ephem.Sun()
    
        sun.compute(observer)
    
        # Warning, ass-coding here: output of sun.ra is different from sun.ra.__str__()... clap clap clap - again
        alpha = angles.Angle(sun.ra.__str__(), unit="hour")
        delta = angles.Angle(sun.dec.__str__(), unit="degree")
    
        # return Az, Alt as Angle object
        return self.get_AzAlt(alpha, delta, obs_time)
    
    def get_AzAlt(self, alpha, delta, obs_time=Time.now(), ref_dir=0):
    
        """
        idea from http://aa.usno.navy.mil/faq/docs/Alt_Az.php
    
        Compute the azimuth and altitude of a source at a given time (by default current time of 
        execution), given its alpha and delta coordinates.
    
        """
    
        lat, lon, elev = self.get_telescope_params()
    
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
        lat=angles.Angle(self.location.get("location", "latitude"))
        lon=angles.Angle(self.location.get("location", "longitude"))
        elev = float(self.location.get("location", "elevation"))
        
        return lat, lon, elev
    

    def get_nighthours(self, obs_night):
        """
        return a list of astropy Time objects, corresponding to the different hours of the obs_night
        """
    
        lat, lon, elev = self.get_telescope_params()
    
        obs_time = Time('%s 05:00:00' % obs_night, format='iso', scale='utc') #5h UT is approx. the middle of the night
    
        obs_time = Time(obs_time.mjd + 1, format='mjd', scale='utc') # That corresponds to the next middle of the observing night
    
        observer = ephem.Observer()
        observer.pressure=0
        observer.date = obs_time.iso
        observer.lat, observer.lon, observer.elevation = str(lat.degree), str(lon.degree), elev
    
        observer.horizon = '-12'
    
        sun = ephem.Sun()
    
        # these fuckers are in YYYY/M(M)/D(D) HH:MM:SS format... 'murica !
        sunset = observer.previous_setting(sun).tuple()
        sunrise = observer.next_rising(sun).tuple()
    
        sunset_time = Time('%i-%02i-%02i %i:%i:%.03f' % sunset, format='iso', scale='utc').mjd
        sunrise_time = Time('%i-%02i-%02i %i:%i:%.03f' % sunrise, format='iso', scale='utc').mjd
    
        mjds = np.linspace(sunset_time, sunrise_time, num=100)
        times = [Time(mjd, format='mjd', scale='utc') for mjd in mjds]
    
        return times


#todo: generalize get_sun and get_moon into a single get_distance_to_obj function.
