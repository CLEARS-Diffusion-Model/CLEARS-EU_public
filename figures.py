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
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.axes as ax
import matplotlib.patheffects as pe
import seaborn as sns
import itertools

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
    if sc == 'dynamic':
        sc = 'Dynamic'
    if sc == 'flex':
        sc = 'FlexPool'
    
    scen_names[f] = sc
    


for scen in scens:

    filename = "output/{}.pickle".format(scen)
    
    # open and load
    with open(filename, "rb") as f:
        results[scen] = pickle.load(f)





cap_est_base = (pd.DataFrame(results['baseline']['battery_cap_est'][:, :, :, 0, 0, 0, :].sum(axis = 1).sum(axis = 1), index = titles['country_short'], columns = timeline))
cap_est_dyn = (pd.DataFrame(results['dynamic']['battery_cap_est'][:, :, :, 0, 0, 0, :].sum(axis = 1).sum(axis = 1), index = titles['country_short'], columns = timeline))
cap_est_flex = (pd.DataFrame(results['flex']['battery_cap_est'][:, :, :, 0, 0, 0, :].sum(axis = 1).sum(axis = 1), index = titles['country_short'], columns = timeline))
cap_est_peak = (pd.DataFrame(results['peak']['battery_cap_est'][:, :, :, 0, 0, 0, :].sum(axis = 1).sum(axis = 1), index = titles['country_short'], columns = timeline))
cap_est = pd.DataFrame(0.0, index = list(titles['country_short']), columns = scen_names.values())
cap_est['Self-cons.'] = (cap_est_base[2050] / 1000).round(1)
cap_est['Dynamic'] = (cap_est_dyn[2050] / 1000).round(1)
cap_est['FlexPool'] = (cap_est_flex[2050] / 1000).round(2)
cap_est['Peak'] = (cap_est_peak[2050] / 1000).round(1)


cmap = plt.cm.jet

# plt.style.use('seaborn-darkgrid')
csfont = {'fontname':'Cambria'}
# plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["figure.dpi"] = 500
# plt.rcParams.update({'font.size': 12})
plt.rcParams["font.family"] = "Cambria"
plt.rcParams["font.size"] = 12





########################################################################################
##################################### Peak hours. ######################################
########################################################################################

fn = "Peak_h.jpg"
fp = os.path.join('figures', fn)
cmap = matplotlib.colormaps.get_cmap('turbo')

filtered_cty = tuple(x for x in titles['country'] if x not in ['Cyprus', 'Malta'])
filtered_cty_idx = [titles['country'].index(cty) for cty in filtered_cty]

# Peak hours in Peak scenario
peak_scen = 'peak' + version
peak_h = results[peak_scen]['peak_h'][filtered_cty_idx, :, 0, 0, 0, 0, 40]
# Flatten the array to 1D
peak_h_flat = peak_h.flatten()

# Count occurrences for each hour 0-23
hours = np.arange(24)
counts = np.array([np.sum(peak_h_flat == h) for h in hours])
peak_occurances = pd.Series(counts, index = hours)
colors = cmap(0.7 + (counts / counts.max()) / 7)

# Plot
plt.figure(figsize=(6.4, 4))
plt.bar(hours, counts, color=colors)
# plt.xticks(hours)
plt.xlabel("Hours", fontsize=12)
plt.ylabel("Occurrences of Peak Hours Across Countries", fontsize=12)
# plt.title("Occurrences of Peak Hours Across Countries")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout(pad=1, rect=[0, 0, 0.91, 1])
plt.savefig(fp)
plt.show()

########################################################################################
####################################### Diffusion ######################################
########################################################################################

# Bar plot in 2050

fn = "Battery_diff_reg_shares.jpg"
fp = os.path.join('figures', fn)

cmap = plt.cm.jet

filtered_cty = tuple(x for x in titles['country'] if x not in ['Cyprus', 'Malta'])
filtered_cty_idx = [titles['country'].index(cty) for cty in filtered_cty]

