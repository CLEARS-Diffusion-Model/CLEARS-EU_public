# -*- coding: utf-8 -*-
"""
Created on Fri Sep 12 21:49:13 2025

@author: hartv
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime


def smooth_battery_use(data, titles, period, f, controlled_share):
    
    threshold = 1.2
    
    data['charge'][:, :, :, :, :, :, :] = 0
    data['charge_level'][:, :, :, :, :, :, :] = 0
    data['discharge'][:, :, :, :, :, :, :] = 0
    
    sc_charge = (data['charge_baseline'][:, :, :, :, :, :, 0] * data['battery_cum'][:, :, :, :, f, np.newaxis, :, period]).sum(axis = 1).sum(axis = 1).sum(axis = 1)
    sc_discharge = (data['discharge_baseline'][:, :, :, :, :, :, 0] * data['battery_cum'][:, :, :, :, f, np.newaxis, :, period]).sum(axis = 1).sum(axis = 1).sum(axis = 1)  
    net_charge = sc_charge - sc_discharge
    
    if np.any(data['peak_participation'][:, :, :, :, :, :, period] > 0):
        peak_str_cap = controlled_share * ((data['battery_cum'][:, :, :, :, f, 0, period] * 
                                            data['battery_size_adj'][:, :, :, :, 0, 0, 0]).sum(axis = 1).sum(axis = 1).sum(axis = 1))

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
                diff_charge_avg = (day_ahead_avg[:, d] - (load[:, d, h] - total_pv_overprod[:, d, h] / 1000 + net_charge[:, d, h] / 1000)) * 1000
                diff_charge_avg[diff_charge_avg < 0] = 0
                # Add charge to battery and adjust for efficiency
                if h > 0:
                    prev_charge_level = charge_level[:, d, h - 1].copy()
                    # charge_level[:, d, h]  = prev_charge_level + np.minimum(np.minimum(diff_charge_avg * battery_eff, total_pv_voltage / 2), total_pv_overprod[:, d, h])
                    charge_level[:, d, h]  = prev_charge_level + np.minimum(diff_charge_avg * battery_eff, total_pv_voltage / 2)

                    # Cap charge with battery size
                    charge_level[:, d, h] = np.minimum(charge_level[:, d, h], peak_str_cap)
                    # Get hourly charge
                    charge[:, d, h] = (charge_level[:, d, h] - prev_charge_level) / battery_eff

                elif h == 0 and d > 0:
                    last_h = max(list(titles['hour_short']))
                    prev_charge_level = charge_level[:, d - 1, last_h].copy()
                    # charge_level[:, d, h]  = prev_charge_level + np.minimum(np.minimum(diff_charge_avg * battery_eff, total_pv_voltage / 2), total_pv_overprod[:, d, h])
                    charge_level[:, d, h]  = prev_charge_level + np.minimum(diff_charge_avg * battery_eff, total_pv_voltage / 2)
                    # Cap charge with battery size
                    charge_level[:, d, h] = np.minimum(charge_level[:, d, h], peak_str_cap)
                    # Get hourly charge
                    charge[:, d, h] = (charge_level[:, d, h] - prev_charge_level) / battery_eff
                else:
                    # If this is the first hour
                    # charge_level[:, d, h] = prev_charge_level + np.minimum(np.minimum(diff_charge_avg * battery_eff, total_pv_voltage / 2), total_pv_overprod[:, d, h])
                    charge_level[:, d, h] = prev_charge_level + np.minimum(diff_charge_avg * battery_eff, total_pv_voltage / 2)
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
                diff_discharge_avg = ((load[:, d, h] - total_pv_overprod[:, d, h] / 1000 + net_charge[:, d, h] / 1000) - day_ahead_avg[:, d] * threshold)  * 1000
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
            
