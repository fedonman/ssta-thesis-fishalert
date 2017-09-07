from __future__ import division
import os
import sys
import argparse
import netCDF4 as cdf
import numpy as np
import matplotlib.pyplot as plt
import skfuzzy as fuzz
from skfuzzy import control as control
from enum import Enum

Fishery = {
    'Anchovy': {
        'Seasons': ['Summer', 'Early Autumn', 'Late Autumn', 'Winter'],
        'Output File': 'Anchovy.nc'
    },
    'Sardine': {
        'Seasons': ['June', 'September', 'December'],
        'Output File': 'Sardine.nc'
    }
}

class Fuzzifier:
    def __init__(self, file):
        self.file = file
        self.setData(file)

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
        self.season = season
        self.fishery = fishery
        self.usedParameters = []
        self.antecedents = {}
        self.consequent = None
        self.rules = list()
        if fishery == 'Anchovy':
            self.outputParameter = 'anchovy'
            self.consequent = fuzz.control.Consequent(np.linspace(0, 100, 10), self.outputParameter)
            self.consequent['low'] = fuzz.trapmf(self.consequent.universe, [0, 0, 20, 30])
            self.consequent['medium'] = fuzz.trapmf(self.consequent.universe, [20, 30, 50, 60])
            self.consequent['high'] = fuzz.trapmf(self.consequent.universe, [50, 60, 80, 90])
            self.consequent['extreme'] = fuzz.trapmf(self.consequent.universe, [80, 90, 100, 100])
            if season == 'Summer':
                self.usedParameters = ['depth', 'sst', 'sla']
                
                self.antecedents['depth'] = fuzz.control.Antecedent(np.linspace(-5000, 0, 100), 'depth')
                self.antecedents['sst'] = fuzz.control.Antecedent(np.linspace(273, 310, 37), 'sst')
                self.antecedents['sla'] = fuzz.control.Antecedent(np.linspace(-1, 1, 20), 'sla')
                
                self.antecedents['depth']['deep'] = fuzz.trapmf(self.antecedents['depth'].universe, [-5000, -5000, -200, -100])
                self.antecedents['depth']['ideal'] = fuzz.trapmf(self.antecedents['depth'].universe, [-200, -100, 0, 0])

                self.antecedents['sst']['low'] = fuzz.trapmf(self.antecedents['sst'].universe, [273, 273, 285, 290])
                self.antecedents['sst']['ideal_1'] = fuzz.trapmf(self.antecedents['sst'].universe, [285, 290, 295, 297])
                self.antecedents['sst']['ideal_2'] = fuzz.trapmf(self.antecedents['sst'].universe, [295, 297, 298, 300])
                self.antecedents['sst']['high'] = fuzz.trapmf(self.antecedents['sst'].universe, [298, 300, 310, 310])

                self.antecedents['sla']['low'] = fuzz.trapmf(self.antecedents['sla'].universe, [-1, -1, -0.14, -0.12])
                self.antecedents['sla']['ideal_1'] = fuzz.trapmf(self.antecedents['sla'].universe, [-0.14, -0.12, -0.06, -0.04])
                self.antecedents['sla']['ideal_2'] = fuzz.trapmf(self.antecedents['sla'].universe, [-0.08, -0.06, -0.02, 0])
                self.antecedents['sla']['high'] = fuzz.trapmf(self.antecedents['sla'].universe, [-0.02, 0, 1, 1])

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['sla']['ideal_1'] & self.antecedents['sst']['ideal_1'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['ideal_2'] & self.antecedents['sst']['ideal_2'] & self.antecedents['depth']['ideal'])
                , self.consequent['extreme']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['sla']['low'] & self.antecedents['sst']['ideal_1'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['high'] & self.antecedents['sst']['ideal_1'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['ideal_2'] & self.antecedents['sst']['ideal_1'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['low'] & self.antecedents['sst']['ideal_2'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['high'] & self.antecedents['sst']['ideal_2'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['ideal_1'] & self.antecedents['sst']['ideal_2'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['ideal_1'] & self.antecedents['sst']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['ideal_1'] & self.antecedents['sst']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['ideal_2'] & self.antecedents['sst']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['ideal_2'] & self.antecedents['sst']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['ideal_1'] & self.antecedents['sst']['ideal_1'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['ideal_2'] & self.antecedents['sst']['ideal_2'] & self.antecedents['depth']['deep'])
                , self.consequent['high']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['sla']['low'] & self.antecedents['sst']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['low'] & self.antecedents['sst']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['high'] & self.antecedents['sst']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['high'] & self.antecedents['sst']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['sla']['low'] & self.antecedents['sst']['ideal_1'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['high'] & self.antecedents['sst']['ideal_1'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['ideal_2'] & self.antecedents['sst']['ideal_1'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['low'] & self.antecedents['sst']['ideal_2'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['high'] & self.antecedents['sst']['ideal_2'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['ideal_1'] & self.antecedents['sst']['ideal_2'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['ideal_1'] & self.antecedents['sst']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['ideal_1'] & self.antecedents['sst']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['ideal_2'] & self.antecedents['sst']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['ideal_2'] & self.antecedents['sst']['high'] & self.antecedents['depth']['deep'])
                , self.consequent['medium']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['sla']['low'] & self.antecedents['sst']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['low'] & self.antecedents['sst']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['high'] & self.antecedents['sst']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['sla']['high'] & self.antecedents['sst']['high'] & self.antecedents['depth']['deep'])    
                , self.consequent['low']))
            elif season == 'Early Autumn':
                self.usedParameters = ['depth', 'sla', 'chl']

                self.antecedents['depth'] = fuzz.control.Antecedent(np.linspace(-5000, 0, 100), 'depth')
                self.antecedents['sla'] = fuzz.control.Antecedent(np.linspace(-1, 1, 20), 'sla')
                self.antecedents['chl'] = fuzz.control.Antecedent(np.linspace(0, 30, 30), 'chl')

                self.antecedents['depth']['deep'] = fuzz.trapmf(self.antecedents['depth'].universe, [-5000, -5000, -360, -180])
                self.antecedents['depth']['ideal'] = fuzz.trapmf(self.antecedents['depth'].universe, [-360, -180, 0, 0])

                self.antecedents['sla']['low'] = fuzz.trapmf(self.antecedents['sla'].universe, [-1, -1, 0.03, 0.05])
                self.antecedents['sla']['ideal'] = fuzz.trapmf(self.antecedents['sla'].universe, [0.03, 0.05, 0.12, 0.14])
                self.antecedents['sla']['high'] = fuzz.trapmf(self.antecedents['sla'].universe, [0.12, 0.14, 1, 1])

                self.antecedents['chl']['low'] = fuzz.trapmf(self.antecedents['chl'].universe, [0, 0, 0.4, 0.5])
                self.antecedents['chl']['ideal'] = fuzz.trapmf(self.antecedents['chl'].universe, [0.4, 0.5, 7.4, 7.5])
                self.antecedents['chl']['high'] = fuzz.trapmf(self.antecedents['chl'].universe, [7.4, 7.5, 30, 30])

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['chl']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal'])
                , self.consequent['extreme']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['chl']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep'])
                , self.consequent['high']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['chl']['low'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep'])
                , self.consequent['medium']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['chl']['low'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep'])    
                , self.consequent['low']))
            elif season == 'Late Autumn':
                self.usedParameters = ['depth', 'sst', 'sla', 'chl']
                
                self.antecedents['depth'] = fuzz.control.Antecedent(np.linspace(-5000, 0, 100), 'depth')
                self.antecedents['sst'] = fuzz.control.Antecedent(np.linspace(273, 310, 37), 'sst')
                self.antecedents['sla'] = fuzz.control.Antecedent(np.linspace(-1, 1, 20), 'sla')
                self.antecedents['chl'] = fuzz.control.Antecedent(np.linspace(0, 30, 30), 'chl')
                
                self.antecedents['depth']['deep'] = fuzz.trapmf(self.antecedents['depth'].universe, [-5000, -5000, -300, -150])
                self.antecedents['depth']['ideal'] = fuzz.trapmf(self.antecedents['depth'].universe, [-300, -150, 0, 0])

                self.antecedents['sst']['low'] = fuzz.trapmf(self.antecedents['sst'].universe, [273, 273, 288, 290])
                self.antecedents['sst']['ideal'] = fuzz.trapmf(self.antecedents['sst'].universe, [288, 290, 292, 294])
                self.antecedents['sst']['high'] = fuzz.trapmf(self.antecedents['sst'].universe, [292, 294, 310, 310])

                self.antecedents['sla']['low'] = fuzz.trapmf(self.antecedents['sla'].universe, [-1, -1, -0.3, -0.05])
                self.antecedents['sla']['ideal'] = fuzz.trapmf(self.antecedents['sla'].universe, [-0.03, -0.05, 0.05, 0.07])
                self.antecedents['sla']['high'] = fuzz.trapmf(self.antecedents['sla'].universe, [0.05, 0.07, 1, 1])

                self.antecedents['chl']['low'] = fuzz.trapmf(self.antecedents['chl'].universe, [0, 0, 0.26, 0.36])
                self.antecedents['chl']['ideal'] = fuzz.trapmf(self.antecedents['chl'].universe, [0.26, 0.36, 2, 2.1])
                self.antecedents['chl']['high'] = fuzz.trapmf(self.antecedents['chl'].universe, [2, 2.1, 30, 30])

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal'])
                    , self.consequent['extreme']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep'])
                    , self.consequent['high']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep'])
                    , self.consequent['medium']))
                self.ruls.append(fuzz.control.Rule(
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['depth']['deep'])
                    , self.consequent['low']))
            elif season == 'Winter':
                self.usedParameters = ['depth', 'sst', 'chl']
                
                self.antecedents['depth'] = fuzz.control.Antecedent(np.linspace(-5000, 0, 100), 'depth')
                self.antecedents['sst'] = fuzz.control.Antecedent(np.linspace(273, 310, 37), 'sst')
                self.antecedents['chl'] = fuzz.control.Antecedent(np.linspace(0, 30, 30), 'chl')
                
                self.antecedents['depth']['deep'] = fuzz.trapmf(self.antecedents['depth'].universe, [-5000, -5000, -120, -60])
                self.antecedents['depth']['ideal'] = fuzz.trapmf(self.antecedents['depth'].universe, [-120, -60, 0, 0])

                self.antecedents['sst']['low'] = fuzz.trapmf(self.antecedents['sst'].universe, [273, 273, 279, 281])
                self.antecedents['sst']['ideal'] = fuzz.trapmf(self.antecedents['sst'].universe, [279, 281, 287, 289])
                self.antecedents['sst']['high'] = fuzz.trapmf(self.antecedents['sst'].universe, [287, 289, 310, 310])

                self.antecedents['chl']['low'] = fuzz.trapmf(self.antecedents['chl'].universe, [0, 0, 0.8, 0.9])
                self.antecedents['chl']['ideal'] = fuzz.trapmf(self.antecedents['chl'].universe, [0.8, 0.9, 5.4, 5.5])
                self.antecedents['chl']['high'] = fuzz.trapmf(self.antecedents['chl'].universe, [5.4, 5.5, 30, 30])

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['depth']['ideal'])
                , self.consequent['extreme']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['ideal'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['depth']['deep'])
                , self.consequent['high']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['low'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['high'] & self.antecedents['depth']['ideal']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['ideal'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['depth']['deep'])
                , self.consequent['medium']))
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['low'] & self.antecedents['sst']['high'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['low'] & self.antecedents['depth']['deep']) |
                    (self.antecedents['chl']['high'] & self.antecedents['sst']['high'] & self.antecedents['depth']['deep'])    
                , self.consequent['low']))
        elif fishery == 'Sardine':
            self.outputParameter = 'sardine'
            self.consequent = fuzz.control.Consequent(np.linspace(0, 100, 10), self.outputParameter)
            self.consequent['low'] = fuzz.trapmf(self.consequent.universe, [0, 0, 20, 30])
            self.consequent['medium'] = fuzz.trapmf(self.consequent.universe, [20, 30, 50, 60])
            self.consequent['high'] = fuzz.trapmf(self.consequent.universe, [50, 60, 80, 90])
            self.consequent['extreme'] = fuzz.trapmf(self.consequent.universe, [80, 90, 100, 100])
            if season == 'June':
                self.usedParameters = ['depth', 'sst', 'sla', 'chl']
                
                self.antecedents['depth'] = fuzz.control.Antecedent(np.linspace(-5000, 0, 100), 'depth')
                self.antecedents['sst'] = fuzz.control.Antecedent(np.linspace(273, 310, 37), 'sst')
                self.antecedents['sla'] = fuzz.control.Antecedent(np.linspace(-1, 1, 20), 'sla')
                
                self.antecedents['depth']['deep'] = fuzz.trapmf(self.antecedents['depth'].universe, [-5000, -5000, -80, -65])
                self.antecedents['depth']['ideal'] = fuzz.trapmf(self.antecedents['depth'].universe, [-80, -65, 0, 0])

                self.antecedents['sst']['ideal'] = fuzz.trapmf(self.antecedents['sst'].universe, [273, 273, 290, 295])
                self.antecedents['sst']['high'] = fuzz.trapmf(self.antecedents['sst'].universe, [290, 295, 310, 310])

                self.antecedents['sla']['low_1'] = fuzz.trapmf(self.antecedents['sla'].universe, [-1, -1, -0.12, -0.1])
                self.antecedents['sla']['ideal_1'] = fuzz.trapmf(self.antecedents['sla'].universe, [-0.12, -0.1, -0.04, -0.02])
                self.antecedents['sla']['high_1'] = fuzz.trapmf(self.antecedents['sla'].universe, [-0.04, -0.02, 1, 1])
                self.antecedents['sla']['low_2'] = fuzz.trapmf(self.antecedents['sla'].universe, [-1, -1, -0.05, -0.03])
                self.antecedents['sla']['ideal_2'] = fuzz.trapmf(self.antecedents['sla'].universe, [-0.05, -0.03, 0, 0.02])
                self.antecedents['sla']['high_2'] = fuzz.trapmf(self.antecedents['sla'].universe, [0.02, 0.04, 1, 1])

                self.antecedents['chl']['low_1'] = fuzz.trapmf(self.antecedents['chl'].universe, [0, 0, 0.06, 0.08])
                self.antecedents['chl']['ideal_1'] = fuzz.trapmf(self.antecedents['chl'].universe, [0.06, 0.08, 0.37,0.39])
                self.antecedents['chl']['high_1'] = fuzz.trapmf(self.antecedents['chl'].universe, [0.37, 0.39, 30, 30])
                self.antecedents['chl']['low_2'] = fuzz.trapmf(self.antecedents['chl'].universe, [0, 0, 0.98, 1])
                self.antecedents['chl']['ideal_2'] = fuzz.trapmf(self.antecedents['chl'].universe, [0.98, 1, 15, 15.2])
                self.antecedents['chl']['high_2'] = fuzz.trapmf(self.antecedents['chl'].universe, [15, 15.2, 30, 30])

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal_1'] & self.antecedents['chl']['ideal_1']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal_2'] & self.antecedents['chl']['ideal_2'])
                    , self.consequent['extreme']))
                
                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal_1'] & self.antecedents['chl']['low_1']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal_1'] & self.antecedents['chl']['high_1']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal_2'] & self.antecedents['chl']['low_2']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal_2'] & self.antecedents['chl']['high_2']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low_1'] & self.antecedents['chl']['ideal_1']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high_1'] & self.antecedents['chl']['ideal_1']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low_2'] & self.antecedents['chl']['ideal_2']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high_2'] & self.antecedents['chl']['ideal_2']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_1'] & self.antecedents['chl']['ideal_1']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_2'] & self.antecedents['chl']['ideal_2'])
                    , self.consequent['high']))

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_1'] & self.antecedents['chl']['low_1']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_1'] & self.antecedents['chl']['high_1']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_2'] & self.antecedents['chl']['low_2']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_2'] & self.antecedents['chl']['high_2']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low_1'] & self.antecedents['chl']['ideal_1']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high_1'] & self.antecedents['chl']['ideal_1']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low_2'] & self.antecedents['chl']['ideal_2']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high_2'] & self.antecedents['chl']['ideal_2']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_1'] & self.antecedents['chl']['ideal_1']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_2'] & self.antecedents['chl']['ideal_2'])
                    , self.consequent['medium']))

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_1'] & self.antecedents['chl']['low_1']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_1'] & self.antecedents['chl']['high_1']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_2'] & self.antecedents['chl']['low_2']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal_2'] & self.antecedents['chl']['high_2']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low_1'] & self.antecedents['chl']['ideal_1']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high_1'] & self.antecedents['chl']['ideal_1']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low_2'] & self.antecedents['chl']['ideal_2']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high_2'] & self.antecedents['chl']['ideal_2'])
                    , self.consequent['low']))
            elif season == 'September':
                self.usedParameters = ['depth', 'sst', 'sla', 'chl']
                
                self.antecedents['depth'] = fuzz.control.Antecedent(np.linspace(-5000, 0, 100), 'depth')
                self.antecedents['sst'] = fuzz.control.Antecedent(np.linspace(273, 310, 37), 'sst')
                self.antecedents['sla'] = fuzz.control.Antecedent(np.linspace(-1, 1, 20), 'sla')
                self.antecedents['chl'] = fuzz.control.Antecedent(np.linspace(0, 30, 30), 'chl')
                
                self.antecedents['depth']['deep'] = fuzz.trapmf(self.antecedents['depth'].universe, [-5000, -5000, -130, -110])
                self.antecedents['depth']['ideal'] = fuzz.trapmf(self.antecedents['depth'].universe, [-130, -110, 0, 0])

                self.antecedents['sst']['low'] = fuzz.trapmf(self.antecedents['sst'].universe, [273, 273, 291, 293])
                self.antecedents['sst']['ideal'] = fuzz.trapmf(self.antecedents['sst'].universe, [291, 293, 299, 301])
                self.antecedents['sst']['high'] = fuzz.trapmf(self.antecedents['sst'].universe, [299, 301, 310, 310])

                self.antecedents['sla']['low'] = fuzz.trapmf(self.antecedents['sla'].universe, [-1, -1, 0, 0.02])
                self.antecedents['sla']['ideal'] = fuzz.trapmf(self.antecedents['sla'].universe, [0, 0.02, 0.1, 0.12])
                self.antecedents['sla']['high'] = fuzz.trapmf(self.antecedents['sla'].universe, [0.1, 0.12, 1, 1])

                self.antecedents['chl']['low'] = fuzz.trapmf(self.antecedents['chl'].universe, [0, 0, 0.11, 0.13])
                self.antecedents['chl']['ideal'] = fuzz.trapmf(self.antecedents['chl'].universe, [0.11, 0.13, 1.49, 1.51])
                self.antecedents['chl']['high'] = fuzz.trapmf(self.antecedents['chl'].universe, [1.49, 1.51, 30, 30])

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['ideal'])
                    , self.consequent['extreme']))

                self.rules.append(fuzz.control.Rule(
                    self.antecedents['depth']['ideal'] & 
                    ((self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']) |
                    (self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['ideal']))
                    , self.consequent['high']))

                self.rules.append(fuzz.control.Rule(
                    self.antecedents['depth']['ideal'] &
                    ((self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['low']) |
                    (self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['low']) |
                    (self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['high']) |
                    (self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['high']) |
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']))
                    , self.consequent['medium']))
                self.rules.append(fuzz.control.Rule(
                    self.antecedents['depth']['deep'] & 
                    ((self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']) |
                    (self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['ideal']))
                    , self.consequent['medium']))

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['chl']['high'])
                    , self.consequent['low']))
            
            elif season == 'December':
                self.usedParameters = ['depth', 'sst', 'sla', 'chl']
                
                self.antecedents['depth'] = fuzz.control.Antecedent(np.linspace(-5000, 0, 100), 'depth')
                self.antecedents['sst'] = fuzz.control.Antecedent(np.linspace(273, 310, 37), 'sst')
                self.antecedents['sla'] = fuzz.control.Antecedent(np.linspace(-1, 1, 20), 'sla')
                self.antecedents['chl'] = fuzz.control.Antecedent(np.linspace(0, 30, 30), 'chl')
                
                self.antecedents['depth']['deep'] = fuzz.trapmf(self.antecedents['depth'].universe, [-5000, -5000, -110, -90])
                self.antecedents['depth']['ideal'] = fuzz.trapmf(self.antecedents['depth'].universe, [-110, -90, 0, 0])

                self.antecedents['sst']['low'] = fuzz.trapmf(self.antecedents['sst'].universe, [273, 273, 285, 287])
                self.antecedents['sst']['ideal'] = fuzz.trapmf(self.antecedents['sst'].universe, [285, 287, 290, 292])
                self.antecedents['sst']['high'] = fuzz.trapmf(self.antecedents['sst'].universe, [290, 292, 310, 310])

                self.antecedents['sla']['low'] = fuzz.trapmf(self.antecedents['sla'].universe, [-1, -1, -0.07, -0.05])
                self.antecedents['sla']['ideal'] = fuzz.trapmf(self.antecedents['sla'].universe, [-0.07, -0.05, 0, 0.02])
                self.antecedents['sla']['high'] = fuzz.trapmf(self.antecedents['sla'].universe, [0, 0.02, 1, 1])

                self.antecedents['chl']['low'] = fuzz.trapmf(self.antecedents['chl'].universe, [0, 0, 0.43, 0.45])
                self.antecedents['chl']['ideal'] = fuzz.trapmf(self.antecedents['chl'].universe, [0.43, 0.45, 4.5, 4.7])
                self.antecedents['chl']['high'] = fuzz.trapmf(self.antecedents['chl'].universe, [4.5, 4.7, 30, 30])

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['ideal'])
                    , self.consequent['extreme']))

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['ideal'])
                    , self.consequent['high']))

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['ideal'])
                    , self.consequent['medium']))

                self.rules.append(fuzz.control.Rule(
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['low'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['ideal'] & self.antecedents['sla']['high'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['chl']['ideal']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['low'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['deep'] & self.antecedents['sst']['high'] & self.antecedents['sla']['ideal'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['low'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['low'] & self.antecedents['sla']['high'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['low'] & self.antecedents['chl']['high']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['chl']['low']) |
                    (self.antecedents['depth']['ideal'] & self.antecedents['sst']['high'] & self.antecedents['sla']['high'] & self.antecedents['chl']['high'])
                    , self.consequent['low']))
            
    def run(self, season, fishery, verbose=True):
        self.setFuzzyRules(season, fishery)
        system = fuzz.control.ControlSystem(self.rules)
        simulation = fuzz.control.ControlSystemSimulation(system)
        self.results = np.zeros((self.X, self.Y))
        if verbose is True:
            print 'Generating PFZ...'
        for x in range(self.X):
            if verbose is True:
                sys.stdout.write('Progress: {:2.1%}\r'.format((x * self.Y) / self.PixelCount))
                sys.stdout.flush()
            for y in range(self.Y):
                data = { param:self.data[param].item(x,y) for param in self.usedParameters }
                if any(np.isnan(value) for value in data.values()):
                    self.results.itemset((x, y), -999)
                else:
                    for param, value in data.items():
                        simulation.input[param] = value
                    simulation.compute()
                    self.results.itemset((x, y), simulation.output[self.outputParameter])
        if verbose is True:
            print 'PFZ generated successfully.'

    def writeData(self, filename, verbose=True):
        if verbose is True:
            print 'Writing data to {0}'.format(filename)
        dsin = cdf.Dataset(self.file)
        dsout = cdf.Dataset(filename, 'w')
        for dname, the_dim in dsin.dimensions.items():
            dsout.createDimension(dname, len(the_dim))
        for v_name, varin in dsin.variables.items():
            if v_name == 'lat' or v_name == 'lon':
                outVar = dsout.createVariable(v_name, varin.datatype, varin.dimensions)
                outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})    
                outVar[:] = varin[:]
        
        var = dsout.createVariable(self.outputParameter, np.dtype('float32'), ('lat', 'lon'), fill_value=-999, zlib=True, least_significant_digit=1)
        var.units = '%'
        var.long_name = 'Possibility of {0} Fishing Zone'.format(self.fishery)
        var.valid_range = np.array((0.0, 100.0))
        var[:] = self.results[:]
        dsin.close()
        dsout.close()
        if verbose is True:
            print 'Data written successfully'

    def ViewMembershipRelationships(self, season, fishery):
        self.setFuzzyRules(season, fishery)
        system = fuzz.control.ControlSystem(self.rules)
        simulation = fuzz.control.ControlSystemSimulation(system)
        sst = np.linspace(273, 310, 100)
        #sla = np.linspace(-1, 1, 21)
        chl = np.linspace(0, 15, 100)
        x, y = np.meshgrid(sst, chl)
        z = np.zeros_like(x)

        vmin = 100
        vmax = 0
        # Loop through the system 21*21 times to collect the control surface
        for i in range(len(chl) - 1):
            for j in range(len(sst) - 1):
                simulation.input['sst'] = x[i, j]
                simulation.input['chl'] = y[i, j]
                simulation.input['depth'] = -30
                #print('{0}, {1}'.format(x[i,j], y[i,j]))
                simulation.compute()
                z[i, j] = simulation.output['anchovy']
                if z[i, j] >= vmax:
                    vmax = z[i, j]
                if z[i, j] <= vmin:
                    vmin = z[i, j]
                #self.consequent.view(sim=simulation)
        print '{0} - {1}'.format(vmin, vmax)

        # Plot the result in pretty 3D with alpha blending
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D  # Required for 3D plotting

        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')

        surf = ax.plot_surface(x, y, z, rstride=1, cstride=1, cmap='viridis',
                            linewidth=0.4, antialiased=True)

        cset = ax.contourf(x, y, z, zdir='z', offset=-2.5, cmap='viridis', alpha=0.5)
        cset = ax.contourf(x, y, z, zdir='x', offset=3, cmap='viridis', alpha=0.5)
        cset = ax.contourf(x, y, z, zdir='y', offset=3, cmap='viridis', alpha=0.5)

        ax.set_xlabel('SST')
        ax.set_ylabel('CHL')
        ax.set_zlabel('PFZ')
        ax.view_init(30, 200)
        plt.show()

    def printRules(self):
        for rule in self.rules:
            rule.view()
        fig = plt.figure(figsize=(8, 8))
        plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fuzzy algorithm for detecting PFZs in Mediterranean Sea')
    parser.add_argument('-i', '--input', help='path to input file')
    parser.add_argument('-o', '--output', help='path to output file')
    parser.add_argument('-s', '--season', help='the season')
    parser.add_argument('-f', '--fishery', help='the fishery')
    parser.add_argument("-v", "--verbose", help="enable verbose mode", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        print 'Initializing fuzzifier...'

    fuzzifier = Fuzzifier(args.input)

    if args.verbose:
        print 'Running fuzzy algorithm...'
    
    fuzzifier.run(args.season, args.fishery)

    if args.verbose:
        print 'Fuzzy algorithm completed...'
        print 'Writing results to {0}...'.format(args.output)

    fuzzifier.writeData()

    if args.verbose:
        print 'PFZ generation completed!'