cty_mapping = {'Austria': 'Austria',
                 'Belgium': 'Other',
                 'Bulgaria': 'Other',
                 'Croatia': 'Other',
                 'Czechia': 'Czechia',
                 'Denmark': 'Other',
                 'Estonia': 'Other',
                 'Finland': 'Other',
                 'France': 'France',
                 'Germany': 'Germany',
                 'Greece': 'Other',
                 'Hungary': 'Other',
                 'Ireland': 'Other',
                 'Italy': 'Italy',
                 'Latvia': 'Other',
                 'Lithuania': 'Other',
                 'Luxembourg': 'Other',
                 'Netherlands': 'Netherlands',
                 'Poland': 'Poland',
                 'Portugal': 'Other',
                 'Romania': 'Other',
                 'Slovakia': 'Other',
                 'Slovenia': 'Other',
                 'Spain': 'Other',
                 'Sweden': 'Other'}
 
# MultiIndex columns: (Group, Stack)
years = timeline[15:]

colors = [cmap(i * 80) for i in range(7)]
colors = [cmap(0), cmap(80), cmap(170), cmap(230)]

colors_total = {scen_names[var]: colors[i] for i, var in enumerate(scens)}


agg_cty = ['Austria', 'Czechia', 'France', 'Germany', 'Italy', 'Netherlands', 'Poland', 'Other']
labs = ['Total-{}'.format(scen_names[var]) for var in scens] + agg_cty
# Create MultiIndex
multi_index = pd.MultiIndex.from_product(
    [agg_cty, years],
    names=["Country", "Year"]
)

f = -1
c = 0
battery_cap_dict = {}
for var in scens:
    scen_name = scen_names[var]
    battery_cap_dict[scen_name] = pd.DataFrame(results[var]['battery_cap_est'][filtered_cty_idx, 0, 0, 0, 0, 0, 15:], index = filtered_cty, columns = timeline[15:]).groupby(cty_mapping).sum().loc[agg_cty].values.flatten()
    
np.concatenate(list(battery_cap_dict.values()))
battery_barp = pd.DataFrame(np.stack(list(battery_cap_dict.values()), axis=0) / 1000,
                            index = battery_cap_dict.keys(), columns = multi_index)

battery_barp = battery_barp.reorder_levels(["Year", "Country"], axis=1)


# --- Parameters ---
years_bar = [2030, 2040, 2050]  
years_line = battery_barp.columns.levels[0]  
scenarios = battery_barp.index
countries = battery_barp.columns.levels[1]
figsize = (8, 5)

fig, ax = plt.subplots(figsize=figsize)

# --- Fixed colors for countries ---
colors = [cmap(i) for i in [0, 35, 70, 105, 140, 175, 215, 250]]

n_groups = len(scenarios)
width = 2

# Store bar center positions and labels
bar_centers = []
bar_labels = []

for i, scenario in enumerate(scenarios):
    bottom = np.zeros(len(years_bar))
    for j, country in enumerate(agg_cty[::-1]):
        values = [battery_barp.loc[scenario, (year, country)] for year in years_bar]
        pos = np.array(years_bar) + (i - (n_groups - 1) / 2) * width
        ax.bar(pos, values, width, bottom=bottom, color=colors[j % len(colors)],
               label=f"{country}" if i == 0 else None, zorder=2)
        bottom += values
    
    # Save bar centers and scenario labels
    bar_centers.extend(np.array(years_bar) + (i - (n_groups - 1)/2) * width)
    bar_labels.extend([scenario]*len(years_bar))

# --- Continuous total lines ---

# for scenario in scenarios:
#     df_scenario = battery_barp.loc[[scenario]]
#     totals = df_scenario.groupby(level="Year", axis=1).sum().iloc[0]
#     ax.plot(years_line, totals, color=colors_total[scenario], linestyle='--',
#             # linewidth=3, alpha=0.9, label=f"Total", zorder=3)
#             linewidth=3, alpha=0.9, label=f"Total-{scenario}", zorder=3)
    
