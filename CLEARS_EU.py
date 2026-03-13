# -*- coding: utf-8 -*-
"""
Created on Fri Dec 16 00:21:33 2022

@author: adh
"""

# Standard library imports
import copy
import os
import sys
import copy

wd = os.path.dirname(os.path.abspath(__file__))
os.chdir(wd)
# os.chdir("C:\\Users\\adh\\OneDrive - Cambridge Econometrics\\ADH CE\\Phd\\KDP_2023\\CLEARS_CEE")

# Third party imports
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
import itertools

# Local library imports
import source_code.paths_append
from model_class import ModelRun

print('Start')

# Instantiate the run
model = ModelRun()

print('Initiated')

# Fetch ModelRun attributes, for examination
# Titles of the model
titles = model.titles
scenario = model.scenario
run_id = model.name
# Dimensions of model variables
dims = model.dims
# Converters
converter = model.converter
# Data
data = model.data
# Timeline
timeline = model.timeline
# Set random seed
np.random.seed(123)
# Run model
model.run()

# Export results
results = copy.deepcopy(model.data)
    

print_vars = ['battery_benefit',
                'battery_cap_est',
                'battery_cum',
                'battery_investment',
                'battery_new',
                'battery_npv',
                'battery_p',
                'battery_potential_pop',
                'battery_potential_pop_share',
                'battery_price',
                'battery_q',
                'battery_scrap',
                'battery_specs',
                'charge',
                'charge_level',
                'charge_total',
                'consumption',
                'consumption_adj',
                'discharge',
                'discharge_total',
                'electricity_price',
                'feed_in_tariff',
                'hh_nr',
                'hh_share',
                'hh_total',
                'labour_cost',
                'ldc',
                'owner_share',
                'peak_h',
                'peak_participation',
                'potential_pop_share',
                'vat']
out = {}

for var in print_vars:
    if 'timeline' in dims[var]:
        out[var] = results[var][:, :, :, :, :, :, 40].copy()
    else:
        out[var] = results[var][:, :, :, :, :, :, :].copy()
        
with open("output/{0}_{1}.pickle".format(scenario, run_id), 'wb') as f:
    pickle.dump(out,f)