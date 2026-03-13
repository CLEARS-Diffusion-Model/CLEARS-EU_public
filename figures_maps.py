# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 10:07:37 2025

@author: hartv
"""


# Standard library imports
import copy
import os
import sys
import copy

# Third party imports
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.axes as ax
import seaborn as sns

# Local library imports
import source_code.paths_append
from model_class import ModelRun


wd = os.path.dirname(os.path.abspath(__file__))
os.chdir(wd)


print('Start')

# Instantiate the run
model = ModelRun()

print('Initiated')

# Fetch ModelRun attributes, for examination
# Titles of the model
titles = model.titles
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
version = 'Dev1'

results = dict()

scens = [f.split('.')[0] for f in os.listdir('output') if version in f]
scen_names = dict()

for f in scens:
    sc = f.replace('_' + version, '')
    if sc == 'baseline':
        sc = 'Self-cons.'
    if sc == 'peak':
        sc = 'Peak'
    if sc == 'dyn':
        sc = 'Dynamic'
    if sc == 'flex':
        sc = 'FlexPool'
    
    scen_names[f] = sc
    


for scen in scens:

    filename = "output/{}.pickle".format(scen)
    
    # open and load
    with open(filename, "rb") as f:
        results[scen] = pickle.load(f)

# colourmap = 'gnuplot'
colourmap = 'turbo'
cmap = matplotlib.colormaps.get_cmap('turbo')

# plt.style.use('seaborn-darkgrid')
csfont = {'fontname':'Cambria'}
plt.rcParams["font.family"] = "Cambria"
plt.rcParams["figure.dpi"] = 500
plt.rcParams.update({'font.size': 12})

import matplotlib.colors as mcolors
own_cmap = mcolors.LinearSegmentedColormap.from_list(
    "vibrant_red_yellowgreen",
    [
        "#C50102",   # deep red
        "#FF3B00",   # bright orange-red
        "#FFEA00",   # vivid yellow
        "#BFFF00",   # bright lime
        "#A0FF54"
    ],
    N=256
)

import geopandas as gpd
import matplotlib.pyplot as plt
plt.rcParams.update({
    'font.size': 9  # Change this value as needed (e.g., 10, 14, etc.)
})
eu_map = gpd.read_file('figures//NUTS_RG_60M_2024_3035.shp')
eu_map = eu_map.dissolve(by='CNTR_CODE').loc[list(titles['country_short'])]
eu_map.plot()
baseline_scen = 'baseline_' + version
plt.rcParams["font.family"] = "Cambria"
plt.rcParams["font.size"] = 12
plot_map = eu_map.copy()
elec_p = pd.Series(data['electricity_price'][:, 1, 0, 0, 0, 0, 0], index = titles['country_short'])
plot_map['Electricity price'] = elec_p
load = pd.Series(data['load'][:, 0, 0, 0, 0, :, :].sum(axis = 1).sum(axis = 1), index = titles['country_short']) / 1000000
plot_map['Electricity demand'] = load
pv_gen = pd.Series(data['pv_gen'][:, 0, 0, 0, 0, :, :].sum(axis = 1).sum(axis = 1), index = titles['country_short']) / 1000
plot_map['PV generation'] = pv_gen
npv = pd.Series(results[baseline_scen]['battery_npv'][:, 2, 1, 0, 0, 0, 15], index = titles['country_short'])
plot_map['NPV'] = npv
hh_cons = pd.Series(results[baseline_scen]['consumption'][:, 0, 0, 0, 0, 0, 0], index = titles['country_short'])
plot_map['Household electricity consumption'] = hh_cons
plot_map = plot_map.drop(['MT', 'CY'])
figsize = (10.0, 8)

###############################################################################################################
# Electricity prices

ax = plot_map.plot(column="Electricity price", edgecolor="black", linewidth = 0.5, alpha = 0.7, cmap=own_cmap, 
                              vmin=0.1, vmax=0.4, legend=True, legend_kwds={"label": "EUR/kWh", "shrink": 0.8},
                              figsize=figsize)
# Get the colorbar axis (always the last axis in the figure)
cbar_ax = ax.get_figure().get_axes()[-1]

# Change font sizes
cbar_ax.set_ylabel("EUR", fontsize=16)   # colorbar label
cbar_ax.tick_params(labelsize=16)        # colorbar tick labels
# ax.set_xticks([16.2, 16.3, 16.4, 16.5, 16.6])
# ax.set_title('Electricity prices', fontsize=20, fontname="Calibri")
ax.set_xlim(2.6 * 10**6, 6.1 * 10**6)
ax.set_ylim(1.4 * 10**6, 4.66 * 10**6)
plt.axis('off')   # completely removes axis lines, ticks, and labels
# Add labels at centroid
for idx, row in plot_map.iterrows():
    x, y = row.geometry.centroid.x, row.geometry.centroid.y
    if idx == 'FI':
        y = y - 0.25 * 10**6
    if idx == 'FR':
        x = x + 0.9 * 10**6
        y = y + 0.25 * 10**6
    if idx == 'PT':
        x = x + 0.05 * 10**6
        y = y - 0.05 * 10**6
    if idx == 'SE':
        x = x - 0.05 * 10**6
    else:
        y = y - 0.05 * 10**6


    plt.text(x, y, idx, ha="center", fontsize=18)
# We can now plot our ``GeoDataFrame``.
# color_scale = [(0, 'blue'), (1,'black')]
# plot_map.plot(ax=ax, color = 'purple', linewidth = 0.25, alpha = 0.8)
plt.xlabel("")
plt.ylabel("")

plt.show()
ax.figure.savefig('figures/EU_electricity_prices.png', bbox_inches="tight", pad_inches=0.1, dpi = 500)

###############################################################################################################

# HH Electricity demand
ax = plot_map.plot(column="Household electricity consumption", edgecolor="black", linewidth = 0.5, alpha = 0.7, cmap=own_cmap, 
                              vmin=1500, vmax=7500, legend=True, legend_kwds={"label": "TWh", "shrink": 0.8},
                              figsize=figsize)
# Get the colorbar axis (always the last axis in the figure)
cbar_ax = ax.get_figure().get_axes()[-1]

# Change font sizes
cbar_ax.set_ylabel("kWh", fontsize=16)   # colorbar label
cbar_ax.tick_params(labelsize=16)        # colorbar tick labels
# ax.set_xticks([16.2, 16.3, 16.4, 16.5, 16.6])
# ax.set_title('Electricity demand', fontsize=20, fontname="Calibri")
ax.set_xlim(2.6 * 10**6, 6.1 * 10**6)
ax.set_ylim(1.4 * 10**6, 4.66 * 10**6)
plt.axis('off')   # completely removes axis lines, ticks, and labels
# Add labels at centroid
for idx, row in plot_map.iterrows():
    x, y = row.geometry.centroid.x, row.geometry.centroid.y
    if idx == 'FI':
        y = y - 0.25 * 10**6
    if idx == 'FR':
        x = x + 0.9 * 10**6
        y = y + 0.25 * 10**6
    if idx == 'PT':
        x = x + 0.05 * 10**6
        y = y - 0.05 * 10**6
    if idx == 'SE':
        x = x - 0.05 * 10**6
    else:
        y = y - 0.05 * 10**6


    plt.text(x, y, idx, ha="center", fontsize=18)
# We can now plot our ``GeoDataFrame``.
# color_scale = [(0, 'blue'), (1,'black')]
# plot_map.plot(ax=ax, color = 'purple', linewidth = 0.25, alpha = 0.8)
plt.xlabel("")
plt.ylabel("")

plt.show()
ax.figure.savefig('figures/EU_hh_electricity_consumption.png', bbox_inches="tight", pad_inches=0.1, dpi = 500)

###############################################################################################################

# Battery NPV

ax = plot_map.plot(column="NPV", edgecolor="black", linewidth = 0.5, alpha = 0.7, cmap=own_cmap, 
                              vmin=-2500, vmax=0, legend=True, legend_kwds={"label": "EUR", "shrink": 0.8},
                              figsize=figsize)
# Get the colorbar axis (always the last axis in the figure)
cbar_ax = ax.get_figure().get_axes()[-1]

# Change font sizes
cbar_ax.set_ylabel("EUR", fontsize=16)   # colorbar label
cbar_ax.tick_params(labelsize=16)        # colorbar tick labels
# ax.set_xticks([16.2, 16.3, 16.4, 16.5, 16.6])
# ax.set_title('Battery NPV', fontsize=20, fontname="Calibri")
ax.set_xlim(2.6 * 10**6, 6.1 * 10**6)
ax.set_ylim(1.4 * 10**6, 4.66 * 10**6)
plt.axis('off')   # completely removes axis lines, ticks, and labels
# Add labels at centroid
for idx, row in plot_map.iterrows():
    x, y = row.geometry.centroid.x, row.geometry.centroid.y
    if idx == 'FI':
        y = y - 0.25 * 10**6
    if idx == 'FR':
        x = x + 0.9 * 10**6
        y = y + 0.25 * 10**6
    if idx == 'PT':
        x = x + 0.05 * 10**6
        y = y - 0.05 * 10**6
    if idx == 'SE':
        x = x - 0.05 * 10**6
    else:
        y = y - 0.05 * 10**6


    plt.text(x, y, idx, ha="center", fontsize=18)
# We can now plot our ``GeoDataFrame``.
# color_scale = [(0, 'blue'), (1,'black')]
# plot_map.plot(ax=ax, color = 'purple', linewidth = 0.25, alpha = 0.8)
plt.xlabel("")
plt.ylabel("")

plt.show()
ax.figure.savefig('figures/EU_battery_NPV.png', bbox_inches="tight", pad_inches=0.1, dpi = 500)