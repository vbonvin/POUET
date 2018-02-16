import matplotlib.pyplot as plt
import matplotlib as mpl
import astropy.units as u
from astropy.time import Time
import numpy as np

import util

def plot_airmass_on_sky(target, meteo, ax=None):
    """
    Plots the airmass evolution on the sky of a given target at a given time.
    
    :param target: a `pouet.obs.Observable` class instance
    :param meteo: a `pouet.meteo.Meteo` class instance
    :param ax: the matplotlib axis to plot on. If None, then plot on a new figure
    """
    
    delta_ts = np.linspace(-5, 5, 101)
    assert 0 in delta_ts
    index_zero = np.where(delta_ts == 0)[0][0]
    
    obs_time = meteo.time
    obs_times = obs_time + delta_ts*u.hour
    
    if ax is None:
        plt.figure()
        ax = plt.gca(projection='polar')
    
    plt.subplots_adjust(right=0.98)
    plt.subplots_adjust(left=0.02)
    
    airmasses = []
    azimuths = []
    altitudes = []
    times = []
    
    for currenttime in obs_times:
     
        azimuth, altitude = meteo.get_AzAlt(target.alpha, target.delta, obs_time=currenttime)
        
        if altitude.degree > 0:
            azimuths.append(azimuth.radian)
            altitudes.append(90.-altitude.degree)
            airmasses.append(util.elev2airmass(altitude.value, meteo.elev))
            times.append(currenttime)
        else:
            azimuths.append(np.nan)
            altitudes.append(np.nan)
            airmasses.append(np.nan)
            times.append(np.nan)
     
    # More axes set-up.
    # Position of azimuth = 0 (data, not label).
    ax.set_theta_zero_location('N')

    # Direction of azimuth increase. Clockwise is -1
    north_to_east_ccw= True
    if north_to_east_ccw is False:
        ax.set_theta_direction(-1)
    
    # Plot target coordinates.
    sp = ax.scatter(azimuths, altitudes, c=airmasses, s=10, vmin=1, vmax=4, cmap=plt.get_cmap("YlGn_r"))#, alpha=0.7)
    
    # Airmass colobar
    cbar = plt.colorbar(sp, pad=.1, ax=ax, shrink=0.9)
    cbar.set_label("Airmass")
    
    ax.set_title("Airmass between {} and {} for {}".format(util.time2hhmm(obs_times[0]), util.time2hhmm(obs_times[-1]), target.name), \
               fontsize=10, y=1.08)
    
    # Now plot for obs_time, and add some time ticks
    degree_sign = u'\N{DEGREE SIGN}'
    ax.scatter(azimuths[index_zero], altitudes[index_zero], marker="+", c='r')
    str_time = util.time2hhmm(obs_times[index_zero])
    ax.annotate(str_time, xy=(azimuths[index_zero], altitudes[index_zero]), fontsize=8, ha="left", va="baseline", color="r")
    
    for ele in [15, 30, 45, 60, 75]:
        if ele < 40:
            fmt = "{:1.2f}"
        else:
            fmt = "{:1.1f}"
            
        ax.annotate('{:d}{:s}'.format(ele, degree_sign), xy=(np.deg2rad(-23), ele), fontsize=8, color="grey", ha='center', va='bottom', rotation=-25)
        ax.annotate(fmt.format(util.elev2airmass(np.deg2rad(90.-ele), meteo.elev)), xy=(np.deg2rad(23), ele), fontsize=8, color="grey", ha='center', va='bottom', rotation=25)
        
    ax.annotate("Airmass", xy=(np.deg2rad(23), 88), fontsize=8, color="grey", ha='center', va='bottom', rotation=25)
    ax.annotate('0' + degree_sign + ' Alt', xy=(np.deg2rad(-23), 89), fontsize=8, color="grey", ha='center', va='bottom', rotation=-23)
    
    for ii in range(np.size(airmasses)):
        
        if not ii % 20 == 0:
            continue
        
        str_time = util.time2hhmm(obs_times[ii])
        ax.annotate(str_time, xy=(azimuths[ii], altitudes[ii]), fontsize=8, ha="left", va="baseline", color="k")
        ax.scatter(azimuths[ii], altitudes[ii], marker=".", c='white', s=2)
    ax.set_rlim(1, 90)
    
    

    r_labels = [ '', '', '', '', '', '', '',]
    ax.set_rgrids(range(0, 105, 15), r_labels)
    
    # Redraw the figure for interactive sessions.
    ax.figure.canvas.draw()
    
    
if __name__ == "__main__":
    
    print("Welcome to demo mode")
    
    import meteo as meteomodule
    import obs
    
    currentmeteo = meteomodule.Meteo(name="LaSilla", cloudscheck=False, debugmode=True)
    currentmeteo.time = Time("2018-02-15 07:00:00.0")
    target = obs.Observable(name="2M1134-2103", obsprogram="lens",alpha="11:34:40.5", delta="-21:03:23")
    
    plot_airmass_on_sky(target=target, meteo=currentmeteo)
    
    plt.show()
    
    
    