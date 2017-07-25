import os
import argparse
import netCDF4 as cdf
import numpy as np
import matplotlib.pyplot as plt
import skfuzzy as fuzz
from skfuzzy import control as control

import downloader

class Fuzzifier:
    def __init__(self, lon_data, lat_data, chl_data, sst_data, depth_data):
        self.lon_data = lon_data
        self.lat_data = lat_data
        self.chl_data = chl_data
        self.sst_data = sst_data
        self.depth_data = depth_data
        self.X = len(self.lat_data)
        self.Y = len(self.lon_data)
        self.chl = fuzz.control.Antecedent(np.linspace(0, 15, 10), 'chl')
        self.sst = fuzz.control.Antecedent(np.linspace(285, 295, 10), 'sst')
        self.depth = fuzz.control.Antecedent(np.linspace(-5000, 0, 10), 'depth')
        self.anchovy = fuzz.control.Consequent(np.linspace(0, 100, 10), 'anchovy')
        self.rules = list()

    def set(self, lon_data, lat_data, chl_data, sst_data, depth_data):
        self.lon_data = lon_data
        self.lat_data = lat_data
        self.chl_data = chl_data
        self.sst_data = sst_data
        self.depth_data = depth_data
        self.X = len(self.lat_data)
        self.Y = len(self.lon_data)

    def run(self):
        self.chl['low'] = fuzz.trapmf(self.chl.universe, [0, 0, 0.2, 0.5])
        self.chl['ideal'] = fuzz.trapmf(self.chl.universe, [0.2, 0.5, 5, 7.5])
        self.chl['high'] = fuzz.trapmf(self.chl.universe, [5, 7.5, 15, 15])

        self.sst['extreme_low'] = fuzz.trapmf(self.sst.universe, [285, 285, 286, 287])
        self.sst['low'] = fuzz.trapmf(self.sst.universe, [286, 287, 289, 290])
        self.sst['medium'] = fuzz.trapmf(self.sst.universe, [289, 290, 292, 293])
        self.sst['high'] = fuzz.trapmf(self.sst.universe, [292, 293, 295, 295])

        self.depth['deep'] = fuzz.trapmf(self.depth.universe, [-5000, -5000, -300, -200])
        self.depth['ideal'] = fuzz.trapmf(self.depth.universe, [-300, -200, 0, 0])

        self.anchovy['none'] = fuzz.trapmf(self.anchovy.universe, [0, 0, 20, 30])
        self.anchovy['low'] = fuzz.trapmf(self.anchovy.universe, [20, 30, 40, 50])
        self.anchovy['maybe'] = fuzz.trapmf(self.anchovy.universe, [40, 50, 60, 70])
        self.anchovy['high'] = fuzz.trapmf(self.anchovy.universe, [70, 80, 100, 100])

        self.rules = list()
        self.rules.append(fuzz.control.Rule(self.chl['low'], self.anchovy['low']))
        self.rules.append(fuzz.control.Rule(self.chl['ideal'], self.anchovy['maybe']))
        self.rules.append(fuzz.control.Rule(self.chl['high'], self.anchovy['maybe']))
        self.rules.append(fuzz.control.Rule(self.sst['extreme_low'], self.anchovy['low']))
        self.rules.append(fuzz.control.Rule(self.sst['low'], self.anchovy['high']))
        self.rules.append(fuzz.control.Rule(self.sst['medium'], self.anchovy['maybe']))
        self.rules.append(fuzz.control.Rule(self.sst['high'], self.anchovy['low']))
        self.rules.append(fuzz.control.Rule(self.chl['low'] & self.sst['high'], self.anchovy['none']))
        self.rules.append(fuzz.control.Rule(self.chl['ideal'] & self.sst['extreme_low'], self.anchovy['high']))
        self.rules.append(fuzz.control.Rule(self.chl['ideal'] & self.sst['low'] & self.depth['ideal'], self.anchovy['high']))
        self.rules.append(fuzz.control.Rule(self.chl['ideal'] & self.sst['low'] & self.depth['deep'], self.anchovy['maybe']))
        self.rules.append(fuzz.control.Rule(self.chl['high'] & self.sst['low'] & self.depth['ideal'], self.anchovy['high']))

        control = fuzz.control.ControlSystem(self.rules)
        simulation = fuzz.control.ControlSystemSimulation(control)
        anchovy_data = np.zeros((self.X, self.Y))
        for x in range(self.X):
            for y in range(self.Y):
                c = self.chl_data.item(x, y)
                s = self.sst_data.item(x, y)
                d = self.depth_data.item(x, y)
                if (c > 0 and s > 0 and d < 0):
                    simulation.input['chl'] = c
                    simulation.input['sst'] = s
                    simulation.input['depth'] = d
                    simulation.compute()
                    output = simulation.output['anchovy']
                    anchovy_data.itemset((x, y), output)
                else:
                    anchovy_data.itemset((x, y), -999)
        return anchovy_data

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fuzzy algorithm for detecting PFZs in Mediterranean Sea')
    parser.add_argument('-f', '--file', help='path to collocated file')
    parser.add_argument("-v", "--verbose", help="enable verbose mode", action="store_true")
    args = parser.parse_args()

    if not args.file:
        parser.error('Collocated data file required')
    else:
        if not os.path.isfile(args.file):
            parser.error('{0} is not a valid file'.format(args.chl))

    data = cdf.Dataset(args.file, 'r+')
    fuzzifier = Fuzzifier(data['lon'][:], data['lat'][:], data['CHL'][:, :], data['analysed_sst'][:, :], data['elevation'][:, :])

    if args.verbose:
        print 'Running fuzzy algorithm...'
    
    anchovy_data = fuzzifier.run()

    if args.verbose:
        print 'Fuzzy algorithm completed'
        print 'Writing results to {0}'.format(args.file)

    anchovy = data.createVariable('pfz_anchovy', np.dtype('float32'), ('lat', 'lon'), fill_value=-999, zlib=True, least_significant_digit=1)
    anchovy.units = '%'
    anchovy.long_name = 'Possibility of PFZ existance'
    anchovy.valid_range = np.array((0.0, 100.0))
    anchovy[:] = anchovy_data

    data.close()

    if args.verbose:
        print 'Results written'