for scenario in scenarios:
    df_scenario = battery_barp.loc[[scenario]]
    totals = df_scenario.groupby(level="Year", axis=1).sum().iloc[0]

    line, = ax.plot(
        years_line,
        totals,
        color=colors_total[scenario],
        linestyle='--',
        linewidth=3,
        alpha=0.9,
        label=f"Total-{scenario}",
        zorder=3
    )

    # Add outline
    line.set_path_effects([
        pe.Stroke(linewidth=5, foreground='black'),  # outline color
        pe.Normal()
    ])

# --- Axis styling ---
year_min, year_max = min(years_line), max(years_line)
bar_offset = (n_groups / 2) * width + 1
ax.set_xlim(year_min - 1, year_max + bar_offset)
ax.set_ylabel("Battery capacity (GWh)")
# ax.set_title("Diffusion of residential battery capacity by country and total (GWh)")

# Set year ticks at the center of each year group
ax.set_xticks(years_bar)
ax.set_xticklabels(years_bar, fontsize=11)

# Calculate y-position for scenario labels (a bit below 0)
y_min = ax.get_ylim()[0]  # current y-axis min
label_y = y_min - 0.08 * (ax.get_ylim()[1] - y_min)  # 5% below axis min

# Add scenario labels under each bar
for xc, lbl in zip(bar_centers, bar_labels):
    ax.text(xc, label_y, lbl, rotation=30, ha='right', va='top', fontsize=10)

# --- Legend ---
handles, labels = ax.get_legend_handles_labels()
order = [labels.index(l) for l in labs]
by_label = dict(zip(labels, handles))
ax.legend([handles[i] for i in order], [labels[i] for i in order], title="Country / Total",
          bbox_to_anchor=(1.05, 1), loc="upper left")



fig.tight_layout(pad=1, rect=[0, 0, 0.91, 1])
fig.savefig(fp, bbox_inches='tight', dpi=300)

plt.show()




######################################################################
################################ LDC #################################
######################################################################


fn = "LDC_EU_boxplot.jpg"
fp = os.path.join('figures', fn)

# Figure size
figsize = (7.5, 5.625)
fig, ax = plt.subplots(figsize=figsize)

colors = [cmap(i * 80) for i in range(7)]
colors = [cmap(0), cmap(80), cmap(170), cmap(240)]

filtered_cty = tuple(x for x in titles['country'] if x not in ['Cyprus', 'Malta'])
filtered_cty_idx = [titles['country'].index(cty) for cty in filtered_cty]



data = []
labels = []
color_list = []

for c, var in enumerate(scens):
    scen_name = scen_names[var]
    rldc = results[var]['ldc'][filtered_cty_idx, 0, 0, 0, :, :, 40].sum(axis=0)

    rldc = rldc.flatten() / 1000  # Convert to GW
    data.append(rldc)
    labels.append(scen_name)
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
    patch.set_alpha(0.8)

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

    ax.text(i + 0.23, min_val, f"min: {min_val:.1f}", va='bottom', ha='left', fontsize=9, color='#555555')
    ax.text(i + 0.23, median_val, f"med: {median_val:.1f}", va='center', ha='left', fontsize=9, color='black')
    ax.text(i + 0.23, max_val, f"max: {max_val:.1f}", va='top', ha='left', fontsize=9, color='#555555')

# Axis labels and grid
ax.set_ylabel("Load (GW)")
# ax.set_title("Load Duration Curves – Distribution by Scenario")
ax.grid(axis='y', color='grey', alpha=0.4, linestyle='--', linewidth=0.5)

# Adjust layout and save
fig.subplots_adjust(bottom=0.2, left=0.15, right=0.9, top=0.9)
fig.savefig(fp, bbox_inches='tight', dpi=300)
plt.show()




########################################################################################
######################################### NPV ##########################################
########################################################################################


################# NPV diff from baseline

year = 2024
yearidx = year - 2010

