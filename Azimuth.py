from numpy import sin, cos, arctan2, tan, deg2rad, floor, arcsin
import astropy.coordinates.angles as angles
from astropy.time import Time
from astropy import units as u
import urllib2
import re
import getopt, sys

################################
### Parameters of observatory  #
################################
lat=angles.Angle("-29d15m33.7s") # La Silla
lon=angles.Angle("-70.7313d") # La Silla
ref_dir=180
##################################################################################

def get_wind(url_weather="http://www.ls.eso.org/lasilla/dimm/meteo.last"):
	WS=[]
	WD=[]
	data=urllib2.urlopen(url_weather).read()
	data=data.split("\n") # then split it into lines
	for line in data:
		if re.match( r'WD', line, re.M|re.I):
			WD.append(int(line[20:25])) # AVG
		if re.match( r'WS', line, re.M|re.I):
			WS.append(float(line[20:25])) # AVG

	WD = WD[0] # WD is chosen between station 1 or 2 in EDP pour la Silla.
	WS = WS[2] # next to 3.6m telescope --> conservative choice.
	
	return WD, WS	

def get_AzAlt(alpha,delta,obs_time,ref_dir):
	""" "http://aa.usno.navy.mil/faq/docs/Alt_Az.php """
	D= obs_time.jd - 2451545.0
	GMST = 18.697374558 + 24.06570982441908*D
	epsilon= deg2rad(23.4393 - 0.0000004*D)
	eqeq= -0.000319*sin(deg2rad(125.04 - 0.052954*D)) - 0.000024*sin(2.*deg2rad(280.47 + 0.98565*D))*cos(epsilon)
	GAST = GMST + eqeq
	GAST -= floor(GAST/24.)*24.

	LHA = angles.Angle((GAST-alpha.hour)*15+lon.degree, unit="degree")
	if LHA > 0: LHA += angles.Angle(floor(LHA/360.)*360., unit="degree")
	else: LHA -= angles.Angle(floor(LHA/360.)*360., unit="degree")

	sina=cos(LHA.radian)*cos(delta.radian)*cos(lat.radian)+sin(delta.radian)*sin(lat.radian)
	Alt = angles.Angle(arcsin(sina),unit="radian")

	num = -sin(LHA.radian)
	den = tan(delta.radian)*cos(lat.radian)-sin(lat.radian)*cos(LHA.radian)

	Az = angles.Angle(arctan2(num,den), unit="radian")
	Az-=angles.Angle(ref_dir, unit="degree")
	if Az.degree < -180: 
		Az+=angles.Angle(360, unit="degree")
	#print 'Azimuth', '\t',  Az.to_string(unit=u.degree)
	return Az, Alt

def hilite(string, status, bold):
	'''Graphism: colors and bold in the terminal'''
	import sys

	if not sys.stdout.isatty() : return '*'+string+'*'
	
	attr = []
	if status:
		# green
		attr.append('32')
	else:
		# red
		attr.append('31')
	if bold:
		attr.append('1')
	return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)

def rev(angle):
	import numpy as np
	if angle < 0: angle += 360
	elif angle > 360: angle -= 360
	return angle

##################################################################################

def main(argv):
	help_msg="Computes the elevation and azimuth of a star in La Silla and compare to wind-a: right ascension (Ex.: 21h57m06.2s)\n-d: declination (Ex.: 20d44m52s)\n-n UTC date (optional - if empty current time, Ex.: 2014-01-02)\n-t: time in UTC (optional - if empty current time, Ex.: 02:03:45)\n-w turn on/off wind comparison (optional, default: True)\nMinimum working command:\npython Azimuth.py -a 0h02m3.17s -d -08d50m36.87s"
	alpha=None
	delta=None
	night=None
	otime=None
	wind=True
	try:
		opts, args = getopt.getopt(argv,"ha:d:n:t:w:",)
	except getopt.GetoptError:
		print help_msg
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print help_msg
			sys.exit()
		elif opt in ("-a"):
			alpha = angles.Angle(arg)
		elif opt in ("-d"):
			delta = angles.Angle(arg)
		elif opt in ("-n"):
			night=arg
		elif opt in ("-t"):
			otime=arg
		elif opt in ("-w"):
			if arg=="False" or arg=="F" or arg=="false": wind=False
	if alpha == None or delta == None:
		print help_msg
		sys.exit(2)

	if otime==None and night==None:
		obs_time=Time.now()
	else:
		import time
		if night==None and not otime == None:
			night = time.strftime("%Y-%m-%d", time.gmtime(time.time()))
			obs_time=Time('%sT%s' % (night,otime), format='isot', scale='utc')
		elif not night==None and otime==None:
			otime = time.strftime("%H:%M:%S", time.gmtime(time.time()))
			obs_time=Time('%sT%s' % (night,otime), format='isot', scale='utc') 
		else:
			obs_time=Time('%sT%s' % (night,otime), format='isot', scale='utc') 


	if wind: WD,WS=get_wind()
	Az,Alt=get_AzAlt(alpha,delta,obs_time,ref_dir)

	print 'UTC time:\t%s' % obs_time
	print 'Azimuth star:\t', Az.to_string(unit=u.degree), '\t(Ref dir =', ref_dir,'deg)'
	msg = 'Elevation star:\t%s' % Alt.to_string(unit=u.degree)
	if Alt.degree < 0:
		print hilite(msg, False, True)
	else:
		print msg

	if not wind: exit()
	msg = "Wind speed:\t%2.1f m/s" % WS
	if WS >= 14.5:
		print hilite(msg, False, False)
		bold=True
	else:
		print hilite(msg, True, False)
		bold=False

	angle_to_wind = (Az.degree+ref_dir-WD)
	msg = "Angle to wind:\t%d deg" % angle_to_wind
	if abs(angle_to_wind) < 90:
		print hilite(msg, False, bold)
		if bold: print hilite('WARNING: This is dangerous!', False, bold)
	else:
		print hilite(msg, True, False)

if __name__=="__main__":
	main(sys.argv[1:])


