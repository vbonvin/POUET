import requests
import numpy as np
import re
import os
import sys, inspect

sys.path.insert(0, '../pouet')
import util

import logging
logger = logging.getLogger(__name__)

class WeatherReport():
    """
    This class is dedicated to recovering the weather report at the La Silla site and feeding the
    wind direction, wind speed, temperature and humidity back to pouet.
    It must contain at least a `get` method that returns the above variable.
    """
    
    def __init__(self, name='LaSilla'):
        """
        Class constructor. Loads the LaSilla.cfg configuration file and saves it as attribute.
        
        :param name: name of the cfg file, only included for completeness.
        """

        self.config = util.readconfig(os.path.join(os.path.join(os.path.dirname(os.path.abspath(inspect.stack()[0][1])), "{}.cfg".format(name))))
        
    def get(self, debugmode, FLAG = -9999):
        """
        Get method that reads the weather reports off the web. In the LaSilla case, it download a `meteo.last` and interprets the data.
        
        :param debugmode: whether or not POUET is in debugmode. If true, it ought to return some static and dummy data
        :param FLAG: what to return in case the weather report cannot be downloaded or treated. Currently, POUET expect -9999 as a placeholder.
    
        :return: Wind direction, speed, temperature and humidity
        
        .. warning:: Such a method *must* return the following variables in that precise order: wind direction, wind speed, temperature and humidity
        
        """
        #todo: add a "no connection" message if page is not reachable instead of an error
        WS=[]
        WD=[]
        RH = None
        Temps = []
        
        error_msg = "Cannot download weather data. Either you or the weather server is offline!"
        
        if debugmode:
            fname = "config/meteoDebugMode.last"
            fi = open(fname, mode='r')
            data = ""
            with fi:
                line = fi.read()
                data += line
        else:
            try:
                #data=urllib.request.urlopen(self.location.get("weather", "url")).read()
                data = requests.get(self.config.get("weather", "url")).content
            except requests.ConnectionError:
                logger.warning(error_msg)
                return FLAG, FLAG, FLAG, FLAG
            
            data = data.decode("utf-8")
            if "404 Not Found" in data:
                logger.warning(error_msg)
                return FLAG, FLAG, FLAG, FLAG
            
        data=data.split("\n") # then split it into lines
        for line in data:
            if re.match( r'WD', line, re.M|re.I):
                WD.append(int(line[20:25])) # AVG
            if re.match( r'WS', line, re.M|re.I):
                WS.append(float(line[20:25])) # AVG
            if re.match( r'RH', line, re.M|re.I):
                RH = float(line[20:25]) # AVG
            if re.match( r'T ', line, re.M|re.I):
                Temps.append(float(line[20:25])) # AVG
    
        # Remove out-of-band readings
        # WD is chosen between station 1 or 2 in EDP pour la Silla.
        # We take average
        Temps = np.asarray(Temps, dtype=np.float)
        Temps = Temps[Temps < 100]
        Temps = np.mean(Temps)
    
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
            logger.warning("Wind speed from 3.6m unavailable, using other readings in LaSilla")
            WS = np.asarray(WS, dtype=np.float)
            WS = WS[WS > 0]
            WS = WS[WS < 99]
            WS = np.mean(WS)
    
        for var in [WD, WS, Temps, RH]:
            if not np.isnan(var):
                var = -9999
        
        WD = util.check_value(WD, FLAG)
        WS = util.check_value(WS, FLAG)
        Temps = util.check_value(Temps, FLAG)
        RH = util.check_value(RH, FLAG)
        
        return WD, WS, Temps, RH
    
class AllSky():
    """
    Station-specific class that handles the all sky image and its transformation of the sky.
    """
    
    def __init__(self):
        """
        Class constructor that saves some important all sky parameters as a class attribute.
        """
        cx = 279
        cy = 230
        prefered_direction = {'dir':194.3, 'posx':297, 'posy':336}
        prefered_theta = np.arctan2(prefered_direction['posy']-cy, prefered_direction['posx']-cx)
        
        self.params = {'k1': 1.96263549291*0.945,
                'k2': 0.6,
                'ff': 1.,
                'r0': 330,
                'cx': cx,
                'cy': cy,
                'prefered_direction':prefered_direction,
                'prefered_theta': prefered_theta,
                'deltatetha': 180-prefered_direction['dir']+5,
                'north': prefered_theta + np.deg2rad(prefered_direction['dir']),
                'url': "http://allsky-dk154.asu.cas.cz/raw/AllSkyCurrentImage.JPG",
                'image_x_size':640,
                'image_y_size':480,
                }
        
    def get_radius(self, elev):
        """
        Method that computes the radius of a given elevation on the sky, in pixel.
        
        :param elev: elevation (in radians) 
        
        :return: Radius, in px
        """
        return self.params["ff"] * self.params["k1"] * np.tan(self.params["k2"] * elev / 2.) * self.params["r0"]
    
    def get_image_coordinates(self, az, elev):
        """
        Converts the azimuth and elevation of a target in pixel coordinates
        
        :param az: azimuth (in rad)
        :param elev: elevation (in rad)
        
        :return: x and y position 
        """
        
        north = self.params['north']
        cx = self.params['cx']
        cy = self.params['cy']
    
        az *= -1.
        elev = np.pi/2. - elev
        
        rr = self.get_radius(elev)
        
        x = np.cos(north + az) * (rr - 2) + cx 
        y = np.sin(north + az) * (rr - 2) + cy
        
        if x < 0 or y < 0: 
            x = np.nan
            y = np.nan 
    
        return x, y
    
    def get_mask(self, ar):
        """
        Returns the mask to apply on the AllSky hide unwanted features in the image.
        In the LaSilla case, to remove the danish and the text in the corners.
        
        :param ar: original image (or at least an array with the same size). Used to get the image size.
        """
        s=np.shape(ar)
        #xxa, xxb = s[0]/2, s[1]/2
        #r = 210#285
        #xxb = 279
        #xxa = 230
        
        #    y,x = np.ogrid[-xxa:s[0]-xxa, -xxb:s[1]-xxb]
        xxa, xxb = s[0]/2, s[1]/2
        r = 285
        y,x = np.ogrid[-xxa:s[0]-xxa, -xxb:s[1]-xxb]
        
        adan, bdan = 145, 570
        rdan = 88
        ydan,xdan = np.ogrid[-adan:s[0]-adan, -bdan:s[1]-bdan]
    
        mask = np.logical_or(x*x + y*y >= r*r, xdan*xdan + ydan*ydan <= rdan*rdan)
        
        return mask

    