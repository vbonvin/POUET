#===================================================================================================
# Program bebop
#===================================================================================================
# The next two lines are there to load the util module
import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import util

# Set general constraints
# If those numbers are object dependent, set to None and compute in observability function
minangletomoon = 70
maxairmass = 1.5

# If there is a common exptime, otherwise define a get_exptime function below
exptime = None

#===================================================================================================
# Now define the exptime function, arguments must be : obj and obs_time
#===================================================================================================
def get_exptime(obj, obs_time):
	# TODO: THIS IS NOT ALWAYS THE CASE, let's change this 
	exptime = 1800
	return exptime

#===================================================================================================
# Now define the observable function, arguments must be : obj and obs_time; should return 1 if 
# observable, 0 otherwise
# Already checked in the observable class: angle to moon, wind, clouds, airmass
# So this gives the possibility to have more specific tests, like say the delta v with the moon
#===================================================================================================
def observability(attributes, obs_time):
	# check the phases. time is obs_time
	msg = '' # This could contain messages that justify the impossibility to observe
	warnings = '' # This contains warnings
	observability = 1
	
	time = obs_time.mjd
	phase = util.takeclosest(attributes['phases'], 'phase', time)
	if phase['phase'] < 0.03 or phase['phase'] > 0.97:
		observability = 0
	msg += '\nPhase = %.2f' % phase['phase']  # we display the phase anyway
	
	return observability, msg, warnings
