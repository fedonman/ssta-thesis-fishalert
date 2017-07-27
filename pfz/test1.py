import netCDF4 as cdf
import numpy as np

data = cdf.Dataset('new.nc', 'w')
lon_data = data['lon'][:]
lat_data = data['lat'][:]
X = len(lat_data)
Y = len(lon_data)
anchovy_data = np.zeros((X, Y))
anchovy = data.createVariable('anchovy', np.dtype('float32'), ('lat', 'lon'), fill_value=-999, zlib=True, least_significant_digit=1)
anchovy.units = '%'
anchovy.long_name = 'Possibility of Fishing Zone'
anchovy.valid_range = np.array((0.0, 100.0))
anchovy[:] = anchovy_data[:]
data.close()