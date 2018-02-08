import numpy as np

def elev2Airmass(el, alt):
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

def obselev2airmass(el, alt):
    
    zenith = np.pi/2.-el
    airmass = 1.0/np.cos(zenith)
    if airmass < 0 or airmass > 10:
        airmass = 10
    
    return airmass 

for angle in np.linspace(0, np.pi/2):
    
    alt = 2400.
    print(np.rad2deg(angle), elev2Airmass(angle, alt), obselev2airmass(angle, alt))