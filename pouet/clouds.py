import numpy as np
import scipy.ndimage
from scipy.optimize import leastsq
import scipy.ndimage.filters as filters
import scipy.ndimage as ndimage
from scipy.spatial import cKDTree
import copy
#todo: there seem to be a problem with urllib.request which does not exists anymore...?
#import urllib.request, urllib.parse, urllib.error
import requests
import astropy.time
from astropy import units as u

import util

import logging
logger = logging.getLogger(__name__)

###################################################################################################
# Definition of the class
###################################################################################################

class Clouds():
    """
    This class loads and analyses an all sky image of the Sky and returns an observability map that
    can be used by another method to advise the observer on the sky quality.
    
    :note: This module can also be used to explore older images, see the example code in `__main__()`.
    """
    
    def __init__(self, name, fimage=None, debugmode=False):
        """
        Initialises the class
        
        :param fimage: (default is None) filename of the all sky image to analyse
        :type: string
        :param name: (default is "LaSilla") name of the location to load the right config file
        """
        
        self.location = name
        
        self.station = (util.load_station(name)).AllSky()
        self.last_im_refresh = None
        self.debugmode = debugmode
        self.failed_connection = False
        
        if fimage is None:
            fimage = "current.JPG"
            if debugmode: 
                fimage = "config/AllSkyDebugMode.JPG" # To be used for debug purposes
                logger.warning("Cloud analysis is working in debug mode (not using the real current image)")
            self.fimage = fimage
            #self.retrieve_image()

        self.observability_map = None
    
    def retrieve_image(self):
        """
        Downloads the current all sky from the server and saves it to disk.
        The url of the image is retrived from the configuration file at that location
        """

        if not self.debugmode:
            try:
                logger.info("Loading all sky from {}...".format(self.station.params['url']))
                #urllib.request.urlretrieve(self.params['url'], "current.JPG")
                open("current.JPG", 'wb').write(requests.get(self.station.params['url']).content)
                self.failed_connection = False
            except :
                self.failed_connection = True
                logger.warning("Cannot download All Sky image. Either you or the server is offline!")
                return 1

        self.im_masked, self.im_original = loadallsky(self.fimage, station=self.station, return_complete=True)
        self.last_im_refresh = astropy.time.Time.now()
        
    def update(self):
        """
        Downloads the image, detects the stars and returns the observability map
        """

        if not self.last_im_refresh is None and (astropy.time.Time.now() - self.last_im_refresh).to(u.s).value / 60. < 1.5:
            logger.info("Last image was downloaded more recently than 1.5 minutes ago, I don't download it again")
            #Seems to be okay#logger.critical("TODO: make sure that this map is correct and there's no .T missing (see get_observability_map)")
            return self.observability_map
        
        self.retrieve_image()
        
        if self.failed_connection:
            logger.warning("Connection down and not running in debugmode so cannot analyse All Sky")
            return None
        
        x, y = self.detect_stars()
        return self.get_observability_map(x, y)
        
    def detect_stars(self, sigma_blur=1.2, threshold=8, neighborhood_size=20, fwhm_threshold=5, meas_star=True, return_all=False):
        """
        Analyses the images to find the stars. 

        :todo: describe algo in more details
        
        :param sigma_blur: Sigma of the Gaussian kernel (in px)
        :param threshold: threshold of detection
        :param neighborhood_size: footprint of the maximum and minimum filters
        :param fwhm_threshold: select objects smaller than this fwhm
        :param meas_star: if not interested in computing fwhm for all objects bypass and return positions of objects
        :param return_all: if `True`, returns the positions of stars + detected objects otherwise only stars

        """
        
        logger.debug("Detecting stars in All Sky...")
        original = self.im_original
        image = filters.gaussian_filter(self.im_masked, sigma_blur)
        data_max = filters.maximum_filter(image, neighborhood_size)
        maxima = (image == data_max)
        
        data_min = filters.minimum_filter(image, neighborhood_size)
        
        # In order to avoid outputing warnings, remove all nans (not the Indian bread)
        delta_arr = data_max - data_min
        delta_arr[np.isnan(delta_arr)] = 0.

        diff = (delta_arr > threshold)
        maxima[diff == 0] = 0
        
        labeled, _ = ndimage.label(maxima)
        slices = ndimage.find_objects(labeled)
        
        x, y = [], []
        for dy, dx in slices:
            x_center = (dx.start + dx.stop - 1)/2
            x.append(x_center)
            y_center = (dy.start + dy.stop - 1)/2    
            y.append(y_center)
        
        if not meas_star: 
            return x, y
        
        resx = []
        resy = []
        for xx, yy in zip(x, y):
            f = fwhm(original, xx, yy, 18)
            if f < fwhm_threshold:
                resx.append(xx)
                resy.append(yy)
                #resfwhm.append(f)
        
        logger.debug("Done. {} stars found".format(len(resx)))
        
        if return_all:
            return resx, resy, x, y
        else:
            return resx, resy
        
    def get_observability_map(self, x, y, threshold=50):
        """
        Returns an observability map (an image of the sky)
        
        :param x: x coordinates of detected stars
        :param y: y coordinates of detected stars
        :param threshold: distance threshold in px of stars such that we have observations
        """
        
        observability = copy.copy(self.im_masked) * 0.
        
        if len(x) > 0:
            notnans = np.where(np.isnan(self.im_masked) == False)
            notnans = list(zip(notnans[0], notnans[1]))
            tree = cKDTree(list(zip(x,y)))    
            for nx, ny in notnans:
                obs = len(tree.query_ball_point((ny,nx), threshold))
                if obs > 2 : observability[nx,ny] = 1. 
                elif obs > 1 : observability[nx,ny] = 0.5#0.5
                #elif obs == 1 : observability[nx,ny] = 0.3
            #res = tree.count_neighbors(pixels, 10)
            #print res
            observability = filters.gaussian_filter(observability, 2)
        """
        #print np.size(np.where(observability > 0.5)[0])
        if np.size(np.where(observability > 0.5)[0]) < 100000:
            obsmap = np.ones_like(observability)
            hstep = 30
            medim = np.nanmedian(self.im_masked)
            #print medim 
            #medim = 150
            for ix in range(hstep,np.shape(self.im_masked)[0],5):#range(hstep,np.shape(self.im_masked)[0],hstep*2):
                for iy in range(hstep,np.shape(self.im_masked)[1],5):
                    if not np.isnan(np.nanmedian(self.im_masked[ix-hstep:ix+hstep,iy-hstep:iy+hstep])):
                        mar = self.im_masked[ix-hstep:ix+hstep,iy-hstep:iy+hstep]
                        res = np.nanmedian(mar) < 0.9*medim
                        obsmap[ix-hstep:ix+hstep,iy-hstep:iy+hstep] = res
                        #= np.ones_like(mar) * res
            obsmap[np.isnan(self.im_masked)] = np.nan
            #print np.nanmedian(self.im_masked)
            #exit()
    

            observability = np.logical_and(observability, obsmap)
        """
        
        self.observability_map = observability.T
        
        return observability

