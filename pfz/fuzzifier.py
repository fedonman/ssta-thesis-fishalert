#from __future__ import print_function
import os
import argparse
import netCDF4 as cdf
import numpy as np
import matplotlib.pyplot as plt
import skfuzzy as fuzz
from skfuzzy import control as control
from enum import Enum

class Season(Enum):
    Summer = 1
    EarlyAutumn = 2
    LateAutumn = 3
    Winter = 4

class Fishery(Enum):
    Anchovy = 1
    Sardine = 2

class Fuzzifier:
    def __init__(self, file, season, fishery):
        self.file = file
        self.season = season
        self.fishery = fishery
        self.setData(file)
        self.setFuzzyRules(season, fishery)

    def setData(self, file):
        self.data = {}
        data = cdf.Dataset(file, 'r+')
        self.data['lon'] = data['lon'][:]
        self.data['lat'] = data['lat'][:]
        self.data['chl'] = data['CHL'][:, :]
        self.data['sst'] = data['analysed_sst'][:, :]
        self.data['sla'] = data['sla'][:, :]
        self.data['depth'] = data['bathymetry'][:, :]
        self.X = len(self.data['lat'])
        self.Y = len(self.data['lon'])
        self.PixelCount = self.X * self.Y
        data.close()

    def setFuzzyRules(self, season, fishery):
        self.usedParameters = []
        self.antecedents = {}
        self.consequent = None
        self.rules = list()
        if fishery is Fishery.Anchovy:
            self.outputParameter = 'anchovy'
            self.consequent = fuzz.control.Consequent(np.linspace(0, 100, 10), 'anchovy')
            if season is Season.Summer:
                self.usedParameters = ['depth', 'sst', 'sla']
                
                self.antecedents['depth'] = fuzz.control.Antecedent(np.linspace(-5000, 0, 10), 'depth')
                self.antecedents['sst'] = fuzz.control.Antecedent(np.linspace(280, 310, 10), 'sst')
                self.antecedents['sla'] = fuzz.control.Antecedent(np.linspace(-1, 1, 10), 'sla')
                
                self.antecedents['depth']['deep'] = fuzz.trapmf(self.antecedents['depth'].universe, [-5000, -5000, -200, -100])
                self.antecedents['depth']['ideal'] = fuzz.trapmf(self.antecedents['depth'].universe, [-200, -100, 0, 0])

                self.antecedents['sst']['low'] = fuzz.trapmf(self.antecedents['sst'].universe, [280, 280, 285, 290])
                self.antecedents['sst']['ideal_1'] = fuzz.trapmf(self.antecedents['sst'].universe, [285, 290, 295, 297])
                self.antecedents['sst']['ideal_2'] = fuzz.trapmf(self.antecedents['sst'].universe, [295, 297, 298, 300])
                self.antecedents['sst']['high'] = fuzz.trapmf(self.antecedents['sst'].universe, [298, 300, 310, 310])

                self.antecedents['sla']['low'] = fuzz.trapmf(self.antecedents['sla'].universe, [-1, -1, -0.14, -0.12])
                self.antecedents['sla']['ideal_1'] = fuzz.trapmf(self.antecedents['sla'].universe, [-0.14, -0.12, -0.06, -0.04])
                self.antecedents['sla']['ideal_2'] = fuzz.trapmf(self.antecedents['sla'].universe, [-0.08, -0.06, -0.02, 0])
                self.antecedents['sla']['high'] = fuzz.trapmf(self.antecedents['sla'].universe, [-0.02, 0, 1, 1])

                self.consequent['low'] = fuzz.trapmf(self.consequent.universe, [0, 0, 20, 30])
                self.consequent['medium'] = fuzz.trapmf(self.consequent.universe, [20, 30, 50, 60])
                self.consequent['high'] = fuzz.trapmf(self.consequent.universe, [50, 60, 80, 90])
                self.consequent['extreme'] = fuzz.trapmf(self.consequent.universe, [80, 90, 100, 100])

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['sst']['ideal_1'] & self.antecedents['sla']['ideal_1'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sst']['ideal_2'] & self.antecedents['sla']['ideal_2'] & self.antecedents['depth']['ideal'])
                    , self.consequent['extreme']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['sst']['ideal_1'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sst']['ideal_1'] & self.antecedents['sla']['ideal_2'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sst']['ideal_2'] & self.antecedents['sla']['ideal_1'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sst']['ideal_2'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['ideal_1'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_2'] & self.antecedents['depth']['ideal'])
                    , self.consequent['high']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['sst']['ideal_1'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sst']['ideal_2'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_1'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['ideal_2'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sst']['ideal_1'] & self.antecedents['sla']['ideal_1'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['ideal_2'] & self.antecedents['sla']['ideal_2'] & self.antecedents['depth']['deep'])
                    , self.consequent['medium']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['ideal_1'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['ideal_2'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['ideal_1'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['ideal_1'] & self.antecedents['sla']['ideal_2'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['ideal_1'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['ideal_2'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['ideal_2'] & self.antecedents['sla']['ideal_1'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['ideal_2'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_1'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_2'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep'])
                    , self.consequent['low']))

    def run(self, verbose=True):
        system = fuzz.control.ControlSystem(self.rules)
        simulation = fuzz.control.ControlSystemSimulation(system)
        self.results = np.zeros((self.X, self.Y))
        for x in range(self.X):
            if verbose is True:
                print('Progress {:2.1%}'.format((x * self.Y) / self.PixelCount), end='\r')
            for y in range(self.Y):
                data = { param:self.data[param].item(x,y) for param in self.usedParameters }
                #print(data)
                if any(np.isnan(value) for value in data.values()):
                    self.results.itemset((x, y), -999)
                else:
                    for param, value in data.items():
                        simulation.input[param] = value
                    simulation.compute()
                    self.results.itemset((x, y), simulation.output[self.outputParameter])
                '''
                for param in self.usedParameters:
                    data[param] = self.data['param'].item(x, y)
                #chl = self.chl_data.item(x, y)
                sst = self.sst_data.item(x, y)
                sla = self.sla_data.item(x, y)
                depth = self.depth_data.item(x, y)
                if np.isnan(sst) or np.isnan(sla) or np.isnan(depth):
                    self.anchovy_data.itemset((x, y), -999)
                else:
                    #simulation.input['chl'] = chl
                    simulation.input['sst'] = sst
                    simulation.input['sla'] = sla
                    simulation.input['depth'] = depth
                    simulation.compute()
                    output = simulation.output['anchovy']
                    self.anchovy_data.itemset((x, y), output)
                '''

    def writeData(self):
        outputFile = '{0}.nc'.format(self.outputParameter)
        dsin = cdf.Dataset(self.file)
        dsout = cdf.Dataset(outputFile, 'w')
        for dname, the_dim in dsin.dimensions.items():
            #print dname, len(the_dim)
            dsout.createDimension(dname, len(the_dim))
        for v_name, varin in dsin.variables.items():
            #print v_name
            if v_name == 'lat' or v_name == 'lon':
                outVar = dsout.createVariable(v_name, varin.datatype, varin.dimensions)
                #print varin.datatype
                # Copy variable attributes
                outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})    
                outVar[:] = varin[:]
        
        var = dsout.createVariable(self.outputParameter, np.dtype('float32'), ('lat', 'lon'), fill_value=-999, zlib=True, least_significant_digit=1)
        var.units = '%'
        var.long_name = 'Possibility of Fishing Zone'
        var.valid_range = np.array((0.0, 100.0))
        var[:] = self.results[:]
        dsin.close()
        dsout.close()

'''
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fuzzy algorithm for detecting PFZs in Mediterranean Sea')
    parser.add_argument('-f', '--file', help='path to collocated file')
    parser.add_argument("-v", "--verbose", help="enable verbose mode", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        print 'Initializing fuzzifier...'

    fuzzifier = Fuzzifier(args.file)

    if args.verbose:
        print 'Running fuzzy algorithm...'
    
    fuzzifier.run()

    if args.verbose:
        print 'Fuzzy algorithm completed...'
        print 'Writing results to {0}...'.format(args.file)

    fuzzifier.writeData()

    if args.verbose:
        print 'PFZ generation completed!'
'''