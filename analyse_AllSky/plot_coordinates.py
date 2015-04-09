import numpy as np
import pylab as plt
import glob
import scipy.ndimage
import matplotlib.cm as cm
import util

theta_coordinates = np.deg2rad([-146,0,45,90,0,180,170,190,200,0, 270, 315])#np.arange(0, 360, 45))
theta_coordinates = np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315])
print theta_coordinates


cx = 279.
cy = 230.
prefered_direction = {'dir':79.5, 'posx':50, 'posy':123}
prefered_direction = {'dir':275.4, 'posx':470, 'posy':254}
prefered_direction = {'dir':194.3, 'posx':297, 'posy':336}
prefered_theta = np.arctan2(prefered_direction['posy']-cy, prefered_direction['posx']-cx)

north = prefered_theta + np.deg2rad(prefered_direction['dir'])

northx = np.cos(north) * 220 + cx
northy = np.sin(north) * 220 + cy

eastx = np.cos(north - np.pi/2.) * 250 + cx
easty = np.sin(north - np.pi/2.) * 250 + cy

coordinatesx = np.cos(north + theta_coordinates) * 330 + cx
coordinatesy = np.sin(north + theta_coordinates) * 330 + cy

list_of_image = glob.glob("AllSkyImage*.JPG")
#list_of_image = glob.glob("reference*.JPG")
for fnimg in list_of_image:
	
	im = scipy.ndimage.imread(fnimg)
	ar = np.array(im)
	ar = util.rgb2gray(ar)

fig = plt.figure()
ax = fig.add_subplot(111)

plt.imshow(ar, interpolation="nearest", cmap = cm.Greys_r)

deltatetha=180-prefered_direction['dir']+5
ax.annotate('N', xy=(northx, northy), rotation=deltatetha,
  horizontalalignment='center', verticalalignment='center')

ax.annotate('E', xy=(eastx, easty), rotation=deltatetha,
  horizontalalignment='center', verticalalignment='center')

altshow = [10, 15, 20, 25, 30, 35, 45, 45.5, 60, 75, 90-40, 90, 90-38]
altshow = [15, 30, 45, 60, 75, 90]
for angle in np.deg2rad(altshow):
	#r90 = 2.*0.71*np.sin(angle/2.) * 330
	k1 = 1.96263549291*0.945
	k2 = 0.6
	ff = 1
	rr = ff*k1*np.tan(k2 * angle / 2.) * 330

	if angle >= np.pi/2: print rr/330.
	fig.gca().add_artist(plt.Circle((cx,cy),rr,color='k', fill=False))

	textx = np.cos(north + np.deg2rad(180)) * (rr - 2) + cx
	texty = np.sin(north + np.deg2rad(180)) * (rr - 2) + cy
	ax.annotate('%d' % (90-np.ceil(np.rad2deg(angle))), xy=(textx, texty), rotation=deltatetha,#prefered_direction['dir'],
	  horizontalalignment='left', verticalalignment='center', size=10)

#plt.plot([cx, northx], [cy, northy], lw=2, color='k')
for ccx, ccy in zip(coordinatesx, coordinatesy):
	plt.plot([cx, ccx], [cy, ccy], lw=1, color='k')

plt.show()