###################################################################################################
# Utilitaries for clouds (only specific functions for that particular module
###################################################################################################

def rgb2gray(arr):
    """
    The all sky in LaSilla is not RGB, but JPG is is 3D...
    """
    red = arr[:,:,0]
    green = arr[:,:,1]
    blue = arr[:,:,2]
    
    return 0.299 * red + 0.587 * green + 0.144 * blue

def loadallsky(fnimg, station, return_complete=False):
    """
    Loads the image
    :param return_complete: returns the masked image and the unmasked image
    """
    
    logger.debug("Loading image {}...".format(fnimg))
    im = scipy.ndimage.imread(fnimg)
    ar = np.array(im)
    ar = rgb2gray(ar)
    rest = copy.copy(ar)
    
    mask = station.get_mask(ar)
    ar[mask] = np.nan
    
    if return_complete:
        return ar, rest
    else:
        return ar
    
def gaussian(params,stamp,stampsize):
    """
    Returns a 2D gaussian profile
    """
    
    xc,yc,std,i0,sky=params

    x=np.arange(stampsize)
    x=x.astype(np.float64)
    std=std.astype(np.float64)
    i0=i0.astype(np.float64)
    x,y=np.meshgrid(x,x)
    x-=xc
    y-=yc
    r=np.hypot(x,y)

    g=i0 * np.exp (-0.5 * (r / std)**2.) / std / np.sqrt(2.*np.pi) + sky
    g-=stamp

    return np.ravel(g)
    
