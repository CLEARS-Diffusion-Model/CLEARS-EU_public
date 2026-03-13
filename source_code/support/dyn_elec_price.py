# -*- coding: utf-8 -*-
"""
Created on Sun Mar  1 08:25:46 2026

@author: hartv
"""

import os 
import pandas as pd
import numpy as np
import pickle

wd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(wd)


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
# Dimensions of model variables
dims = model.dims
# Converters
converter = model.converter
# Data
data = model.data
# Timeline
timeline = model.timeline   

# Load model data
filename = "output/baseline.pickle"

# open and load
with open(filename, "rb") as f:
    results = pickle.load(f)

# Load wholesale electricity prices
wholesale_prices = pd.read_csv("data/european_wholesale_electricity_price_data_hourly/all_countries.csv")

# Decompose date
date = wholesale_prices['Datetime (Local)']
date = pd.to_datetime(date)
wholesale_prices['year'] = date.dt.year.astype(str)
wholesale_prices['month'] = date.dt.month.astype(str)
wholesale_prices['hour'] = date.dt.hour.astype(str)
# Filter 2023 prices (same year as PV data)
wholesale_prices_2023 = wholesale_prices.loc[wholesale_prices.year == '2023']
# Filter countries
wholesale_prices_2023 = wholesale_prices_2023.loc[wholesale_prices_2023.Country.isin(titles['country'])]
wholesale_prices_2023 = wholesale_prices_2023.rename(columns = {'Country': 'country'})
# Get hourly average
avg_hourly_price = wholesale_prices_2023.groupby(['country', 'hour'])['Price (EUR/MWhe)'].mean().reset_index()
avg_hourly_price['Price (EUR/MWhe)'] = avg_hourly_price['Price (EUR/MWhe)'] / 100
# Divide by average
avg_hourly_price["country_avg"] = (
    avg_hourly_price.groupby("country")["Price (EUR/MWhe)"]
      .transform("mean"))

avg_hourly_price["Value"] = (
    avg_hourly_price["Price (EUR/MWhe)"] / avg_hourly_price["country_avg"])
# Create 2D table
avg_hourly_price_wide = avg_hourly_price.pivot(index = 'country', columns = 'hour', values = 'Value')
# Add Malta and Cyprus
avg_hourly_price_wide.loc['Malta'] = 1
avg_hourly_price_wide.loc['Cyprus'] = 1


# ensure proper ordering
avg_hourly_price_wide = avg_hourly_price_wide.loc[list(titles['country'])]
avg_hourly_price_wide = avg_hourly_price_wide[list(titles['hour'])]
hourly_price_array = avg_hourly_price_wide.to_numpy(dtype=float)

# Find normal profile data
normal_type_idx = titles['profile_type'].index('normal')
normal_profiles = results['profiles_adj'][:, normal_type_idx, :, 0, 0, :, :]
# Electricity prices by consumption size
elec_price = results['electricity_price'][:, :, 0, 0, 0, 0, 0]
# Electricity costs
flat_costs = normal_profiles.sum(axis = 2).sum(axis = 2) * elec_price
# dyn cost
dyn_costs = (normal_profiles.sum(axis = 2) * hourly_price_array[:, np.newaxis, :]).sum(axis = 2)
# Calculate price adjustment
costs_diff = flat_costs / dyn_costs
hourly_price_adj_array = hourly_price_array[:, np.newaxis, :] * costs_diff[:, :, np.newaxis]
# Check if adjustment is correct
dyn_adj_costs = (normal_profiles.sum(axis = 2) * hourly_price_adj_array[:, :, :]).sum(axis = 2)
# All diff should be 1
costs_adj_diff = flat_costs / dyn_adj_costs
if np.any(np.abs(costs_adj_diff - 1) > 0.00001):
    print('Dynamic price adjustment was not successful!')

# Create long df
n_countries = len(titles['country'])
n_cons_size = len(titles['cons_size'])
n_hour = len(titles['hour'])

df_long = pd.DataFrame({
    "country":  np.repeat(list(titles['country']), n_cons_size * n_hour),
    "cons_size": np.tile(np.repeat(list(titles['cons_size']), n_hour), n_countries),
    "hour":     np.tile(list(titles['hour']), n_countries * n_cons_size),
    "Value":    hourly_price_adj_array.reshape(-1)
})

# Visual check
check_df = df_long.pivot(index = ['country', 'cons_size'], columns = 'hour', values = 'Value')
check_df = check_df[list(titles['hour'])]
for c in titles['cons_size']:
    ax = check_df.xs(c, level="cons_size").T.plot()
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol= 5,
        frameon=False)
    
# Export results
out_fn = 'input/Baseline/dyn_elec_price.csv'

# Remove file if exists
try:
    os.remove(out_fn)
except FileNotFoundError:
    pass

# Create comments to the csv file
first_row = 'Calculated dynamic hourly prices form wholesale prices'
second_row = 'EUR/kWh'
third_row = 'Eurostat/Ember'


with open(out_fn, 'a', newline='') as f:
    f.write(first_row + ' \n')
    f.write(second_row + ' \n')
    f.write(third_row + ' \n')
    df_long.to_csv(f, header = True, index = False)
    
    
    
    
    
