# -*- coding: utf-8 -*-
"""
Created on Fri Jan 19 13:54:29 2024

@author: adh
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
# Local library imports
import source_code.paths_append
from model_class import ModelRun
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.axes as ax
import seaborn as sns

import itertools

# Local library imports
import source_code.paths_append
from model_class import ModelRun


wd = os.path.dirname(os.path.abspath(__file__))
os.chdir(wd)
# os.chdir("C:\\Users\\adh\\OneDrive - Cambridge Econometrics\\ADH CE\\Phd\\KDP_2023\\CLEARS_CEE")




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


# run_id = 'Dev1'
# with open('output\{}.pickle'.format(run_id), 'wb') as f:
#     model = pickle.load(f)

filename = "output/smoothed_Dev1.pickle"

# open and load
with open(filename, "rb") as f:
    results = pickle.load(f)
    
filename = "output/baseline_Dev1.pickle"

# open and load
with open(filename, "rb") as f:
    results0 = pickle.load(f)
    

filename = "output/peak_Dev1.pickle"

# open and load
with open(filename, "rb") as f:
    results1 = pickle.load(f)


# colourmap = 'gnuplot'
colourmap = 'turbo'
cmap = matplotlib.colormaps.get_cmap('turbo')

# plt.style.use('seaborn-darkgrid')
csfont = {'fontname':'Times New Roman'}
# plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["figure.dpi"] = 500
# plt.rcParams.update({'font.size': 12})
plt.rcParams["font.family"] = "Calibri"
plt.rcParams["font.size"] = 12
summer_idx = list(range(151, 243))
summer = titles['date'][151:243]
winter_idx = list(range(0, 59)) + list(range(334, 365))
winter = titles['date'][0:59] + titles['date'][334:365]
off_season_idx = list(range(59, 151)) + list(range(243, 334))
off_season = titles['date'][59:151] + titles['date'][243:334]

########################################################################################
##################################### Peak hours. ######################################
########################################################################################

fn = "Peak_h_2050.jpg"
fp = os.path.join('figures', fn)

filtered_cty = tuple(x for x in titles['country'] if x not in ['Cyprus', 'Malta'])
filtered_cty_idx = [titles['country'].index(cty) for cty in filtered_cty]

# Peak hours in Peak scenario

peak_h = results1['peak_h'][filtered_cty_idx, :, 0, 0, 0, 0]
# Flatten the array to 1D
peak_h_flat = peak_h.flatten()

# Count occurrences for each hour 0-23
hours = np.arange(24)
counts = np.array([np.sum(peak_h_flat == h) for h in hours])
peak_occurances = pd.Series(counts, index = hours)
colors = cmap(0.7 + (counts / counts.max()) / 7)

# Plot
plt.figure(figsize=(8, 5))
plt.bar(hours, counts, color=colors)
plt.xticks(hours)
plt.xlabel("Hours", fontsize=12)
plt.ylabel("Occurrences of Peak Hours Across Countries", fontsize=12)
# plt.title("Occurrences of Peak Hours Across Countries")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout(pad=1, rect=[0, 0, 0.91, 1])
plt.savefig(fp)
plt.show()





######################################################################
################################ LDC ################################
######################################################################

fn = "LDC_EU_boxplot_2050.jpg"
fp = os.path.join('figures', fn)

# Figure size
figsize = (7.5, 5.625)
fig, ax = plt.subplots(figsize=figsize)

colors = [cmap(0), cmap(70), cmap(180), cmap(250)]
filtered_cty = tuple(x for x in titles['country'] if x not in ['Cyprus', 'Malta'])
filtered_cty_idx = [titles['country'].index(cty) for cty in filtered_cty]



data = []
labels = []
color_list = []

for c, var in enumerate(['Self-consumption', 'Peak', 'Smoothed'], start=1):
    if var == 'Smoothed':
        ldc = results['ldc'][filtered_cty_idx, 0, 0, 0, :, :].sum(axis=0)
    elif var == 'Self-consumption':
        ldc = results0['ldc'][filtered_cty_idx, 0, 0, 0, :, :].sum(axis=0)
    elif var == 'Peak':
        ldc = results1['ldc'][filtered_cty_idx, 0, 0, 0, :, :].sum(axis=0)

    ldc = ldc.flatten() / 1000  # Convert to GW
    data.append(ldc)
    labels.append(var)
    color_list.append(colors[c])

# --- Boxplot ---
box = ax.boxplot(
    data,
    patch_artist=True,
    labels=labels,
    showfliers=True,  # show dots for outliers
    flierprops=dict(marker='o', markersize=4, markerfacecolor='gray', alpha=0.5)
)

# Color boxes
for patch, color in zip(box['boxes'], color_list):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)

# Calculate overall limits and add margin
all_vals = np.concatenate(data)
ymin, ymax = np.min(all_vals), np.max(all_vals)
yrange = ymax - ymin
ax.set_ylim(ymin - 0.05 * yrange, ymax + 0.1 * yrange)  # add 20% headroom

# Add extra horizontal space by setting x-axis limits
num_boxes = len(data)
ax.set_xlim(0.5, num_boxes + 0.7)  # adds 0.5 padding on both side

# Annotate min, median, and max only
for i, vals in enumerate(data, start=1):
    min_val = np.min(vals)
    max_val = np.max(vals)
    median_val = np.median(vals)

    ax.text(i + 0.17, min_val, f"min: {min_val:.1f}", va='bottom', ha='left', fontsize=10, color='#555555')
    ax.text(i + 0.17, median_val, f"med: {median_val:.1f}", va='center', ha='left', fontsize=10, color='black')
    ax.text(i + 0.17, max_val, f"max: {max_val:.1f}", va='top', ha='left', fontsize=10, color='#555555')

# Axis labels and grid
ax.set_ylabel("Load (GW)")
# ax.set_title("Load Duration Curves – Distribution by Scenario")
ax.grid(axis='y', color='grey', alpha=0.4, linestyle='--', linewidth=0.5)

# Adjust layout and save
fig.subplots_adjust(bottom=0.2, left=0.15, right=0.9, top=0.9)
fig.savefig(fp, bbox_inches='tight', dpi=300)
plt.show()




########################################################################################
################################ System impacts in 2050 ################################
########################################################################################


fn = "Total_system_impact_2050_EU.jpg"
fp = os.path.join('figures', fn)



# Figure size
figsize = (7, 5)
# Create subplot
fig, axes = plt.subplots(nrows=2, ncols=1,
                         figsize=figsize,
                         sharex=True, sharey=True)



# colors = ["green", "black", "firebrick", "gray", "blue", "aqua", "red", "orange", "magenta", "navy", "tan", "maroon", "peru", "olive", "khaki"]
line_info  = {}

colors = ['#C5446E', '#49C9C5', '#AAB71D']#, '#009FE3', '#909090']
colors = [cmap(0), cmap(80), cmap(180), cmap(250)]
filtered_cty = tuple(x for x in titles['country'] if x not in ['Cyprus', 'Malta'])
filtered_cty_idx = [titles['country'].index(cty) for cty in filtered_cty]
f = 0
row = -1
for s in ['summer', 'winter']:
    c = 1
    row += 1
    if s == 'summer':
        s_idx = summer_idx
    else:
        s_idx = winter_idx

    for var in ['Self-consumption', 'Peak', 'Smoothed']:
    
        # Set color
        colour = colors[c]
        c += 1
        # Set line style
        linestyle = '-'
        if var == 'Smoothed':
            reg_discharge = results['discharge_total'][:, :, :, :, s_idx, :].sum(axis = 1).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000
            reg_charge = results['charge_total'][:, :, :, :, s_idx, :].sum(axis = 1).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000
            reg_output = (- reg_charge + reg_discharge).mean(axis = 0) / 1000
        if var == 'Self-consumption':
            reg_discharge = results0['discharge_total'][:, :, :, :, s_idx, :].sum(axis = 1).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000
            reg_charge = results0['charge_total'][:, :, :, :, s_idx, :].sum(axis = 1).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000
            reg_output = (- reg_charge + reg_discharge).mean(axis = 0) / 1000
        if var == 'Peak':
            reg_discharge = results1['discharge_total'][:, :, :, :, s_idx, :].sum(axis = 1).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000
            reg_charge = results1['charge_total'][:, :, :, :, s_idx, :].sum(axis = 1).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000
            reg_output = (- reg_charge + reg_discharge).mean(axis = 0) / 1000
        lbl = str(var)
    
        axes[row].plot(range(0, 24),
                  reg_output,
                  label=lbl,
                  color=colour,
                  linewidth=2,
                  linestyle=linestyle)
        # axes.set_title('EU', fontstyle='italic', fontsize=14)
    
        axes[row].set_xlim([0, 24]);
        # min_npv = results['battery_cum'][:, :, :, 1, 0, 0, 16:].min() - 200
        # max_npv = results['battery_cum'][:, :, :, 1, 0, 0, 16:].max() + 200
        # axes[row, col].set_ylim([-1, 1]);
        axes[row].grid(color = 'grey', alpha=0.4, linestyle = '--', linewidth = 0.5)
        axes[row].tick_params('x', labelrotation=60)
        # axes[row, col].label_outer()
        axes[row].set_xticks([0, 6, 12, 18, 24])

axes[0].set_ylabel("Summer")
axes[1].set_ylabel("Winter")
axes[1].set_xlabel("Hours")
fig.text(0.05, 0.55, "GW", va='center', rotation='vertical', fontsize=12)


h1, l1 = axes[0].get_legend_handles_labels()
# l1[4] = l1[4].split(' ')[0] + '\n' + l1[4].split(' ')[1]
handles = h1[1::2] + [h1[0]]
labels = l1
#labels[12] = labels[12].split(';')[0] + '\n' + labels[12].split(';')[1]

# l1 = [lab.split(';')[0]+'\n' +lab.split(';')[1] for lab in l1]
fig.subplots_adjust(hspace=0.3, wspace=0.3, right=0.75, bottom=0.25, left=0.17)
fig.legend(handles=h1,
           labels=l1,
           loc="lower center",
           bbox_to_anchor=(0.4605, 0),
           frameon=False,
           borderaxespad=0.,
           ncol=3,
           title="Scenario",
           fontsize=12)


# fig.tight_layout(pad=0.9, rect=[0, 0, 0, 1])
fig.savefig(fp, bbox_inches='tight', dpi=300)
plt.show()






########################################################################################
######################################### Maps #########################################
########################################################################################

import geopandas as gpd
import matplotlib.pyplot as plt
plt.rcParams.update({
    'font.size': 9  # Change this value as needed (e.g., 10, 14, etc.)
})
eu_map = gpd.read_file('figures//NUTS_RG_60M_2024_3035.shp')
eu_map = eu_map.dissolve(by='CNTR_CODE').loc[list(titles['country_short'])]
eu_map.plot()

plt.rcParams["font.family"] = "Calibri"
plt.rcParams["font.size"] = 12
plot_map = eu_map.copy()
elec_p = pd.Series(results0['electricity_price'][:, 1, 0, 0, 0, 0, 0], index = titles['country_short'])
plot_map['Electricity price'] = elec_p
# NPV in 2030
npv = pd.Series(results0['battery_npv'][:, 2, 1, 0, 0, 0], index = titles['country_short'])
plot_map['NPV'] = npv
hh_cons = pd.Series(results0['consumption'][:, 0, 0, 0, 0, 0, 0], index = titles['country_short'])
plot_map['Household electricity consumption'] = hh_cons
plot_map = plot_map.drop(['MT', 'CY'])
figsize = (10.0, 8)

#################################
# Electricity prices
#################################



ax = plot_map.plot(column="Electricity price", edgecolor="black", linewidth = 0.5, alpha = 0.7, cmap='cool', 
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
ax.figure.savefig('figures/EU_electricity_prices_2024.png', bbox_inches="tight", pad_inches=0.1, dpi = 500)



#################################
# HH Electricity demand
#################################



ax = plot_map.plot(column="Household electricity consumption", edgecolor="black", linewidth = 0.5, alpha = 0.7, cmap='cool', 
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
ax.figure.savefig('figures/EU_hh_electricity_consumption_2024.png', bbox_inches="tight", pad_inches=0.1, dpi = 500)


#################################
# Battery NPV
#################################


ax = plot_map.plot(column="NPV", edgecolor="black", linewidth = 0.5, alpha = 0.7, cmap='cool', 
                              vmin=-3000, vmax=3000, legend=True, legend_kwds={"label": "EUR", "shrink": 0.8},
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
ax.figure.savefig('figures/EU_battery_NPV_2050.png', bbox_inches="tight", pad_inches=0.1, dpi = 500)
