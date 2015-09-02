import numpy as np

import pylab as plt
import util
import matplotlib.cm as cm

import glob
import scipy.ndimage.filters as filters
import copy
import config

pca, classifier = util.readpickle(config.cl_fname)

list_of_image = glob.glob("to_test/AllSkyImage*.JPG")
for fnimg in list_of_image:
	coords = []
	datas = []
	print 'treating image', fnimg
	ar = util.loadallsky(fnimg)
	s=np.shape(ar)
	
	temp_observability = np.zeros_like(ar)
	nb_passes = np.zeros_like(ar)
	
	for y in range(config.a/2, s[0]-config.a/2, config.deltaa):
		for x in range(config.a/2, s[1]-config.a/2, config.deltaa):

			win = ar[y-config.a/2:y+config.a/2, x-config.a/2:x+config.a/2]
			#win = win.flatten()
			nb_nans = np.isnan(win)
			idnans = np.where(nb_nans)
			nb_nans = np.size(idnans)
			
			if nb_nans > config.a*config.a * 0: 
				continue
			
			coords.append([float(x-config.a/2),-float(y-config.a/2)])
			
			winf = win.flatten()
			#winf = winf[~np.isnan(winf)]
			winf[np.isnan(winf)] = np.median(winf)
			#exit()
			datas.append(np.asarray(winf))
			
			#exit()
	
			"""
			print y, y-a/2
	
			plt.figure()
			plt.imshow(win, interpolation="nearest", vmin=0, vmax=255)
			plt.colorbar()
	
			plt.figure()
			plt.imshow(ar, interpolation="nearest", vmin=0, vmax=255)
			xxx = np.array([x-a/2, x-a/2, x+a/2, x+a/2, x-a/2]) - 0.5
			yyy = np.array([y+a/2, y-a/2, y-a/2, y+a/2, y+a/2]) - 0.5
			plt.plot(xxx, yyy, color="red")
	
			plt.figure()
			winf = win.flatten()
			winf = winf[~np.isnan(winf)]
	
			# SHOW PCA OF THIS !!!!!!!!!!!!!!!!!!!!!!
	
			plt.hist(winf, bins=bins)
			plt.show()
			"""
	print 'windowing done.'
	#datas = filters.prewitt(datas)
	#datas = filters.gaussian_filter(datas,3)
	pca_coeffs = pca.transform(datas)
	pca_coeffs = classifier.predict(pca_coeffs)
	print 'classified.'
	pca_coeffs -= np.amin(pca_coeffs)
	pca_coeffs /= np.amax(pca_coeffs)

	fig1 = plt.figure(figsize=(12,12))
	ax1 = fig1.add_subplot(221, aspect='equal')
	#pca_coeffs = [0] * len(coords) 
	
	plt.imshow(ar, interpolation="nearest", vmin=0, vmax=255, cmap = cm.Greys_r)

	for (x, y), c in zip(coords, pca_coeffs):
		
		temp_observability[-y:-y+config.a, x:x+config.a] += float(c)
		nb_passes[-y:-y+config.a, x:x+config.a] += 1

	#nb_passes[nb_passes < 1] == 1.
	temp_observability /= nb_passes
	observability = temp_observability
	observability[np.isnan(ar)] = np.nan
	
	#print observability; exit()
	medfilter = filters.gaussian_filter(observability, 2)
	medfilter = filters.median_filter(medfilter, size=20)
	medfilter = filters.gaussian_filter(medfilter, 2)
	"""
	threshold = 0.5
	observability[observability < threshold] = 0
	observability[observability >= threshold] = 1"""
	
	plt.imshow(observability, interpolation="nearest", vmin=0, vmax=1, cmap = cm.RdYlGn_r, alpha=1)

	ax2 = fig1.add_subplot(222, aspect='equal')
	plt.imshow(ar, interpolation="nearest", vmin=0, vmax=255, cmap = cm.Greys_r)
	
	ax3 = fig1.add_subplot(223, aspect='equal')
	plt.imshow(medfilter, interpolation="nearest", vmin=0, vmax=1, cmap = cm.RdYlGn_r)

	outres = copy.copy(medfilter)
	threshold = 0.6
	idt = outres < threshold
	idf = outres > threshold
	#print idt
	#exit()
	ar2 = copy.copy(ar)
	ar2[idf] = np.nan
	ax4 = fig1.add_subplot(224, aspect='equal')
	plt.imshow(ar2, interpolation="nearest", vmin=0, vmax=255, cmap = cm.Greys_r)
	#plt.figure()
	#plt.scatter(pca_coeffs[:,0], pca_coeffs[:,1], c=cm.RdYlGn_r(pca_coeffs[:,0]))
	plt.show()
	plt.cla()
	plt.clf() 
	plt.close()
		
print 'done'
