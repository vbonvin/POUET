#===================================================================================================
# Program 703
#===================================================================================================

# Set general constraints
# If those numbers are object dependent, set to None and compute in observability function
minangletomoon = 20
maxairmass = 1.5

# If there is a common exptime, otherwise define a get_exptime function below
exptime = None

#===================================================================================================
# Now define the exptime function, arguments must be : obj and obs_time
#===================================================================================================
def get_exptime(obj, obs_time): # Just to have some fun
	flux = 10 ** (obj['mv'] / -2.5)
	return flux / 100. 

#===================================================================================================
# Now define the observable function, arguments must be : obj and obs_time; should return 1 if 
# observable, 0 otherwise
# Already checked in the observable class: angle to moon, wind, clouds, airmass
# So this gives the possibility to have more specific tests, like say the delta v with the moon
#===================================================================================================
def observability(obj, obs_time):
	msg = '' # This could contain messages that justify the impossibility to observe
	warnings = '' # This contains warnings
	
	return 1, msg, warnings
