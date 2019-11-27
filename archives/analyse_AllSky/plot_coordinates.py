import numpy as np
import pylab as plt
import glob
import util
import imageio


theta_coordinates = np.deg2rad([-146,0,45,90,0,180,170,190,200,0, 270, 315])#np.arange(0, 360, 45))
theta_coordinates = np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315])
print theta_coordinates


params = util.get_params(location="LaSilla")

ff = params['ff']
k1 = params['k1']
k2 = params['k2']
r0 = params['r0']
cx = params['cx']
cy = params['cy']
north = params['north']
deltatetha = params['deltatetha']

coordinatesx = np.cos(north + theta_coordinates) * r0 + cx
coordinatesy = np.sin(north + theta_coordinates) * r0 + cy

list_of_image = glob.glob("current*.JPG")
for fnimg in list_of_image:
	
	im = imageio.imread(fnimg)
	ar = np.array(im)
	ar = util.rgb2gray(ar)

fig = plt.figure()
ax = fig.add_subplot(111)

plt.imshow(ar, interpolation="nearest", cmap = plt.get_cmap("Greys_r"))

northx, northy = util.get_image_coordinates(np.deg2rad(0), np.deg2rad(24))
eastx, easty = util.get_image_coordinates(np.deg2rad(90), np.deg2rad(20))

ax.annotate('N', xy=(northx, northy), rotation=deltatetha,
  horizontalalignment='center', verticalalignment='center')

ax.annotate('E', xy=(eastx, easty), rotation=deltatetha,
  horizontalalignment='center', verticalalignment='center')

altshow = [10, 15, 20, 25, 30, 35, 45, 45.5, 60, 75, 90-40, 90, 90-38]
altshow = np.arange(15, 105, 15)
for angle in np.deg2rad(altshow):
	rr = util.get_radius(angle, ff, k1, k2, r0)

	if angle >= np.pi/2: print rr/330.
	fig.gca().add_artist(plt.Circle((cx,cy),rr,color='k', fill=False))

	textx = np.cos(north + np.deg2rad(180)) * (rr - 2) + cx
	texty = np.sin(north + np.deg2rad(180)) * (rr - 2) + cy
	ax.annotate('%d' % (90-np.ceil(np.rad2deg(angle))), xy=(textx, texty), rotation=deltatetha,#prefered_direction['dir'],
	  horizontalalignment='left', verticalalignment='center', size=10)

elev_grid = np.deg2rad(np.arange(0, 90, 15))
azim_grid = np.deg2rad(np.arange(0, 360, 45))

for angle in elev_grid:
	for alpha in azim_grid:
		x, y = util.get_image_coordinates(alpha, angle)
		#plt.plot(x, y, 'o', markersize=5, c="r")
		#ax.annotate('%d %d' % (np.rad2deg(angle), np.rad2deg(alpha)), xy=(x, y), horizontalalignment='center', verticalalignment='center', size=10)
print elev_grid
print azim_grid
#exit()

#plt.plot([cx, northx], [cy, northy], lw=2, color='k')
for ccx, ccy in zip(coordinatesx, coordinatesy):
	plt.plot([cx, ccx], [cy, ccy], lw=1, color='k')

plt.show()
