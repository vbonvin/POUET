#===================================================================================================
# Program Lens
#===================================================================================================

# Set general constraints
# If those numbers are object dependent, set to None and compute in observability function
minangletomoon = 30
maxairmass = 1.5

# If there is a common exptime, otherwise define a get_exptime function below
exptime = 5*360

#===================================================================================================
# Now define the exptime function, arguments must be : attributes and obs_time
#===================================================================================================
def get_exptime(attributes, obs_time): # Just to have some fun
	return 600.

#===================================================================================================
# Now define the observable function, arguments must be : obj and obs_time; should return 1 if 
# observable, 0 otherwise
# Already checked in the observable class: angle to moon, wind, clouds, airmass
# So this gives the possibility to have more specific tests, like say the delta v with the moon
#===================================================================================================
def observability(attributes, obs_time):
	msg = '' # This could contain messages that justify the impossibility to observe
	warnings = '' # This contains warnings
	
	return 1, msg, warnings
