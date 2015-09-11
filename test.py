import obs, meteo, util
import time

prog = '714'
check_clouds = False

currentmeteo = meteo.Meteo(name='LaSilla', check_clouds=check_clouds)
time.sleep(1)

if prog == '703':
	observables = util.rdbimport('rdb/cat703.rdb', prog, col_name='code', col_alpha='alphacat', col_delta='deltacat')
elif prog == '714':
	observables = util.rdbimport('rdb/cat714.rdb', prog, col_name='refnocod', col_alpha='alphacat', col_delta='deltacat')
elif prog == 'bebop':
	bebop = 'BEBOP_Observing_Targets.xlsx'
	observables = util.excelimport(bebop, obsprogram=prog)
	
obs.showstatus(observables, currentmeteo, displayall=False, check_clouds=check_clouds)
