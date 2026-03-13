# -*- coding: utf-8 -*-
"""
Created on Fri Sep 12 21:47:44 2025

@author: hartv
"""


import pandas as pd
import numpy as np
import os
from datetime import datetime


def peak_battery_use(data, titles, period):
    # Set main parameters
    eff_idx = titles['battery_data'].index('efficiency')
    battery_eff = data['battery_specs'][eff_idx, 0, 0, 0, 0, 0, 0]


    # Get DoD
    dod_idx = titles['battery_data'].index('depth_of_discharge')
    dod = data['battery_specs'][dod_idx, 0, 0, 0, 0, 0, 0]


    # Set PV and battery size
    pv_size = data['pv_size_adj'][:, :, :, :, 0, 0, 0]
    battery_size = data['battery_size_adj'][:, :, :, :, 0, 0, 0]



    # for i, country in enumerate(titles['country']):
        
    #     peak_h = data['peak_h'][i, :, :, 0, 0, 0, 0]
            
    #     # Get county profiles and solar generation
    #     adj_profile = data['profiles_adj'][i, :, :, :, 0, :, :]
    #     adj_pv_gen = data['pv_gen_adj'][i, :, :, :, 0, :, :]
    #     # Calculate PV overproduction
    #     overprod = adj_pv_gen - adj_profile
    #     overprod[overprod < 0] = 0

    #     # Calculate residual load
    #     residual_demand = adj_profile - adj_pv_gen
    #     residual_demand[residual_demand < 0] = 0
    #     reg_pv_size = pv_size[i, :, :, :]

    #     charge = np.zeros_like(residual_demand)
    #     charge_level = np.zeros_like(residual_demand)
    #     discharge = np.zeros_like(residual_demand)

    #     for d, day in enumerate(titles['date']):

    #         for h, hour in enumerate(titles['hour']):
    #             if not np.any(np.all(peak_h == np.array([d, h])[None, :], axis=1)):
    #                 # Add charge to battery and adjust for efficiency
    #                 if h > 0:
    #                     prev_charge_level = charge_level[:, :, :, d, h - 1]
    #                     charge_level[:, :, :, d, h]  = prev_charge_level + np.minimum(overprod[:, :, :, d, h] * battery_eff, reg_pv_size / 2)
    
    #                 elif h == 0 and d > 0:
    #                     last_h = max(list(titles['hour_short']))
    #                     prev_charge_level = charge_level[:, :, :, d - 1, last_h]
    #                     charge_level[:, :, :, d, h]  = prev_charge_level + np.minimum(overprod[:, :, :, d, h] * battery_eff, reg_pv_size / 2)
    #                     # Get hourly charge
    #                     charge[:, :, :, d, h] = charge_level[:, :, :, d, h] - prev_charge_level
    #                 else:
    #                     charge_level[:, :, :, d, h]  = np.minimum(overprod[:, :, :, d, h] * battery_eff, reg_pv_size / 2)
    #                     prev_charge_level = np.zeros_like(charge_level[:, :, :, d, h])
    
    #                 # Create holder for discharge potential
    #                 discharge_potential = np.zeros_like(discharge[:, :, :, d, h])
    #                 # Cap charge with battery size
    #                 for s, size in enumerate(titles['cons_size']):
    #                     charge_level[:, s, :, d, h] = np.minimum(charge_level[:, s, :, d, h], battery_size[i, :, s, :])
    #                     # Do not allow battery to go below 20%
    #                     # Calculate discharge potential
    #                     discharge_potential[:, s, :] = np.maximum(0, charge_level[:, s, :, d, h] - (1 - dod) * battery_size[i, :, s, :])

    #                 # Get hourly charge
    #                 charge[:, :, :, d, h] = charge_level[:, :, :, d, h] - prev_charge_level

    
    #                 # Calculate hourly charge
    #                 if h > 0:
    #                     prev_charge_level = charge_level[:, :, :, d, h - 1]
    #                     charge[:, :, :, d, h] = (charge_level[:, :, :, d, h] - prev_charge_level) / battery_eff
    
    #                 elif h == 0 and d > 0:
    #                     last_h = max(list(titles['hour_short']))
    #                     prev_charge_level = charge_level[:, :, :, d - 1, last_h]
    #                     charge[:, :, :, d, h] = (charge_level[:, :, :, d, h] - prev_charge_level) / battery_eff
    #                 else:
    #                     charge[:, :, :, d, h] = (charge_level[:, :, :, d, h]) / battery_eff
    
    
    #                 # Calculate discharge
    #                 discharge[:, :, :, d, h] = np.minimum(discharge_potential[:, :, :], residual_demand[:, :, :, d, h])

    #             # If peak hour
    #             # sun_h = list(range(11, 16))
    #             if np.any(np.all(peak_h == np.array([d, h])[None, :], axis=1)):

    #                 # Assume that during peak hours batteries are not charged
    #                 if h > 0:
    #                     prev_charge_level = charge_level[:, :, :, d, h - 1]
    #                     charge_level[:, :, :, d, h]  = prev_charge_level
    #                     # Charge remains 0    
    #                 elif h == 0 and d > 0:
    #                     last_h = max(list(titles['hour_short']))
    #                     prev_charge_level = charge_level[:, :, :, d - 1, last_h]
    #                     charge_level[:, :, :, d, h]  = prev_charge_level
    #                 # If the first hour of the first day is peak hour charge and charge level remains 0
                    
                    
    #                 # Get the 30-day average residual demand (demand potentially supplied by battery)
    #                 prev_month = d - 30
    #                 # Consider the following 16 hours to supply with the battery
    #                 if h < 8:
    #                     follow_h = np.array(list(range(h + 1, h + 17)))
    #                 elif 7 < h < 23:
    #                     next_day = -(24 - h - 16)
    #                     follow_h = np.array(list(range(h + 1, 24)) + list(range(0, next_day + 1)))
    #                 else:
    #                     follow_h = np.array(list(range(0, 16)))

    #                 # Create holder for discharge potential
    #                 discharge_potential = np.zeros_like(discharge[:, :, :, d, h])
    #                 # Cap charge with battery size
    #                 for s, size in enumerate(titles['cons_size']):
    #                     charge_level[:, s, :, d, h] = np.minimum(charge_level[:, s, :, d, h], battery_size[i, :, s, :])
    #                     # Do not allow battery to go below 20%
    #                     # Calculate discharge potential
    #                     discharge_potential[:, s, :] = np.maximum(0, charge_level[:, s, :, d, h] - (1 - dod) * battery_size[i, :, s, :])
    
    
    #                 # Calculate discharge
    #                 discharge[:, :, :, d, h] = np.minimum(discharge_potential[:, :, :], residual_demand[:, :, :, d, h])
    #                 remaining_potential = discharge_potential[:, :, :] - discharge[:, :, :, d, h]


    #                 if d >= 30:
    #                     date_idx = np.array(list(range(prev_month, d)))
    #                 else:
    #                     # If date in January then use December data
    #                     date_idx = np.array(list(range(365 + d - 30, 365)) + list(range(0, d + 1)))
    #                 avg_daily_demand = residual_demand[:, :, :, date_idx[:,None], follow_h[None, :]].mean(axis = 3).sum(axis = 3)

    #                 # If stored energy is more than the 30-day average sell excess energy to the system
    #                 # if np.any(remaining_potential > avg_daily_demand):
    #                 # Sell excess energy but limited to battery power capacity
    #                 peak_sell = np.minimum(reg_pv_size / 2, (remaining_potential))
    #                 peak_sell[peak_sell < 0] = 0
    #                 # Add discharge to peak hour
    #                 discharge[:, :, :, d, h] += peak_sell


    #             # Remove discharge
    #             charge_level[:, :, :, d, h] = charge_level[:, :, :, d, h] - discharge[:, :, :, d, h]

    #     data['charge'][i, :, :, :, :, :, 0] = charge[:, :, :, :, :]
    #     data['charge_level'][i, :, :, :, :, :, 0] = charge_level[:, :, :, :, :]
    #     data['discharge'][i, :, :, :, :, :, 0] = discharge[:, :, :, :, :]

        
    for i, country in enumerate(titles['country']):
        
        if np.any(data['peak_h'] > 0):
            peak_h = data['peak_h'][i, :, 0, 0, 0, 0, period - 1]
        else: 
            peak_h = [18, 19, 20, 21]
            data['peak_h'][i, :, 0, 0, 0, 0, period - 1] = [18, 19, 20, 21]
            

        # Get county profiles and solar generation
        adj_profile = data['profiles_adj'][i, :, :, :, 0, :, :]
        adj_pv_gen = data['pv_gen_adj'][i, :, :, :, 0, :, :]
        # Calculate PV overproduction
        overprod = adj_pv_gen - adj_profile
        overprod[overprod < 0] = 0

        # Calculate residual load
        residual_demand = adj_profile - adj_pv_gen
        residual_demand[residual_demand < 0] = 0
        reg_pv_size = pv_size[i, :, :, :]

        charge = np.zeros_like(residual_demand)
        charge_level = np.zeros_like(residual_demand)
        discharge = np.zeros_like(residual_demand)
        prev_charge_level = np.zeros_like(charge_level[:, :, :, 0, 0])


        for d, day in enumerate(titles['date']):

            for h, hour in enumerate(titles['hour']):
                # Add charge to battery and adjust for efficiency
                if h > 0:
                    prev_charge_level = charge_level[:, :, :, d, h - 1]
                    charge_level[:, :, :, d, h]  = prev_charge_level + np.minimum(overprod[:, :, :, d, h] * battery_eff, reg_pv_size / 2)
                    # Get hourly charge

                elif h == 0 and d > 0:
                    last_h = max(list(titles['hour_short']))
                    prev_charge_level = charge_level[:, :, :, d - 1, last_h]
                    charge_level[:, :, :, d, h]  = prev_charge_level + np.minimum(overprod[:, :, :, d, h] * battery_eff, reg_pv_size / 2)
                else:
                    charge_level[:, :, :, d, h]  = np.minimum(overprod[:, :, :, d, h] * battery_eff, reg_pv_size / 2)


                # Create holder for discharge potential
                discharge_potential = np.zeros_like(discharge[:, :, :, d, h])
                # Cap charge with battery size
                for s, size in enumerate(titles['cons_size']):
                    charge_level[:, s, :, d, h] = np.minimum(charge_level[:, s, :, d, h], battery_size[i, :, s, :])
                    charge[:, s, :, d, h] = (charge_level[:, s, :, d, h] - prev_charge_level[:, s, :]) / battery_eff
                    # Do not allow battery to go below 20%
                    # Calculate discharge potential
                    discharge_potential[:, s, :] = np.maximum(0, charge_level[:, s, :, d, h] - (1 - dod) * battery_size[i, :, s, :])    

                # Calculate discharge
                discharge[:, :, :, d, h] = np.minimum(discharge_potential[:, :, :], residual_demand[:, :, :, d, h])

                # If peak hour
                if h in peak_h:
                    # Calculate discharge
                    remaining_potential = discharge_potential[:, :, :] - discharge[:, :, :, d, h]

                    # If stored energy is more than 0 sell excess energy to the system
                    if np.any(remaining_potential > 0):
                        # Sell excess energy but limited to battery power capacity
                        peak_sell = np.minimum(reg_pv_size / 4, (remaining_potential))
                        peak_sell[peak_sell < 0] = 0
                        # Add discharge to peak hour
                        discharge[:, :, :, d, h] += peak_sell
    
                        # Remove discharge
                        charge_level[:, :, :, d, h] = charge_level[:, :, :, d, h] - discharge[:, :, :, d, h]

        data['charge'][i, :, :, :, :, :, 0] = charge[:, :, :, :, :]
        data['charge_level'][i, :, :, :, :, :, 0] = charge_level[:, :, :, :, :]
        data['discharge'][i, :, :, :, :, :, 0] = discharge[:, :, :, :, :]



    return data


