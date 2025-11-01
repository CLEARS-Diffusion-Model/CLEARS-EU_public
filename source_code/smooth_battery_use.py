# -*- coding: utf-8 -*-
"""
Created on Fri Sep 12 21:49:13 2025

@author: hartv
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime


def smooth_battery_use(data, titles, period, f):
    
    if np.any(data['peak_participation'][:, :, :, :, :, :, period] > 0):
        peak_str_cap = ((data['battery_cum'][:, :, :, :, f, 0, period] * data['battery_size_adj'][:, :, :, :, 0, 0, 0]).sum(axis = 1).sum(axis = 1).sum(axis = 1) * 
                        data['peak_participation'][:, 0, 0, 0, 0, 0, period] / 100)


        # Set main parameters
        eff_idx = titles['battery_data'].index('efficiency')
        battery_eff = data['battery_specs'][eff_idx, 0, 0, 0, 0, 0, 0]
    
        # Get DoD
        dod_idx = titles['battery_data'].index('depth_of_discharge')
        dod = data['battery_specs'][dod_idx, 0, 0, 0, 0, 0, 0]
    

        # Set PV and battery size
        pv_size = data['pv_size_adj'][:, :, :, :, 0, 0, 0]
        total_pv_gen = (data['pv_gen_adj'][:, :, :, :, 0, :, :] * data['battery_cum'][:, :, :, :, f, 0, period, np.newaxis, np.newaxis]).sum(axis = 1).sum(axis = 1).sum(axis = 1)
        
        
        # Get county profiles and solar generation
        adj_profile = data['profiles_adj'][:, :, :, :, 0, :, :]
        adj_pv_gen = data['pv_gen_adj'][:, :, :, :, 0, :, :]
        # Calculate PV overproduction
        overprod = adj_pv_gen - adj_profile
        overprod[overprod < 0] = 0
        # Total PV overgeneration
        total_pv_overprod = (overprod * data['battery_cum'][:, :, :, :, f, 0, period, np.newaxis, np.newaxis]).sum(axis = 1).sum(axis = 1).sum(axis = 1)
        total_pv_voltage = (pv_size * data['battery_cum'][:, :, :, :, f, 0, period]).sum(axis = 1).sum(axis = 1).sum(axis = 1)
        
        charge = np.zeros_like(total_pv_overprod)
        charge_level = np.zeros_like(total_pv_overprod)
        discharge = np.zeros_like(total_pv_overprod)
        prev_charge_level = np.zeros_like(total_pv_overprod[:, 0, 0])

        # Get day-ahead load
        day_ahead_load = data['load_day_ahead'][:, 0, 0, 0, 0, :, :].copy()
        residual_day_ahead_load = day_ahead_load - total_pv_overprod / 1000
        drop_hours = [1, 2, 3, 4]
        day_ahead_main_hours = np.delete(residual_day_ahead_load, drop_hours, axis=2)
        day_ahead_avg = np.mean(day_ahead_main_hours, axis=2)
        # day_ahead_median = np.percentile(residual_day_ahead_load, 50, axis=2)
        load = data['load'][:, 0, 0, 0, 0, :, :].copy()
        
        
        for d, day in enumerate(titles['date']):
            for h, hour in enumerate(titles['hour']):   
                # Charge if load is lower than the median
                diff_charge_avg = (day_ahead_avg[:, d] * 1 - (load[:, d, h] - total_pv_overprod[:, d, h] / 1000)) * 1000
                diff_charge_avg[diff_charge_avg < 0] = 0
                # Add charge to battery and adjust for efficiency
                if h > 0:
                    prev_charge_level = charge_level[:, d, h - 1].copy()
                    charge_level[:, d, h]  = prev_charge_level + np.minimum(np.minimum(diff_charge_avg * battery_eff, total_pv_voltage / 2), total_pv_overprod[:, d, h])
                    # Cap charge with battery size
                    charge_level[:, d, h] = np.minimum(charge_level[:, d, h], peak_str_cap)
                    # Get hourly charge
                    charge[:, d, h] = (charge_level[:, d, h] - prev_charge_level) / battery_eff

                elif h == 0 and d > 0:
                    last_h = max(list(titles['hour_short']))
                    prev_charge_level = charge_level[:, d - 1, last_h].copy()
                    charge_level[:, d, h]  = prev_charge_level + np.minimum(np.minimum(diff_charge_avg * battery_eff, total_pv_voltage / 2), total_pv_overprod[:, d, h])
                    # Cap charge with battery size
                    charge_level[:, d, h] = np.minimum(charge_level[:, d, h], peak_str_cap)
                    # Get hourly charge
                    charge[:, d, h] = (charge_level[:, d, h] - prev_charge_level) / battery_eff
                else:
                    # If this is the first hour
                    charge_level[:, d, h] = prev_charge_level + np.minimum(np.minimum(diff_charge_avg * battery_eff, total_pv_voltage / 2), total_pv_overprod[:, d, h])
                    # Cap charge with battery size
                    charge_level[:, d, h] = np.minimum(charge_level[:, d, h], peak_str_cap)
                    # Get hourly charge
                    charge[:, d, h] = (charge_level[ :, d, h]) / battery_eff


                # Create holder for discharge potential
                discharge_potential = np.zeros_like(discharge[:, d, h])

                # Do not allow battery to go below 20%
                # Calculate discharge potential
                discharge_potential[:] = np.maximum(0, charge_level[:, d, h] - (1 - dod) * peak_str_cap[:])
                # Discharge if load is higher than median
                diff_discharge_avg = ((load[:, d, h] - total_pv_overprod[:, d, h] / 1000) - day_ahead_avg[:, d] * 1)  * 1000
                diff_discharge_avg[diff_discharge_avg < 0] = 0
                # Calculate discharge
                discharge[:, d, h] = np.minimum(np.minimum(discharge_potential[:], diff_discharge_avg[:]), total_pv_voltage / 2)
                # Remove discharge
                charge_level[:, d, h] = charge_level[:, d, h] - discharge[:, d, h]

                # if h == 14:
                #     print('______________________________')
                #     print('Day:', d)
                #     print(charge_level[0, d, h] / peak_str_cap[0])
                # if h == 18:
                #     print(charge_level[0, d, h] / peak_str_cap[0])
                # if h == 23:
                #     print(charge_level[0, d, h] / peak_str_cap[0])
        data['charge'][:, 0, 0, 0, :, :, 0] = charge[:, :, :]
        data['charge_level'][:, 0, 0, 0, :, :, 0] = charge_level[:, :, :]
        data['discharge'][:, 0, 0, 0, :, :, 0] = discharge[:, :, :]    
    
    return data
            

# def smooth_battery_use(data, titles, period, f):
    
#     if np.any(data['peak_participation'][:, :, :, :, :, :, period] > 0):
#         peak_str_cap = ((data['battery_cum'][:, :, :, :, f, 0, period] * data['battery_size_adj'][:, :, :, :, 0, 0, 0]).sum(axis = 1).sum(axis = 1).sum(axis = 1) * 
#                         data['peak_participation'][:, 0, 0, 0, 0, 0, period] / 100)


#         # Set main parameters
#         yearly_cons = data['consumption'][:, :, :, :, :, :, :]
#         cons_size = np.array([1.5, 1, 0.75])[np.newaxis, np.newaxis, :, np.newaxis, np.newaxis, np.newaxis, np.newaxis]
#         eff_idx = titles['battery_data'].index('efficiency')
#         battery_eff = data['battery_specs'][eff_idx, 0, 0, 0, 0, 0, 0]
    
#         # Get DoD
#         dod_idx = titles['battery_data'].index('depth_of_discharge')
#         dod = data['battery_specs'][dod_idx, 0, 0, 0, 0, 0, 0]
    
#         # Adjust profiles with consumption
#         cons_prof = np.repeat(yearly_cons, len(titles['profile_type']), axis = 1)
#         cons_prof_size = np.repeat(cons_prof, len(titles['cons_size']), axis = 2)
#         cons_prof_size_azi = np.repeat(cons_prof_size, len(titles['azimuth']), axis = 3)
    
#         profile_sum = np.expand_dims(data['profiles'][:, :, :, :, :, :, :].sum(axis = 6).sum(axis = 5), axis = (5, 6))
    
#         data['consumption_adj'] = cons_prof_size_azi * profile_sum * cons_size
#         data['battery_size_adj'] = data['battery_size'] * data['consumption_adj'] / data['consumption']
#         data['pv_size_adj'] = data['pv_size'] * data['consumption_adj'] / data['consumption']
    
    
#         # Adjust solar profile to meet annual consumption
#         pv_size = data['pv_size_adj'][:, :, :, :, 0, 0, 0]
#         # data['pv_size_adj'][:, :, :, :, 0, 0, 0] = pv_size
#         data['pv_gen_adj'] = data['pv_gen'][:, :, :, :, :, :, :] * pv_size[:, :, :, :, np.newaxis, np.newaxis, np.newaxis]
#         # Total PV generation
#         total_pv_gen = (data['pv_gen_adj'][:, :, :, :, 0, :, :] * data['battery_cum'][:, :, :, :, f, 0, period, np.newaxis, np.newaxis]).sum(axis = 1).sum(axis = 1).sum(axis = 1)
        
#         # Get day-ahead load
#         day_ahead_load = data['load_day_ahead'][:, 0, 0, 0, 0, :, :]
#         load = data['load'][:, 0, 0, 0, 0, :, :].copy()
        
#         # Get county profiles and solar generation
#         adj_profile = data['profiles_adj'][:, :, :, :, 0, :, :]
#         adj_pv_gen = data['pv_gen_adj'][:, :, :, :, 0, :, :]
#         # Calculate PV overproduction
#         overprod = adj_pv_gen - adj_profile
#         overprod[overprod < 0] = 0
#         # Total PV overgeneration
#         total_pv_overprod = (overprod * data['battery_cum'][:, :, :, :, f, 0, period, np.newaxis, np.newaxis]).sum(axis = 1).sum(axis = 1).sum(axis = 1)
#         total_pv_voltage = (pv_size * data['battery_cum'][:, :, :, :, f, 0, period]).sum(axis = 1).sum(axis = 1).sum(axis = 1)
        
#         charge = np.zeros_like(total_pv_overprod)
#         charge_level = np.zeros_like(total_pv_overprod)
#         discharge = np.zeros_like(total_pv_overprod)
#         prev_charge_level = np.zeros_like(total_pv_overprod[:, 0, 0])

        
#         # Get 7-day rolling median of load for the past 7 days
#         n_countries, n_days, n_hours = load.shape
#         hours = load.reshape(n_countries, -1)  # (N, 8760)
#         total_hours = hours.shape[1]
#         window = 168
        
#         # Extend the array by wrapping the first (window-1) hours to the end
#         hours_extended = np.concatenate([hours[:, -window+1:], hours], axis=1)

#         # shape: (N, 8760 + 167)
        
#         # Sliding windows across the extended time axis
#         windows = np.lib.stride_tricks.sliding_window_view(
#             hours_extended, window_shape=window, axis=1
#         )
#         # shape: (N, 8760, 168)
        
#         # Median along the 168-hour window
#         rolling_median = np.median(windows, axis=-1)
#         rolling_median = rolling_median.reshape(n_countries, n_days, n_hours)
        
        
#         # Build a datetime index for one non-leap year
#         time_index = pd.date_range("2025-01-01", periods=8760, freq="H")
        
#         # Put into a Series for rolling operations
#         hour_df = pd.DataFrame(hours.T, index = time_index, columns = titles['country'])
        
#         # Take last 167 hours, but shift them back by 1 year to keep index monotonic
#         pad = hour_df.iloc[-(window - 1):].copy()
#         pad.index = pad.index - pd.DateOffset(years=1)
        
#         # Concatenate (extended length = 8760 + 167)
#         df_extended = pd.concat([pad, hour_df])
        
#         # mask out 1–4 am (in extended frame)
#         # df_masked = df_extended.copy()
#         # df_masked.loc[df_extended.index.hour.isin([1, 2, 3, 4])] = np.nan
#         drop_hours = [1, 2, 3, 4]
#         df_masked = df_extended.loc[~df_extended.index.hour.isin(drop_hours)].copy()
#         rolling_median_l = int(window - window / 24 * len(drop_hours))
#         # rolling median (always 168 values possible)
#         df_rolling = df_masked.rolling(rolling_median_l, min_periods=rolling_median_l).median()
        
#         # drop the padded rows
#         df_rolling = df_rolling.iloc[(rolling_median_l - 1):]
        
#         df_reindexed = df_rolling.reindex(time_index)
#         rolling_median_filled = df_reindexed.interpolate(method="time")
#         rolling_median = rolling_median_filled.T.values.reshape(n_countries, n_days, n_hours) * 0.95

        
#         # # interpolate missing values (1–4 am)
#         # df_filled = df_rolling.interpolate(method="time")
        
#         # # back to NumPy (27, 8760)
#         # result = df_filled.T.to_numpy()
        

#         # # Remove evening valley hours
#         # hour_df.loc[hour_df.index.hour.isin([1, 2, 3, 4])] = np.nan
        
#         # # Rolling median over 168h, excluding 1–4am values
#         # rolling_median = hour_df.rolling("168H", min_periods=1).median()
        
#         # # Interpolate missing values for 1–4am
#         # rolling_median_filled = rolling_median.interpolate(method="time")
        
#         # result = rolling_median_filled.to_numpy()
        
#         for d, day in enumerate(titles['date']):
#             for h, hour in enumerate(titles['hour']):   
#                 # Charge if load is lower than the median
#                 diff_charge_median = (rolling_median[:, d, h] - load[:, d, h]) * 1000
#                 diff_charge_median[diff_charge_median < 0] = 0
#                 # Add charge to battery and adjust for efficiency
#                 if h > 0:
#                     prev_charge_level = charge_level[:, d, h - 1].copy()
#                     charge_level[:, d, h]  = prev_charge_level + np.minimum(np.minimum(diff_charge_median * battery_eff, total_pv_voltage), total_pv_overprod[:, d, h])
#                     # Cap charge with battery size
#                     charge_level[:, d, h] = np.minimum(charge_level[:, d, h], peak_str_cap)
#                     # Get hourly charge
#                     charge[:, d, h] = charge_level[:, d, h] - prev_charge_level

#                 elif h == 0 and d > 0:
#                     last_h = max(list(titles['hour_short']))
#                     prev_charge_level = charge_level[:, d - 1, last_h].copy()
#                     charge_level[:, d, h]  = prev_charge_level + np.minimum(np.minimum(diff_charge_median * battery_eff, total_pv_voltage), total_pv_overprod[:, d, h])
#                     # Cap charge with battery size
#                     charge_level[:, d, h] = np.minimum(charge_level[:, d, h], peak_str_cap)
#                     # Get hourly charge
#                     charge[:, d, h] = charge_level[:, d, h] - prev_charge_level
#                 else:
#                     # If this is the first hour
#                     charge_level[:, d, h] = prev_charge_level + np.minimum(np.minimum(diff_charge_median * battery_eff, total_pv_voltage), total_pv_overprod[:, d, h])
#                     # Cap charge with battery size
#                     charge_level[:, d, h] = np.minimum(charge_level[:, d, h], peak_str_cap)
#                     # Get hourly charge
#                     charge[:, d, h] = charge_level[ :, d, h]


#                 # Create holder for discharge potential
#                 discharge_potential = np.zeros_like(discharge[:, d, h])

#                 # Do not allow battery to go below 20%
#                 # Calculate discharge potential
#                 discharge_potential[:] = np.maximum(0, charge_level[:, d, h] - (1 - dod) * peak_str_cap[:])
#                 # Discharge if load is higher than median
#                 diff_discharge_median = (load[:, d, h] - rolling_median[:, d, h])  * 1000
#                 diff_discharge_median[diff_discharge_median < 0] = 0
#                 # Calculate discharge
#                 discharge[:, d, h] = np.minimum(np.minimum(discharge_potential[:], diff_discharge_median[:]), total_pv_voltage)
#                 # Remove discharge
#                 charge_level[:, d, h] = charge_level[:, d, h] - discharge[:, d, h]

#                 # if h == 14:
#                 #     print('______________________________')
#                 #     print('Day:', d)
#                 #     print(charge_level[0, d, h] / peak_str_cap[0])
#                 # if h == 18:
#                 #     print(charge_level[0, d, h] / peak_str_cap[0])
#                 # if h == 23:
#                 #     print(charge_level[0, d, h] / peak_str_cap[0])
#         data['charge'][:, 0, 0, 0, :, :, 0] = charge[:, :, :]
#         data['charge_level'][:, 0, 0, 0, :, :, 0] = charge_level[:, :, :]
#         data['discharge'][:, 0, 0, 0, :, :, 0] = discharge[:, :, :]    
    
#     return data
            
            
            
            
            
            
            
                



