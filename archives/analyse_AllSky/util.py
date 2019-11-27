"""
Useful functions and definitions
"""

import os
import cPickle as pickle
import gzip
import copy
import imageio

import numpy as np

import urllib2, re

def rgb2gray(arr):
	red = arr[:,:,0]
	green = arr[:,:,1]
	blue = arr[:,:,2]
	
	return 0.299 * red + 0.587 * green + 0.144 * blue

def get_mask(ar):
	s=np.shape(ar)
	#xxa, xxb = s[0]/2, s[1]/2
	#r = 210#285
	#xxb = 279
	#xxa = 230
	
	#	y,x = np.ogrid[-xxa:s[0]-xxa, -xxb:s[1]-xxb]
	xxa, xxb = s[0]/2, s[1]/2
	r = 285
	y,x = np.ogrid[-xxa:s[0]-xxa, -xxb:s[1]-xxb]
	
	adan, bdan = 145, 570
	rdan = 88
	ydan,xdan = np.ogrid[-adan:s[0]-adan, -bdan:s[1]-bdan]

	mask = np.logical_or(x*x + y*y >= r*r, xdan*xdan + ydan*ydan <= rdan*rdan)
	
	return mask

def loadallsky(fnimg, return_complete=False):
	im = imageio.imread(fnimg)
	ar = np.array(im)
	ar = rgb2gray(ar)
	rest = copy.copy(ar)
	
	mask = get_mask(ar)
	ar[mask] = np.nan
	
	if return_complete:
		return ar, rest
	else:
		return ar

def writepickle(obj, filepath, protocol = -1):
	"""
	I write your python object obj into a pickle file at filepath.
	If filepath ends with .gz, I'll use gzip to compress the pickle.
	Leave protocol = -1 : I'll use the latest binary protocol of pickle.
	"""
	if os.path.splitext(filepath)[1] == ".gz":
		pkl_file = gzip.open(filepath, 'wb')
	else:
		pkl_file = open(filepath, 'wb')
	
	pickle.dump(obj, pkl_file, protocol)
	pkl_file.close()
	
def readpickle(filepath):
	"""
	I read a pickle file and return whatever object it contains.
	If the filepath ends with .gz, I'll unzip the pickle file.
	"""
	if os.path.splitext(filepath)[1] == ".gz":
		pkl_file = gzip.open(filepath,'rb')
	else:
		pkl_file = open(filepath, 'rb')
	obj = pickle.load(pkl_file)
	pkl_file.close()
	return obj

from scipy.optimize import leastsq

def gaussian(params,stamp,stampsize):
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

def fwhm(data,xc,yc,stampsize,show=False, verbose=True):
	if verbose : print
	if xc < stampsize or yc < stampsize or data.shape[1]-xc < stampsize or data.shape[0]-yc < stampsize:
		if verbose: print "WARNING: Star at %d %d could not be measured (too close to edge)" % (xc,yc)
		return np.nan
	assert stampsize % 2==0 #make sure it's an integer
	
	xi=int(xc-stampsize/2.)
	xf=int(xc+stampsize/2.)
	yi=int(yc-stampsize/2.)
	yf=int(yc+stampsize/2.)
	stamp=data[yi:yf,xi:xf]
	
	if np.isnan(np.sum(stamp)):
		if verbose: print "WARNING: Star at %d %d could not be measured (contains NaN)" % (xc,yc)
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
		if verbose:print "WARNING: Star at %d %d could not be measured (width unphysical)" % (xc,yc)
		#return np.nan
	if verbose:
		print p
		print 'x=%.2f' % (xi+p[0])
		print 'y=%.2f' % (yi+p[1])
		print 'width=%.2f' % p[2]
		print 'FWHM=%.2f' % (p[2] * 2. * np.sqrt(2.*np.log(2.)))

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

def get_params(location="LaSilla"):
	if location == "LaSilla":
		cx = 279
		cy = 230
		prefered_direction = {'dir':194.3, 'posx':297, 'posy':336}
		prefered_theta = np.arctan2(prefered_direction['posy']-cy, prefered_direction['posx']-cx)
		north = prefered_theta + np.deg2rad(prefered_direction['dir'])
		deltatetha=180-prefered_direction['dir']+5
		params = {'k1': 1.96263549291*0.945,
				'k2': 0.6,
				'ff': 1.,
				'r0': 330,
				'cx': cx,
				'cy': cy,
				'prefered_direction':prefered_direction,
				'prefered_theta': prefered_theta,
				'deltatetha': deltatetha,
				'north': north,
				'url': "http://allsky-dk154.asu.cas.cz/raw/AllSkyCurrentImage.JPG",
				'url_weather':"http://www.ls.eso.org/lasilla/dimm/meteo.last",
				'wind_pointing_limit':15.,
				'wind_stopping_limit':20.}
	else:
		raise ValueError("Unknown location")
	
	return params

def get_radius(elev, ff, k1, k2, r0):
	return ff*k1*np.tan(k2 * elev / 2.) * r0

def get_image_coordinates(az, elev, location="LaSilla", params=None):
	if params is None:
		params = get_params(location)
	
	k1 = params['k1']
	k2 = params['k2']
	ff = params['ff']
	r0 = params['r0']
	north = params['north']
	cx = params['cx']
	cy = params['cy']

	az *= -1.
	elev = np.pi/2. - elev
	
	rr = get_radius(elev, ff, k1, k2, r0)
	
	x = np.cos(north + az) * (rr - 2) + cx 
	y = np.sin(north + az) * (rr - 2) + cy
	
	if x < 0 or y < 0: 
		x = np.nan
		y = np.nan 

	return x, y


def get_wind(url_weather="http://www.ls.eso.org/lasilla/dimm/meteo.last"):
	"""
	WARNING: bad pratice I'm not sure this is used and is copy/paste code!!!
	"""

	raise RuntimeError("Using get_wind from analyse_AllSky/util.py")

	#todo: add a "no connection" message if page is not reachable instead of an error
	WS=[]
	WD=[]
	data=urllib2.urlopen(url_weather).read()
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
		WS = np.asarray(WS, dtype=np.float)
		WS = WS[WS > 0]
		WS = WS[WS < 99]
		WS = np.mean(WS)
		
	return WD, WS
