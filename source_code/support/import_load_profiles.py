# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 14:45:19 2024

@author: adh
"""

import numpy as np
import pandas as pd
import h5py
import os

os.chdir("D://KDP_2023//FTT-CLEARS//CLEARS_EU")


########################################
######## Import load components ########
########################################

filename = "data/loadprofiles.hdf5"

titles_fn = 'utilities/classification_titles.xlsx'
titles = pd.read_excel(titles_fn, sheet_name = None)

conv_fn = 'utilities/converters.xlsx'
conv = pd.read_excel(titles_fn, sheet_name = None)
conv['country']

f1 = h5py.File(filename,'r+')

data = dict()

with h5py.File(filename, "r") as f:
    # Print all root level object names (aka keys)
    # these can be group or dataset names
    print("Keys: %s" % f.keys())
    for k1 in f.keys():
        data[k1] = dict()

        for k2 in f[k1].keys():

            if k2 in conv['country']['Short name'].values:

                for k3 in f[k1][k2].keys():
                    arr = f[k1][k2][k3]['table'][()]  # returns as a numpy array
                    arr2 = np.asarray([np.asarray([sublist[0], sublist[1]]) for sublist in arr])
                    if k2 not in data[k1].keys():
                        data[k1][k2] = pd.DataFrame(arr2, columns = ['index', k3]).set_index('index')
                    else:
                        data[k1][k2][k3] = pd.DataFrame(arr2, columns = ['index', k3]).set_index('index')

# Mapping appliances to profiles
profiles = dict()
profiles['normal'] = ['hot_water', 'ict', 'lighting', 'mechanical_energy',
                      'process_heat']
profiles['heating'] = ['hot_water', 'ict', 'lighting', 'mechanical_energy',
       'process_heat', 'space_heating']
profiles['cooling'] = ['cooling', 'hot_water', 'ict', 'lighting', 'mechanical_energy',
       'process_heat']

# Create indices
dates = np.repeat(titles['date']['Full name'].values, len(titles['hour']['Full name'].values))
hours = []
for _ in range(len(titles['date']['Full name'].values)):
    hours.extend(titles['hour']['Full name'].values)

idx = pd.MultiIndex.from_arrays([dates, hours], names=('date', 'hour'))
cols = ['country', 'profile_type', 'date', 'hour', 'Value']
load_cols = ['country']
load_cols.extend(data['2014']['HU'].columns)

# Create empty dataframes
country_profiles = pd.DataFrame(columns = cols)
norm_country_profiles = pd.DataFrame(columns = cols)

load_df_long = pd.DataFrame(columns = load_cols)

# Convert data into long datasets
for i, cty in enumerate(conv['country']['Short name'].values):
    cty_long = conv['country']['Full name'][i]
    if cty == 'CY':
        load_df = data['2014']['MT'].copy()
    else:
        load_df = data['2014'][cty].copy()
    cty_df = pd.DataFrame(0, columns = titles['profile_type']['Full name'].values,
                                     index = idx)

    for p in titles['profile_type']['Full name'].values:
        appliances = profiles[p]
        cty_df[p] = load_df[profiles[p]].sum(axis = 1).values

    # Save load by appliance
    load_df.insert(0, 'country', cty_long)
    load_df_long = pd.concat([load_df_long, load_df]).reset_index(drop = True)

    # Save results in long format
    cty_df_long = pd.melt(cty_df.reset_index(), id_vars = ['date', 'hour'],
                                         var_name = 'profile_type', value_name = 'Value')
    cty_df_long = cty_df_long[['profile_type', 'date', 'hour', 'Value']]
    cty_df_long.insert(0, 'country', cty_long)

    country_profiles = pd.concat([country_profiles, cty_df_long]).reset_index(drop = True)

    # Save results in long format
    cty_df_long = pd.melt(cty_df.reset_index(), id_vars = ['date', 'hour'],
                                         var_name = 'profile_type', value_name = 'Value')
    cty_df_long = cty_df_long[['profile_type', 'date', 'hour', 'Value']]
    cty_df_long.insert(0, 'country', cty_long)

    country_profiles = pd.concat([country_profiles, cty_df_long]).reset_index(drop = True)


    # Normalise consumption
    norm_cty_df = cty_df / cty_df.normal.sum()

    norm_cty_df_long = pd.melt(norm_cty_df.reset_index(), id_vars = ['date', 'hour'],
                                         var_name = 'profile_type', value_name = 'Value')
    norm_cty_df_long = norm_cty_df_long[['profile_type', 'date', 'hour', 'Value']]
    norm_cty_df_long.insert(0, 'country', cty_long)

    norm_country_profiles = pd.concat([norm_country_profiles, norm_cty_df_long]).reset_index(drop = True)

# Export results
out_fn = 'input/Baseline/profiles.csv'

# Remove file if exists
try:
    os.remove(out_fn)
except FileNotFoundError:
    pass

# Create comments to the csv file
first_row = 'Load profiles by country'
second_row = 'Normalised to normal profile'
third_row = 'Schlemminger et al. (2021)'


with open(out_fn, 'a', newline='') as f:
    f.write(first_row + ' \n')
    f.write(second_row + ' \n')
    f.write(third_row + ' \n')
    norm_country_profiles.to_csv(f, header = True, index = False)



#########################################
##### Calculate share of profiles ######
#########################################

hh_nr_fn = 'input/Baseline/hh_total.csv'
hh_nr = pd.read_csv(hh_nr_fn, skiprows = 3, index_col = 0)
end_use_fn = 'input/Baseline/end_use_consumption.csv'
end_use = pd.read_csv(end_use_fn, skiprows = 3, index_col = 0)


profile_sums = norm_country_profiles.groupby(by = ['country', 'profile_type']).Value.sum()
appliance_sums = load_df_long.groupby(by = ['country']).sum()
# appliance_sums = pd.melt(appliance_sums.reset_index(), id_vars = 'country', var_name = 'appliance', value_name = 'Value')

# Get share of households using cooling
appliances = ['space_heating', 'cooling']
cooling_sums = appliance_sums.cooling
cooling_share = end_use.loc[end_use.end_use == 'cooling', 'Value'] * 1000000 / cooling_sums / hh_nr.Value
cooling_share[cooling_share > 0.9] = 0.8
# Get share of households using heating
heating_sums = appliance_sums.space_heating
heating_share = end_use.loc[end_use.end_use == 'space_heating', 'Value'] * 1000000 / heating_sums / hh_nr.Value
heating_share[heating_share > 0.9] = 0.8
heating_share[(heating_share + cooling_share) > 1] = 0.2

profile_share = end_use.copy()
profile_share = profile_share.query("end_use in ['space_heating', 'cooling', 'total']")
profile_share.end_use = profile_share.end_use.str.replace('total', "normal")
profile_share.end_use = profile_share.end_use.str.replace('space_heating', "heating")
profile_share = profile_share.rename({'end_use': 'profile_type'}, axis = 1)
profile_share.loc[profile_share.profile_type == 'cooling', 'Value'] = cooling_share
profile_share.loc[profile_share.profile_type == 'heating', 'Value'] = heating_share
profile_share.loc[profile_share.profile_type == 'normal', 'Value'] = 1 - cooling_share - heating_share

# Export results
prof_share_fn = 'input/Baseline/profile_shares.csv'

# Remove file if exists
try:
    os.remove(prof_share_fn)
except FileNotFoundError:
    pass

# Create comments to the csv file
first_row = 'Shares of profile_types by country'
second_row = '-'
third_row = 'Calculated from end-use energy consumption from Eurostat'


with open(prof_share_fn, 'a', newline='') as f:
    f.write(first_row + ' \n')
    f.write(second_row + ' \n')
    f.write(third_row + ' \n')
    profile_share.reset_index().to_csv(f, header = True, index = False)



end_use.loc[end_use.end_use == 'space_heating', 'Value'] / end_use.loc[end_use.end_use == 'total', 'Value']

# Get avg. consumption by profile type
prof_share_fn = 'input/Baseline/profile_shares.csv'
prof_share = pd.read_csv(prof_share_fn, skiprows = 3, index_col = [0, 1])

# Avg. total consumption
avg_total_cons = end_use.loc[end_use.end_use == 'total', 'Value'] / hh_nr.Value * 1000000


# Calculate normal profile consumption based on profile shares and avg. consumption
prof_share_cons = profile_sums * prof_share.Value
prof_share_cons = prof_share_cons.reset_index().set_index('country')
prof_share = prof_share.reset_index().set_index('country')

heating_share_cons = prof_share_cons.loc[prof_share_cons.profile_type == 'heating', 'Value']
cooling_share_cons = prof_share_cons.loc[prof_share_cons.profile_type == 'cooling', 'Value']
normal_share_cons = prof_share_cons.loc[prof_share_cons.profile_type == 'normal', 'Value']

normal_share = prof_share.loc[prof_share.profile_type == 'normal', 'Value']


normal_cons = avg_total_cons / (normal_share_cons + heating_share_cons + cooling_share_cons)

# Export results
out_fn = 'input/Baseline/consumption.csv'

# Remove file if exists
try:
    os.remove(out_fn)
except FileNotFoundError:
    pass

# Create comments to the csv file
first_row = 'Average annual electricity consumption of normal profiles by country'
second_row = 'kWh'
third_row = 'Calculated from Eurostat'


with open(out_fn, 'a', newline='') as f:
    f.write(first_row + ' \n')
    f.write(second_row + ' \n')
    f.write(third_row + ' \n')
    normal_cons.to_csv(f, header = True)


########################################
######### Import national load #########
########################################


cty_conv = {'AT': 'Austria',
  'BE': 'Belgium',
  'BG': 'Bulgaria',
  'HR': 'Croatia',
  'CY': 'Cyprus',
  'CZ': 'Czechia',
  'DK': 'Denmark',
  'EE': 'Estonia',
  'FI': 'Finland',
  'FR': 'France',
  'DE': 'Germany',
  'EL': 'Greece',
  'HU': 'Hungary',
  'IE': 'Ireland',
  'IT': 'Italy',
  'LV': 'Latvia',
  'LT': 'Lithuania',
  'LU': 'Luxembourg',
  'MT': 'Malta',
  'NL': 'Netherlands',
  'PL': 'Poland',
  'PT': 'Portugal',
  'RO': 'Romania',
  'SK': 'Slovakia',
  'SI': 'Slovenia',
  'ES': 'Spain',
  'SE': 'Sweden',
  'EU': 'EU'}


# Import load data
df = pd.read_csv('data/loads.csv', skiprows = 3)
# Split date into multiple columns
df['date'] = df.date.str.split(' - ', expand = True)[0]
df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y %H:%M', dayfirst = True)
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.day
df['hour'] = df['date'].dt.hour
df['value'] = df['value'].interpolate(method='linear')
df = df.rename(columns = {'value': 'Value'})
df_group = df.groupby(['country', 'month', 'day', 'hour']).mean('Value').reset_index()

df_group['date'] = df_group['day'].astype(str) + '/' + df_group['month'].astype(str) + '/' + '2024'
df_group = df_group.drop(['day', 'month'], axis = 1)
df_group = df_group.replace({"country": cty_conv})
# Drop 29th of February
df_group = df_group.loc[df_group['date'] != '29/2/2024']
# Add Malta and Cyprus with 0s
empty_rows = df_group.loc[df_group.country == 'Austria'].copy()
empty_rows['Value'] = 0
cyprus_rows = empty_rows
empty_rows.country = 'Cyprus'
malta_rows = empty_rows
malta_rows.country = 'Malta'
# Merge
df_group = pd.concat([df_group, cyprus_rows, malta_rows]).sort_values(['country', 'date', 'hour'])
df_group = df_group[['country', 'date', 'hour', 'Value']]
# df_group.to_csv('load.csv', index = False)

# Export results
out_fn = 'input/Baseline/load.csv'

# Remove file if exists
try:
    os.remove(out_fn)
except FileNotFoundError:
    pass

# Create comments to the csv file
first_row = 'Hourly load'
second_row = 'MW'
third_row = 'ENTSO-E'


with open(out_fn, 'a', newline='') as f:
    f.write(first_row + ' \n')
    f.write(second_row + ' \n')
    f.write(third_row + ' \n')
    df_group.to_csv(f, header = True, index = False)

########################################
######## Import VRE generation #########
########################################

# Assess variable generation
wind = ['Wind Offshore - Actual Aggregated [MW]', 'Wind Onshore - Actual Aggregated [MW]']
solar = ['Solar - Actual Aggregated [MW]']
gen_files = [f for f in os.listdir('data/ENTSOE_generation') if "Actual Generation per Production Type_202401010000-202501010000" in f]

gen_df = pd.DataFrame(columns = ['country', 'date', 'hour', 'solar', 'wind'])

for f in gen_files:
    df = pd.read_csv(os.path.join('data/ENTSOE_generation', f))
    cty = df['Area'][0].split(' (')[0]
    # print(f)
    # print(cty)
    # print('-----------------------------------')
    if cty == 'Czech Republic':
        cty = 'Czechia'
    if cty not in gen_df.country:
        df['date'] = df.MTU.str.split(' - ', expand = True)[0]
        df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y %H:%M', dayfirst = True)
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['hour'] = df['date'].dt.hour
        df['country'] = cty
        df['wind'] = 0
        for w in wind:
            df[w] = df[w].astype(str).str.replace('n/e', '0').astype(float)
            df['wind'] += df[w]
            df['wind'] = df['wind'].interpolate(method='linear')
    
        df['solar'] = df[solar[0]].astype(str).str.replace('n/e', '0').astype(float)
        df['solar'] = df['solar'].interpolate(method='linear')
    
    
        df_vre = df.groupby(['country', 'month', 'day', 'hour']).mean(['solar', 'wind']).reset_index()
    
        df_vre['date'] = df_vre['day'].astype(str) + '/' + df_vre['month'].astype(str) + '/' + '2024'
        # Drop 29th of February
        df_vre = df_vre.loc[df_vre['date'] != '29/2/2024']
        df_vre = df_vre[['country', 'date', 'hour', 'solar', 'wind']]
        gen_df = pd.concat([gen_df, df_vre])



# Shift solar generation
solar = gen_df[['country', 'date', 'hour', 'solar']]
solar = solar.rename(columns = {'solar': 'Value'})
# solar.to_csv('solar.csv', index = False)
wind = gen_df[['country', 'date', 'hour', 'wind']]
wind = wind.rename(columns = {'wind': 'Value'})
# wind.to_csv('wind.csv', index = False)
# Add Malta and Cyprus with 0s
empty_rows = wind.loc[wind.country == 'Austria'].copy()
empty_rows['Value'] = 0
cyprus_rows = empty_rows
empty_rows.country = 'Cyprus'
malta_rows = empty_rows
malta_rows.country = 'Malta'
# Merge
solar = pd.concat([solar, cyprus_rows, malta_rows]).sort_values(['country', 'date', 'hour'])
wind = pd.concat([wind, cyprus_rows, malta_rows]).sort_values(['country', 'date', 'hour'])


# Export results
out_fn = 'input/Baseline/solar.csv'

# Remove file if exists
try:
    os.remove(out_fn)
except FileNotFoundError:
    pass

# Create comments to the csv file
first_row = 'Solar generation'
second_row = 'MW'
third_row = 'ENTSO-E'


with open(out_fn, 'a', newline='') as f:
    f.write(first_row + ' \n')
    f.write(second_row + ' \n')
    f.write(third_row + ' \n')
    solar.to_csv(f, header = True)
    
# Export results
out_fn = 'input/Baseline/wind.csv'

# Remove file if exists
try:
    os.remove(out_fn)
except FileNotFoundError:
    pass

# Create comments to the csv file
first_row = 'Wind generation'
second_row = 'MW'
third_row = 'ENTSO-E'


with open(out_fn, 'a', newline='') as f:
    f.write(first_row + ' \n')
    f.write(second_row + ' \n')
    f.write(third_row + ' \n')
    wind.to_csv(f, header = True)

########################################
####### Import EV load profiles ########
########################################

# Charging profiles for 50 EVs with regular charging pattern
df_ev = pd.read_excel('data/charging_profile_regular.xlsx', sheet_name = "Absolute profile fraction")
df_ev.columns = df_ev.columns.str.replace('power_demand_', '')
# Split date into multiple columns
df_ev['date'] = pd.to_datetime(df_ev['date_time'], format='%d.%m.%Y %H:%M', dayfirst = True)
df_ev['month'] = df_ev['date'].dt.month
df_ev['day'] = df_ev['date'].dt.day
df_ev['hour'] = df_ev['date'].dt.hour
df_ev_group = df_ev.groupby(['month', 'day', 'hour']).mean('value').reset_index()

df_ev_group['date'] = df_ev_group['day'].astype(str) + '/' + df_ev_group['month'].astype(str) + '/' + '2024'
df_ev_group = df_ev_group.drop(['day', 'month'], axis = 1)
df_ev_group = df_ev_group.set_index(['date', 'hour'])
df_ev_group = df_ev_group['aggregated'] * 20 # Scale up to 1000 vehicles
df_ev_group.name = 'Value'

# Export results
out_fn = 'input/Baseline/ev_charging.csv'

# Remove file if exists
try:
    os.remove(out_fn)
except FileNotFoundError:
    pass

# Create comments to the csv file
first_row = 'EV charging profile'
second_row = 'kW for 1000 vehicles'
third_row = 'Elaad'


with open(out_fn, 'a', newline='') as f:
    f.write(first_row + ' \n')
    f.write(second_row + ' \n')
    f.write(third_row + ' \n')
    df_ev_group.to_csv(f, header = True, index = True)


########################################
###### Import EV battery capacity ######
########################################

df_ftt_ev = pd.read_csv('data/FTT_Tr_EU_EV.csv', skiprows = 4, index_col = 1)

# Based on FTT.Tr input
ev_battery = {"19 Electric Econ": 18.5,
              "20 Electric Mid": 50.2,
              "21 Electric Lux": 81}
years = [c for c in df_ftt_ev.columns if "20" in c]
ev_battery_cap = df_ftt_ev[years].mul(df_ftt_ev['dimension2'].map(ev_battery), axis = 0)
ev_battery_cap = ev_battery_cap.reset_index().groupby("dimension").sum()
ev_battery_cap.index = ev_battery_cap.reset_index()['dimension'].str.split("(", expand = True)[1].str.replace(")", "")

# Examining the vehicle-to-grid opportunity alone, we find that 21%-26%
# of the global theoretical battery capacity (i.e., on-board EV battery
# capacity of the entire EV fleet without considering battery degradation) 
# could be available for vehicle-to-grid services by 2050  =Xu et al, 2023)
# Assume 25% particiption by 2050 with linear growth from 2026
ev_participation = pd.Series(0, index = years)
ev_participation[years[16:]] = list(range(1, 26))
# Assume that 60% could be used for vehicle-to-grid
v2g_ev_battery_cap = ev_battery_cap.mul(ev_participation) / 100 * 0.6 / 1000

cty_conv2 = {'AT': 'Austria',
  'BE': 'Belgium',
  'BG': 'Bulgaria',
  'HR': 'Croatia',
  'CY': 'Cyprus',
  'CZ': 'Czechia',
  'DK': 'Denmark',
  'EN': 'Estonia',
  'FI': 'Finland',
  'FR': 'France',
  'DE': 'Germany',
  'EL': 'Greece',
  'HU': 'Hungary',
  'IE': 'Ireland',
  'IT': 'Italy',
  'LV': 'Latvia',
  'LT': 'Lithuania',
  'LX': 'Luxembourg',
  'MT': 'Malta',
  'NL': 'Netherlands',
  'PL': 'Poland',
  'PT': 'Portugal',
  'RO': 'Romania',
  'SK': 'Slovakia',
  'SI': 'Slovenia',
  'ES': 'Spain',
  'SW': 'Sweden',
  'EU': 'EU'}

v2g_ev_battery_cap.index.name = "country"
v2g_ev_battery_cap.insert(0, '2009', 0)
v2g_ev_battery_cap.insert(0, '2008', 0)
v2g_ev_battery_cap = v2g_ev_battery_cap.rename(cty_conv2, axis = 0).reset_index().sort_values('country').reset_index(drop = True)
v2g_ev_battery_cap = v2g_ev_battery_cap.melt(id_vars = 'country', var_name = 'timeline', value_name = 'Value').sort_values(['country', 'timeline'])

# Export results
out_fn = 'input/Baseline/ev_battery_cap.csv'

# Remove file if exists
try:
    os.remove(out_fn)
except FileNotFoundError:
    pass

# Create comments to the csv file
first_row = 'EV battery capacity available for V2G'
second_row = 'MWh'
third_row = 'FTT:Transport'


with open(out_fn, 'a', newline='') as f:
    f.write(first_row + ' \n')
    f.write(second_row + ' \n')
    f.write(third_row + ' \n')
    v2g_ev_battery_cap.to_csv(f, header = True, index = False)
    
    
    
df_ftt_ev = pd.read_csv('data/FTT_Tr_EU_EV.csv', skiprows = 4, index_col = 1)

df_ftt_ev = df_ftt_ev.reset_index().groupby("dimension").sum()
df_ftt_ev = df_ftt_ev.drop(['scenario', 'dimension2', 'dimension3'], axis = 1)
df_ftt_ev.index = df_ftt_ev.reset_index()['dimension'].str.split("(", expand = True)[1].str.replace(")", "")
df_ftt_ev.index.name = 'country'
df_ftt_ev = df_ftt_ev.reset_index().melt(id_vars = ['country'], var_name = 'timeline', value_name = 'Value').sort_values(['country', 'timeline'])
df_ftt_ev = df_ftt_ev.set_index('country')
df_ftt_ev = df_ftt_ev.rename(index = cty_conv2).reset_index()

# Export results
out_fn = 'input/Baseline/ev_stock.csv'

# Remove file if exists
try:
    os.remove(out_fn)
except FileNotFoundError:
    pass

# Create comments to the csv file
first_row = 'Number of electric vehicles'
second_row = '1000 vehicles'
third_row = 'FTT:Transport'


with open(out_fn, 'a', newline='') as f:
    f.write(first_row + ' \n')
    f.write(second_row + ' \n')
    f.write(third_row + ' \n')
    df_ftt_ev.to_csv(f, header = True, index = False)

########################################
##### Import heating technologies ######
########################################

# filename = "data/FTT_heat_data.xlsx"

# heat_df = pd.read_excel(filename, skiprows = 2)

# df_list = np.split(heat_df, heat_df[heat_df.isnull().all(1)].index)

# heat_dict = {}

# for df in df_list[1:]:
#     cty = df.iloc[1, 0].strip()
#     cty_df = pd.DataFrame(df.iloc[3:, 1:].values, columns = df.iloc[2, 1:].astype(int), index = df.iloc[3:, 0].values)
#     heat_dict[cty] = cty_df