def fwhm(data,xc,yc,stampsize,show=False, verbose=False):
    """
    Fits a 2D Gaussian profile and returns the FWHM in px
    
    :param data: the stamp containing the image 
    :param xc: centroid x position
    :param yc: centroid y position
    :param stampsize: size of nominal square stampe
    :param show: shows a diagnostic plot of the fit
    :param verbose: should I speak? 
    """

    #TODO: remove verbose since I use loggger?
    
    if xc < stampsize or yc < stampsize or data.shape[1]-xc < stampsize or data.shape[0]-yc < stampsize:
        if verbose: logger.debug("WARNING: Star at %d %d could not be measured (too close to edge)" % (xc,yc))
        return np.nan
    assert stampsize % 2==0 #make sure it's an integer
    
    xi=int(xc-stampsize/2.)
    xf=int(xc+stampsize/2.)
    yi=int(yc-stampsize/2.)
    yf=int(yc+stampsize/2.)
    stamp=data[yi:yf,xi:xf]
    
    if np.isnan(np.sum(stamp)):
        if verbose: logger.debug("WARNING: Star at %d %d could not be measured (contains NaN)" % (xc,yc))
        return np.nan

    if show:
        import pylab as plt
        plt.figure()
        plt.imshow(stamp,interpolation="nearest")
    
        """plt.figure()
        plt.scatter([xc],[yc],marker='+', s=50,c='k')
        plt.scatter([xi,xi,xf,xf],[yi,yf,yi,yf],marker='+', s=50,c='k')
        plt.imshow(data,interpolation="nearest")"""

    guess=[stampsize/2.,stampsize/2.,2.,1e5, np.median(data)]

    p, _ = leastsq(gaussian,guess,args=(stamp,stampsize))


    if p[2]<0.2 or p[2]>1e3:
        if verbose: logger.debug("WARNING: Star at %d %d could not be measured (width unphysical)" % (xc,yc))
        #return np.nan
    if verbose:
        logger.debug(p)
        logger.debug('x=%.2f' % (xi+p[0]))
        logger.debug('y=%.2f' % (yi+p[1]))
        logger.debug('width=%.2f' % p[2])
        logger.debug('FWHM=%.2f' % (p[2] * 2. * np.sqrt(2.*np.log(2.))))

    if show:
        plt.figure()
        plt.imshow(np.log10(data),interpolation="nearest")

        xs=[xi,xf,xf,xi,xi]
        ys=[yi,yi,yf,yf,yi]
        plt.scatter(xi+p[0],yi+p[1],marker="*",c='k')
        plt.plot(xs,ys,color="red")
        plt.xlim([0,np.shape(data)[0]-1])
        plt.ylim([np.shape(data)[1]-1,0])
        plt.show()

    return p[2] * 2. * np.sqrt(2.*np.log(2.))


###################################################################################################
# Standard examples to be analysed when running clouds.py
###################################################################################################
            
if __name__ == "__main__":
    import glob
    import matplotlib.pyplot as plt
    
    logging.basicConfig(level=logging.DEBUG)
    
    station = util.load_station("LaSilla").AllSky()
    
    list_of_images = glob.glob("to_test/*.JPG")
    print("I found %s images" % len(list_of_images))
    
    imgs = []
    for fim in list_of_images:
        imgs.append(loadallsky(fim, station=station))
    """
    img = None
    for fim in list_of_images:
        if img is None:
            img = util.loadallsky(fim)
        else:
            img += util.loadallsky(fim)
    imgs = [img]
    """
    #plt.imshow(img, interpolation='nearest')
    #plt.show(); exit()
        
    for i, im in enumerate(imgs):

        print('Treating', list_of_images[i])
    
        imo = copy.deepcopy(im)
        analysis = Clouds(fimage = list_of_images[i], name="LaSilla")
        analysis.im_masked, analysis.im_original = loadallsky(list_of_images[i], station=station, return_complete=True)
        analysis.mask = station.get_mask(analysis.im_original)
        
        x, y, ax, ay = analysis.detect_stars(return_all=True)
        observability = analysis.get_observability_map(x, y)
        
        #print '0, 30,', analysis.is_observable(np.deg2rad(0), np.deg2rad(30))
        #print '0, -30,', analysis.is_observable(np.deg2rad(0), np.deg2rad(-30))
        #print '180, 0,', analysis.is_observable(np.deg2rad(180), np.deg2rad(0))
        
        plt.figure(figsize=(18,6))
        plt.subplot(1, 3, 1)
        plt.imshow(imo, vmin=0, vmax=255, cmap=plt.get_cmap('Greys_r'))
        plt.scatter(ax, ay, s=4, marker='o', edgecolors='g', color='none')
        #plt.scatter(x, y, s=4, marker='o', edgecolors='r', color='none')
        plt.title('Detected peaks')
        
        plt.subplot(1, 3, 2)
        plt.imshow(imo, vmin=0, vmax=255, cmap=plt.get_cmap('Greys_r'))
        plt.scatter(x, y, s=4, marker='o', edgecolors='r', color='none')
        plt.title('Detected stars')
        
        plt.subplot(1, 3, 3)
        plt.imshow(imo, vmin=0, vmax=255, cmap=plt.get_cmap('Greys_r'))
        plt.imshow(observability, cmap=plt.get_cmap('RdYlGn'), alpha=0.2)
        plt.title("Observability")
    
    plt.show()

