#from __future__ import print_function
import fuzzifier as fz

print('Initializing fuzzifier...')

fuzz = fz.Fuzzifier('collocate_depth_chl_sst_sla.nc', fz.Season.Summer, fz.Fishery.Anchovy)

print('Running fuzzy algorithm...')

fuzz.run()

print('Fuzzy algorithm completed...')
print('Writing results to {0}...'.format('anchovy.nc'))

fuzz.writeData()

print('Results written successfully')