colors = [cmap(i * 80) for i in range(7)]
npv_avg = []
labels = []
color_list = []

for c, var in enumerate(scens):
    scen_name = scen_names[var]
    scen_npv_avg = np.mean(results[var]['battery_npv'][:, 2, 1, 0, 0, 0, yearidx])

    npv_avg.append(scen_npv_avg)
    labels.append(scen_name)

npv_avg_diff = npv_avg[1:] - npv_avg[0]
labels = labels[1:]


fn = "Battery_NPV_diff_{}.jpg".format(year)
fp = os.path.join('figures', fn)
figsize = (1.5, 3.75)

# Figure
fig, axes = plt.subplots(
    nrows=1,
    ncols=1,
    figsize=figsize,
    sharex=True, 
    sharey=True)

bar_width = 0.6
x = np.arange(len(npv_avg_diff))  # [0,1,2]


axes.bar(
    x,
    npv_avg_diff,
    color=colors[1:(len(npv_avg_diff) + 1)],
    width=bar_width,
    edgecolor='black'
)

axes.set_title('Δ NPV', fontsize=16)
# ax.set_ylim(min_npv, max_npv)
axes.grid(axis='y', linestyle='--', alpha=0.4)

axes.set_xticks(x)
axes.set_xticklabels(labels, rotation=30)
    
axes.axhline(
    y=0,
    color="black",
    linewidth=1.0,
    linestyle="--",
    alpha=0.8,
    zorder=0
)

# Y-axis labels
fig.text(
    1, 0.5,
    "Avg. difference from Self-cons. (EUR)",
    va="center",
    rotation="vertical",
    fontsize=14
)

# Legend
legend_handles = [
    plt.Rectangle((0, 0), 1, 1, color=colors[i], ec='black')
    for i in range(3)
]


fig.savefig(fp, dpi=150)
plt.show()




########################################################################################
################################ System impacts in 2050 ################################
########################################################################################


######################### EU


fn = "Total_system_impact_2050_EU.jpg"
fp = os.path.join('figures', fn)

summer_idx = list(range(151, 243))
summer = titles['date'][151:243]
winter_idx = list(range(0, 59)) + list(range(334, 365))
winter = titles['date'][0:59] + titles['date'][334:365]

# Figure size
figsize = (7, 5)
# Create subplot
fig, axes = plt.subplots(nrows=2, ncols=1,
                         figsize=figsize,
                         sharex=True, sharey=True)



# colors = ["green", "black", "firebrick", "gray", "blue", "aqua", "red", "orange", "magenta", "navy", "tan", "maroon", "peru", "olive", "khaki"]
line_info  = {}
colors = [cmap(i * 80) for i in range(7)]
colors = [cmap(0), cmap(80), cmap(175), cmap(240)]
filtered_cty = tuple(x for x in titles['country'] if x not in ['Cyprus', 'Malta'])
filtered_cty_idx = [titles['country'].index(cty) for cty in filtered_cty]
f = 0
row = -1
for s in ['summer', 'winter']:
    c = 0
    row += 1
    if s == 'summer':
        s_idx = summer_idx
    else:
        s_idx = winter_idx

    for var in scens:
        scen_name = scen_names[var]
        # Set color
        colour = colors[c]
        c += 1
        # Set line style
        linestyle = '-'

        reg_discharge = results[var]['discharge_total'][:, :, :, :, s_idx, :, 40].sum(axis = 1).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000
        reg_charge = results[var]['charge_total'][:, :, :, :, s_idx, :, 40].sum(axis = 1).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000
        reg_output = (- reg_charge + reg_discharge).mean(axis = 0) / 1000

        lbl = str(scen_name)
    
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
           bbox_to_anchor=(0.4605, 0.03),
           frameon=False,
           borderaxespad=0.,
           ncol=4,
           title="Scenario",
           fontsize=12)


# fig.tight_layout(pad=0.9, rect=[0, 0, 0, 1])
fig.savefig(fp, bbox_inches='tight', dpi=300)
plt.show()

