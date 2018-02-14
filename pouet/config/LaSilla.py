import requests
import numpy as np
import re
import os
import sys 

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
        
        self.config = util.readconfig(os.path.join("config", "{}.cfg".format(name)))
        
    def get(self, debugmode, FLAG = -9999):
        #todo: add a "no connection" message if page is not reachable instead of an error
        WS=[]
        WD=[]
        RH = None
        Temps = []
        
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
                logger.warning("Cannot download weather data. Either you or the weather server is offline!")
                return FLAG, FLAG, FLAG, FLAG
            data = data.decode("utf-8")
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
    def __init__(self):
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
        return self.params["ff"] * self.params["k1"] * np.tan(self.params["k2"] * elev / 2.) * self.params["r0"]
    
    def get_image_coordinates(self, az, elev):
        
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
        Returns the mask to apply on the AllSky to remove the image of the danish...
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

    