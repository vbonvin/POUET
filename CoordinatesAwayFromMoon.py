"""
Author: Thibault Kuntzer
Email: thibault.kuntzer@epfl.ch
Date: 2014-07-07
Aim: Plots all coordinates that are a minimum of <moon_angle> degrees from the Moon and with a maximal <airmass_max>
"""

import ephem
import numpy as np
import pylab as plt

########################################################

LaSilla=ephem.Observer()
LaSilla.lon, LaSilla.lat = '-70.73291','-29.259354'
LaSilla.date="2015/09/20 00:20" # !! CURRENT UT DATE --> AFTER MIDNIGHT CHANGE THE DATE TOO!
LaSilla.elevation=2400

moon_angle=40 # in degree
airmass_max = 1.5 # Maximal airmass tolerable
#########################################################
def hpos(body): return body.ra, body.dec

def grid_points(res_x=400,res_y=200):
    """ Generates the grid points necessary for the computation """
    
    ra_i = 0.
    ra_f = 2*np.pi
    ra_step=(ra_f-ra_i)/res_x
    dec_i = -np.pi/2.
    dec_f = np.pi/2.
    dec_step=(dec_f-dec_i)/res_y
            
    ras = np.arange(ra_i+ra_step/2, ra_f, ra_step)
    decs= np.arange(dec_i+dec_step/2, dec_f, dec_step)
    return ras,decs

def Elev2Airmass(el,lat,alt):
    ''' Converts the elevation to airmass.
    @param elevation_deg elevation [radians]
    @return airmass air mass
    This is the code used at La Silla for Euler.'''

    altitudeFactor = 0.00087 + alt*(-8.6664803e-8) # altitude factor

    cosz = np.cos(np.pi/2.-el)

    if(cosz< 0.1): # we do not compute Airmass for small value of cosz
        airmass = 13;
    else:
        airmass = (1.0+altitudeFactor-altitudeFactor/(cosz*cosz))/cosz;

    return airmass


#########################################################

moon = ephem.Moon()
moon.compute(LaSilla)

#########################################################4

ras,decs=grid_points()
ra_g, dec_g = np.meshgrid(ras,decs)
sep=np.zeros_like(ra_g)
vis=np.zeros_like(ra_g)
for i,ra in enumerate(ras):
    for j,dec in enumerate(decs):
        star = ephem.FixedBody()
        star._ra = ra
        star._dec = dec
        star.compute(LaSilla)
        if Elev2Airmass(el=star.alt+0,lat=LaSilla.lat,alt=LaSilla.elevation)<airmass_max:
            vis[j,i]=1
            s = ephem.separation(hpos(moon), (ra, dec))+0.
            if np.rad2deg(s)-0.5>moon_angle: # Don't forget that the angular diam of the Moon is ~0.5 deg
                sep[j,i]=np.rad2deg(s)
            else: sep[j,i]=np.nan
        else: 
            sep[j,i]=np.nan
            vis[j,i]=np.nan
    del star
    
#########################################################

ra_g=ra_g/2/np.pi*24
dec_g=dec_g/np.pi*180

plt.figure()
ax=plt.subplot(111)
plt.subplots_adjust(right=1.0)
v = np.linspace(moon_angle, 180, 100, endpoint=True)
plt.contourf(ra_g,dec_g,vis,cmap=plt.cm.Greys)
CS=plt.contour(ra_g,dec_g, sep, levels=[50,70,90],colors=['yellow','red','k'],inline=1)
plt.clabel(CS,fontsize=10,fmt='%d')
CS=plt.contourf(ra_g,dec_g,sep,v,)
t= np.arange(moon_angle, 190, 10)
plt.colorbar(CS,ticks=t)
plt.xlim([0,24])
plt.ylim([-90,90])
plt.xticks(rotation=70)
plt.xlabel('Right ascension')
plt.ylabel('Declination')



ax.set_xticks(np.linspace(0,24,25))
ax.set_yticks(np.linspace(-90,90,19))
""" This is useless and we lose readability on the graph
import astropy.coordinates.angles as angles
labels = [item.get_text() for item in ax.get_xticklabels()]
for i,[label, tick] in enumerate(zip(labels,ax.get_xticks())):
    labels[i] = angles.Angle(tick,unit="radian").hms
    labels[i] = "%02dh" % (labels[i][0])
ax.set_xticklabels(labels)

labels = [item.get_text() for item in ax.get_yticklabels()]
for i,[label, tick] in enumerate(zip(labels,ax.get_yticks())):
    labels[i] = angles.Angle(tick,unit="radian").dms
    labels[i] = "%02dd" % (labels[i][0])
ax.set_yticklabels(labels)
"""
plt.title("%s - Moon sep %d deg - max airmass %1.2f" % (LaSilla.date, moon_angle, airmass_max))

plt.grid()

plt.show()