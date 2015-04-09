import numpy as np
import scipy.ndimage
import matplotlib.pyplot as plt
import util
import matplotlib.cm as cm
import os
import glob

import config

def keypress(event):
	global instr

	names = {'c':'cloud-covered', 's':'Good sky', 'm':'moon', 'u':'Unknown/defects'}

	if event.key in ['c','s','m','u']:
		print 'Pressed "%s" --> %s' % (event.key, names[event.key])
		plt.close()
		instr = event.key
	else:
		print "mumble mumble, ignored"

#disable matplotlib keymaps
keyMaps = [key for key in plt.rcParams.keys() if 'keymap.' in key]
for keyMap in keyMaps:
	plt.rcParams[keyMap] = ''   

list_of_image = glob.glob("AllSkyImage*.JPG")
if os.path.exists(config.db_fname):
	[id_im, coords, datas, labels] = util.readpickle(config.db_fname)
	coords = coords.tolist()
	datas = datas.tolist()
else:
	datas = []
	coords = []
	labels = []
	id_im = []
	
list_img_already_done = np.unique(id_im)


for fnimg in list_of_image:
	if fnimg in list_img_already_done:
		print '%s already in database, skipping...' % fnimg
		continue
	
	print 'Loading %s...' % fnimg
	ar = util.loadallsky(fnimg)
	s=np.shape(ar)

	for y in range(config.a/2, s[0]-config.a/2, config.deltaat):
		
		for x in range(config.a/2, s[1]-config.a/2, config.deltaat):
	
			win = ar[y-config.a/2:y+config.a/2, x-config.a/2:x+config.a/2]
			#win = win.flatten()
			nb_nans = np.isnan(win)
			nb_nans = np.size(np.where(nb_nans))
			
			
			if nb_nans > 0: 
				continue
			
			coords.append([float(x),float(-y)])
			
			winf = win.flatten()
			#winf = winf[~np.isnan(winf)]
			winf[np.isnan(winf)] = np.nanmedian(winf)
			#exit()
			datas.append(np.asarray(winf))
	
			fig = plt.figure(figsize=(12,6))
			ax0 = plt.subplot(121)
			ax0.imshow(win, interpolation="nearest", vmin=0, vmax=255, cmap = cm.Greys_r)
	
			ax1 = plt.subplot(122)
			cmap = cm.Greys_r 
			ax1.imshow(ar, interpolation="nearest", vmin=0, vmax=255, cmap = cmap)
			xxx = np.array([x-config.a/2, x-config.a/2, x+config.a/2, x+config.a/2, x-config.a/2]) - 0.5
			yyy = np.array([y+config.a/2, y-config.a/2, y-config.a/2, y+config.a/2, y+config.a/2]) - 0.5
			ax1.plot(xxx, yyy, color="red")
			
			ax1.set_xlim([0, s[1]])
			ax1.set_ylim([0, s[0]])
			ax1.set_xticks([])
			ax1.set_yticks([])
			
			ax1.annotate('s: good sky\nc: clouds\nm: moon\nu: unknown/defect',
				xy=(0.6, 0.3),  # theta, radius
				xytext=(0.5, 0.18),	# fraction, fraction
				textcoords='figure fraction',
				arrowprops=None,
				horizontalalignment='left',
				verticalalignment='top',
				)
			
			instr = ''
			cid = fig.canvas.mpl_connect('key_press_event', keypress)
			plt.show()
			labels.append(instr)
			id_im.append(fnimg)

datas = np.asarray(datas)
coords = np.asarray(coords)

database = [id_im, coords, datas, labels]
util.writepickle(database, config.db_fname)
