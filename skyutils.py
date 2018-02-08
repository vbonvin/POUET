import numpy as np

def grid_points(res_x=400,res_y=200):
    """ Generates grid points on the sky """
    
    ra_i = 0.
    ra_f = 2*np.pi
    ra_step=(ra_f-ra_i)/res_x
    dec_i = -np.pi/2.
    dec_f = np.pi/2.
    dec_step=(dec_f-dec_i)/res_y
            
    ras = np.arange(ra_i+ra_step/2, ra_f, ra_step)
    decs= np.arange(dec_i+dec_step/2, dec_f, dec_step)
    return ras,decs

def elev2airmass(el, alt, threshold=10.):
    ''' Converts the elevation to airmass.
    :param elevation_deg: elevation [radians]
    :param alt: altitude of station [m]
    :return: air mass
    This is the code used for the Euler EDP at La Silla.'''

    altitudeFactor = 0.00087 + alt*(-8.6664803e-8) # altitude factor

    cosz = np.cos(np.pi/2.-el)

    if(cosz< 0.1): # we do not compute Airmass for small value of cosz
        airmass = threshold;
    else:
        airmass = (1.0 + altitudeFactor - altitudeFactor / (cosz * cosz)) / cosz;

    return airmass

