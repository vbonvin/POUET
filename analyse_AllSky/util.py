"""
Useful functions and definitions
"""

import os
import cPickle as pickle
import gzip

import scipy.ndimage
import numpy as np

def rgb2gray(arr):
	red = arr[:,:,0]
	green = arr[:,:,1]
	blue = arr[:,:,2]
	return 0.299 * red + 0.587 * green + 0.144 * blue

def loadallsky(fnimg):
	im = scipy.ndimage.imread(fnimg)
	ar = np.array(im)
	ar = rgb2gray(ar)
		
	s=np.shape(ar)
	xxa, xxb = s[0]/2, s[1]/2
	r = 280
	y,x = np.ogrid[-xxa:s[0]-xxa, -xxb:s[1]-xxb]
	
	adan, bdan = 145, 570
	rdan = 100
	ydan,xdan = np.ogrid[-adan:s[0]-adan, -bdan:s[1]-bdan]

	mask = np.logical_or(x*x + y*y >= r*r, xdan*xdan + ydan*ydan <= rdan*rdan)
	ar[mask] = np.nan
	
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
