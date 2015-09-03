"""
Useful functions and definitions
"""

import os
import cPickle as pickle
import gzip
import copy

import scipy.ndimage
import numpy as np

def rgb2gray(arr):
	red = arr[:,:,0]
	green = arr[:,:,1]
	blue = arr[:,:,2]
	return 0.299 * red + 0.587 * green + 0.144 * blue

def loadallsky(fnimg, return_complete=False):
	im = scipy.ndimage.imread(fnimg)
	ar = np.array(im)
	ar = rgb2gray(ar)
	rest = copy.copy(ar)
	
	s=np.shape(ar)
	xxa, xxb = s[0]/2, s[1]/2
	r = 280
	y,x = np.ogrid[-xxa:s[0]-xxa, -xxb:s[1]-xxb]
	
	adan, bdan = 145, 570
	rdan = 100
	ydan,xdan = np.ogrid[-adan:s[0]-adan, -bdan:s[1]-bdan]

	mask = np.logical_or(x*x + y*y >= r*r, xdan*xdan + ydan*ydan <= rdan*rdan)
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

	# The following puts weight to remove the noise
	rhalf = np.sqrt(-2.*np.log(0.5))*std
	wt = np.exp(-(r/rhalf - 1)**2)  #for r/rhalf > 1 only
	wt/=np.sum(wt)
	wt[r<rhalf]=1.

	"""
	wm = np.exp (-0.5 * (r / std)**2.) / std / np.sqrt(2.*np.pi)
	wm[r<std*2.35]=0.
	wm/=np.sum(wm)"""

	#g*=wt

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

	p, sucess=leastsq(gaussian,guess,args=(stamp,stampsize))


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


