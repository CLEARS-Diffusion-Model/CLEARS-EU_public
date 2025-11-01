# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 19:51:33 2023

@author: adh
"""


import pandas as pd
import numpy as np
import os
from datetime import datetime
import math


# for integers
def convert_int_date(ordinal_date):
    date_time = datetime.fromordinal(
        (datetime(1900, 1, 1).toordinal() + int(ordinal_date) - 2)
    )
    return date_time


def read_inputs():
    os.chdir("D:/KDP_2023/FTT-CLEARS/CLEARS_EU")
    data_fn = 'data'
    # Load dummyincome
    # inc = pd.read_csv(os.path.join(data_fn, 'dummy_income.csv'), index_col = 0, encoding = 'ISO-8859-1')
    # inc.index = inc.index.str.strip()
    # inc = inc.rename(index = {'Gyõr-Moson-Sopron': 'Győr-Moson-Sopron'})
    # Load MEKH profiles
    # profiles = pd.read_excel(os.path.join(data_fn, "Felhasználói terhelés profil naptár 2022.xlsb"), skiprows = 0, sheet_name = 'Yearly T-curve')
    # # Drop metadata rows
    # profiles = profiles.loc[profiles.Dátum.notnull(), :]
    # # Get dates
    # profiles['Date'] = profiles.Dátum.apply(convert_int_date)
    # profiles['Month'] = pd.DatetimeIndex(profiles['Date']).month
    # profiles['Day'] = pd.DatetimeIndex(profiles['Date']).day
    # profiles['Hour'] = (profiles['Negyedórák'] * 24).apply(math.floor)
    # keep_cols = ['Lakossági Budapest - teljes lakossági ELMŰ HMKE', 'Lakossági vidék',
    #              'Lakossági általános', 'Date', 'Month', 'Day', 'Hour']
    # profiles = profiles[keep_cols]

    pv_dict = dict()
    ctys = list()
    for f in os.listdir(os.path.join(data_fn, 'JRC_PV')):
        cty = f.split('.')[0].split('_')[0]
        ctys = ctys + [cty]
        # Load solar PV output
        pv_output = pd.read_csv(os.path.join(data_fn, 'JRC_PV', f), skiprows = 10, low_memory = False)
        # Drop metadata rows
        pv_output = pv_output.loc[pv_output.P.notnull(), :]
        # Drop metadata row
        pv_output = pv_output.loc[pv_output.P != ' 2001-2025', :].reset_index(drop = True)
        # Get dates
        pv_output['date'] = pv_output.time.str.split(':').str[0]
        pv_output['hour'] = pv_output.time.str.split(':').str[1].str[0:2]
        # Convert output to float and to KW from W
        pv_output['P'] = pv_output['P'].astype(float) / 1000
        pv_output['date'] = pv_output['date'].astype(int)
        pv_output['date'] = pd.to_datetime(pv_output['date'], format = '%Y%m%d')
        pv_output['hour'] = pv_output['hour'].astype(int)
        pv_dict[cty] = pv_output.copy()

    year = 2023
    dates = pv_output.loc[pv_output.date >= pd.to_datetime(year, format='%Y')]
    dates = dates.loc[dates.date < pd.to_datetime(year + 1, format='%Y')]

    idx = pd.MultiIndex.from_arrays([dates['date'], dates['hour']], names=('date', 'hour'))

    pv_df = pd.DataFrame(np.nan, index = idx, columns = pv_dict.keys())
    for code, pv in pv_dict.items():
        # Restrict dataframe for 2020 and only time and output variables
        pv = pv.loc[pv.date >= pd.to_datetime(year, format='%Y')]
        pv = pv.loc[pv.date < pd.to_datetime(year + 1, format='%Y')]
        # pv['date'] = pv['date'] + pd.DateOffset(years = year_diff)
        # pv = pv.loc[pv.Date < str(int(year) + 1)]
        pv = pv.loc[:, ['date', 'hour', 'P']]
        pv = pv.set_index(['date', 'hour'])

        # Concat profile and PV output data
        pv_df[code] = pv['P']

    # Export data
    pv_long = pv_df.reset_index().melt(id_vars = ['date', 'hour'], value_name = 'Value')[['variable', 'date', 'hour', 'Value']]
    pv_long[['country']] = pv_long.variable.str.split("_", expand = True)
    pv_long.drop(columns=["variable"], inplace=True)
    pv_long = pv_long.sort_values(['country', 'date', 'hour']).reset_index(drop = True)
    pv_long = pv_long[['country', 'date', 'hour', 'Value']]

    # Export results
    out_fn = 'input/Baseline/pv_gen.csv'

    # Remove file if exists
    try:
        os.remove(out_fn)
    except FileNotFoundError:
        pass

    # Create comments to the csv file
    first_row = 'Solar profiles by country'
    second_row = '1kWp'
    third_row = 'JRC'


    with open(out_fn, 'a', newline='') as f:
        f.write(first_row + ' \n')
        f.write(second_row + ' \n')
        f.write(third_row + ' \n')
        pv_long.to_csv(f, header = True, index = False)

    # pv_long.to_csv('input/Baseline/pv_gen' + '.csv', encoding = 'ISO-8859-2', index = False)


    return pv_dict


def residual_pv(profile, profile_type, pv_dict, pv_size, yearly_cons, year, titles):
    # Calculate hourly profile by averaging
    # hourly_profiles = profiles.groupby(['Date', 'Hour'])[profile_type].mean()

    # Adjust profile for yearly consumption
    profile = data['profiles'][0,1,:, :]
    adj_profile = profile #* yearly_cons / profile.sum()
    profile_df = pd.DataFrame(adj_profile, index = titles['date'], columns = titles['hour'])
    profile_df = profile_df.reset_index().melt(id_vars = ['index'], var_name = 'hour', value_name = 'profile')
    profile_df = profile_df.rename(columns = {'index': 'date'})
    profile_df['date'] = pd.to_datetime(profile_df['date'])
    profile_df['hour'] = profile_df['hour'].astype(int)
    profile_df = profile_df.sort_values(['date', 'hour']).reset_index(drop = True)
    profile_df = profile_df.set_index(['date', 'hour'])

    pv_df = pd.DataFrame(np.nan, index = profile_df.index, columns = titles['country'])
    year_diff = 2022 - int(year)

    for cty in titles['country']:
        # Restrict dataframe for 2020 and only time and output variables
        pv = pv_dict[cty].loc[pv_dict[cty].date >= pd.to_datetime(year, format='%Y')]
        pv = pv.loc[pv.date < pd.to_datetime(year + 1, format='%Y')]
        pv['date'] = pv['date'] + pd.DateOffset(years = year_diff)
        # pv = pv.loc[pv.Date < str(int(year) + 1)]
        pv = pv.loc[:, ['date', 'hour', 'P']]
        pv = pv.set_index(['date', 'hour'])

        # Scale up PV to yearly consumption
        # adj_pv = pv_2020 * yearly_cons / pv_2020.sum()
        adj_pv = pv #* pv_size
        # Remove duplicates
        adj_pv = adj_pv[~adj_pv.index.duplicated(keep = 'first')]

        # Concat profile and PV output data
        profile_df['PV'] = adj_pv
        pv_df.loc[:, cty] = adj_pv['P']

    # Export data
    pv_long = pv_df.reset_index().melt(id_vars = ['date', 'hour'])[['variable', 'date', 'hour', 'value']]
    pv_long = pv_long.sort_values(['variable', 'date', 'hour']).reset_index(drop = True)
    pv_long.to_csv('pv_gen' + str(year) + '.csv', encoding = 'ISO-8859-2')
