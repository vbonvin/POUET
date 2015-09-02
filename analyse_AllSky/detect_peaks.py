import numpy as np
import scipy.ndimage.filters as filters
import scipy.ndimage as ndimage
import util
import copy
from scipy.spatial import cKDTree

def gaussian(height, center_x, center_y, width_x, width_y):
	"""Returns a gaussian function with the given parameters"""
	width_x = float(width_x)
	width_y = float(width_y)
	return lambda x,y: height*np.exp(-(((center_x-x)/width_x)**2+((center_y-y)/width_y)**2)/2)

def detect_stars(image, sigma_blur=2, threshold=7, neighborhood_size=20, fwhm_threshold=10, meas_star=True, return_all=False):
	original = copy.copy(image)
	image = filters.gaussian_filter(image, sigma_blur)
	data_max = filters.maximum_filter(image, neighborhood_size)
	maxima = (image == data_max)
	
	data_min = filters.minimum_filter(image, neighborhood_size)
	diff = ((data_max - data_min) > threshold)
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
		f=util.fwhm(original, xx, yy, 18,show=False,verbose=False)
		if f < fwhm_threshold:
			resx.append(xx)
			resy.append(yy)
			#resfwhm.append(f)
	
	if return_all:
		return resx, resy, x, y
	else:
		return resx, resy
	
def get_observability(data, x, y, threshold=60):
	observability = copy.copy(data) * 0.
	
	if len(x) > 0:
		notnans = np.where(np.isnan(data) == False)
		notnans = zip(notnans[0], notnans[1])
		tree = cKDTree(zip(x,y))	
		for nx, ny in notnans:
			obs = len(tree.query_ball_point((ny,nx), threshold))
			if obs > 4 : observability[nx,ny] = 1. 
			elif obs > 1 : observability[nx,ny] = 0.5
		#res = tree.count_neighbors(pixels, 10)
		#print res
		observability = filters.gaussian_filter(observability, 2)
	
	return observability
			
if __name__ == "__main__":
	import glob
	import matplotlib.pyplot as plt
	
	list_of_images = glob.glob("to_test/AllSkyImage*.JPG")
	
	imgs = []
	for fim in list_of_images:
		imgs.append(util.loadallsky(fim))
		
		plt.imshow(imgs[0], interpolation='nearest')
		plt.show(); exit()
		
	for i, im in enumerate(imgs):
		#if i < 6:continue
		print 'Treating', list_of_images[i]
	
		imo = copy.deepcopy(im)
		x, y, ax, ay = detect_stars(im, return_all=True)
		observability = get_observability(im, x, y)
		
	
		plt.figure(figsize=(18,6))
		plt.subplot(1, 3, 1)
		plt.imshow(imo, vmin=0, vmax=255, cmap=plt.get_cmap('Greys_r'))
		#plt.scatter(ids[1], ids[0], s=4, marker='o', edgecolors='r', color='none')
		
		plt.scatter(ax, ay, s=4, marker='o', edgecolors='g', color='none')
		plt.scatter(x, y, s=4, marker='o', edgecolors='r', color='none')
		
		plt.subplot(1, 3, 2)
		plt.imshow(imo, vmin=0, vmax=255, cmap=plt.get_cmap('Greys_r'))
		plt.scatter(x, y, s=4, marker='o', edgecolors='r', color='none')
		
		plt.subplot(1, 3, 3)
		plt.imshow(imo, vmin=0, vmax=255, cmap=plt.get_cmap('Greys_r'))
		plt.imshow(observability, cmap=plt.get_cmap('RdYlGn'), alpha=0.2)
	
	plt.show()
