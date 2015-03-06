"""
Useful functions and definitions
"""
from numpy import sin, cos, arctan2, tan, deg2rad, floor, arcsin
import astropy.coordinates.angles as angles
from astropy.time import Time
from astropy import units as u
import urllib2
import re
import getopt, sys


# La Silla Telescope Parameters
def get_telescope_params():
	# LaSilla
	lat=angles.Angle("-29d15m33.7s")
	lon=angles.Angle("-70.7313d")
	elev = 2400

	return lat, lon, elev

def get_AzAlt(alpha, delta, obs_time=Time.now(), ref_dir=0):

	"""
	idea from http://aa.usno.navy.mil/faq/docs/Alt_Az.php

	Compute the azimuth and altitude of a souce at a given time (by default current time of execution), given its alpha and delta coordinates.

	WARNING ! Azimuth and altitude are computed at La Silla Observatory

	"""

	lat, lon, elev = get_telescope_params()

	# Untouched code from Azimuth.py
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

	# I changed this to get the same angle as the edp, using 0 (North) as reference
	if Az.degree < 0:
		Az+=angles.Angle(360, unit="degree")

	return Az, Alt



def reformat(coordinate, format):
	"""
	Transform a coordinate (hour, degree) in the format of your choice

	HHhDDdSSs <---> HH:DD:SS
	"""

	if 'm' in coordinate:
		if 'd' in coordinate:
			hd = coordinate.split('d')[0]
			m = coordinate.split('d')[1].split('m')[0]
		if 'h' in coordinate:
			hd = coordinate.split('h')[0]
			m = coordinate.split('h')[1].split('m')[0]
		s  = coordinate.split('m')[1].split('s')[0]

	elif ':' in coordinate:
		[hd, m, s] = coordinate.split(':')

	else:
		raise ValueError("%s, Unknown coordinate input format!" %coordinate)

	if format == 'numeric':
		return "%s:%s:%s" %(hd,m,s)

	elif format == 'alphabetic_degree':
		return "%sd%sm%ss" %(hd,m,s)

	elif format == 'alphabetic_hour':
		return "%sh%sm%ss" %(hd,m,s)

	else:
		raise ValueError("%s, Unknown coordinate output format!" %format)
