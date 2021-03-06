import numpy as np
import scipy.ndimage.filters as filters
import scipy.ndimage as ndimage
import util
import copy
from scipy.spatial import cKDTree
import urllib
from astropy.time import Time


class Analyse_AllSky():
	
	def __init__(self, fimage=None, location="LaSilla"):
		
		# Todo: load ALL PARAMS
		self.location = location
		self.params = util.get_params(location)
		
		if fimage is None:
			fimage = "current.JPG"
			self.fimage = fimage
			self.retrieve_image()
			
		self.im_masked, self.im_original = util.loadallsky(fimage, return_complete=True)
		self.mask = util.get_mask(self.im_original)
		self.observability_map = None
	
	def retrieve_image(self):
		urllib.urlretrieve(self.params['url'], "current.JPG")
		self.im_masked, self.im_original = util.loadallsky(self.fimage, return_complete=True)
		self.last_im_refresh = Time.now()
		
	def update(self):
		self.retrieve_image()
		x, y = self.detect_stars()
		return self.get_observability_map(x, y)
		
	def detect_stars(self, sigma_blur=1.5, threshold=8, neighborhood_size=20, fwhm_threshold=5, meas_star=True, return_all=False):
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
			f=util.fwhm(original, xx, yy, 18,show=False,verbose=False)
			if f < fwhm_threshold:
				resx.append(xx)
				resy.append(yy)
				#resfwhm.append(f)
		
		if return_all:
			return resx, resy, x, y
		else:
			return resx, resy
		
	def get_observability_map(self, x, y, threshold=50):
		
		observability = copy.copy(self.im_masked) * 0.
		
		if len(x) > 0:
			notnans = np.where(np.isnan(self.im_masked) == False)
			notnans = zip(notnans[0], notnans[1])
			tree = cKDTree(zip(x,y))	
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
	
	def is_observable(self, az, elev):
		"""
		Angles must be in radians!
		"""
		xpix, ypix = util.get_image_coordinates(az, elev, location=self.location)
		
		if self.observability_map is None:
			raise RuntimeError("You should run the update() method first, no image has been analysed yet.")
		
		try:
			xpix = int(np.round(xpix))
			ypix = int(np.round(ypix))
		except ValueError:
			return np.nan
		try:
			return self.observability_map[xpix, ypix]
		except IndexError:
			return np.nan 

			
if __name__ == "__main__":
	import glob
	import matplotlib.pyplot as plt
	
	list_of_images = glob.glob("to_test/AllSkyImage*.JPG")
	print "I found %s images" % len(list_of_images)
	
	imgs = []
	for fim in list_of_images:
		imgs.append(util.loadallsky(fim))
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

		print 'Treating', list_of_images[i]
	
		imo = copy.deepcopy(im)
		analysis = Analyse_AllSky(fimage = list_of_images[i])
		x, y, ax, ay = analysis.detect_stars(return_all=True)
		observability = analysis.get_observability_map(x, y)
		
		print '0, 30,', analysis.is_observable(np.deg2rad(0), np.deg2rad(30))
		print '0, -30,', analysis.is_observable(np.deg2rad(0), np.deg2rad(-30))
		print '180, 0,', analysis.is_observable(np.deg2rad(180), np.deg2rad(0))
		
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

