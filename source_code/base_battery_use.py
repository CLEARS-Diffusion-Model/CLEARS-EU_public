# -*- coding: utf-8 -*-
"""
Created on Fri Sep 12 21:45:56 2025

@author: hartv
"""


import pandas as pd
import numpy as np
import os
from datetime import datetime


def base_battery_use(data, titles, period):
    # Set main parameters
    yearly_cons = data['consumption'][:, :, :, :, :, :, :]
    cons_size = np.array([1.5, 1, 0.75])[np.newaxis, np.newaxis, :, np.newaxis, np.newaxis, np.newaxis, np.newaxis]
    eff_idx = titles['battery_data'].index('efficiency')
    battery_eff = data['battery_specs'][eff_idx, 0, 0, 0, 0, 0, 0]
    # Get number of potential adopters by profile
    size_w = np.expand_dims([0.25, 0.5, 0.25], axis = (0, 1, 3))
    azi_w = np.expand_dims([1], axis = (0, 1, 2))
    nr_houses_4d = np.repeat(data['hh_total'][:, :, :, :, 0, 0, 0], len(titles['profile_type']), axis = 1)
    nr_houses_4d = np.repeat(nr_houses_4d, len(titles['cons_size']), axis = 2)
    nr_houses_4d = np.repeat(nr_houses_4d, len(titles['azimuth']), axis = 3)

    nr_houses_profile = data['profile_shares'][:, :, :, :, 0, 0, 0] * nr_houses_4d
    nr_houses_profile = size_w * nr_houses_profile
    nr_houses_profile = azi_w * nr_houses_profile
    owner_sh = data['owner_share'][:, :, :, :, 0, 0, 0] / 100
    hh_sh = data['hh_share'][:, :, :, :, 0, 0, 0] / 100
    # Restrict to 1-3 apartment houses
    data['hh_nr'][:, :, :, :, 0, 0, 0] = nr_houses_profile * hh_sh * owner_sh

    # Get DoD
    dod_idx = titles['battery_data'].index('depth_of_discharge')
    dod = data['battery_specs'][dod_idx, 0, 0, 0, 0, 0, 0]

    # Adjust profiles with consumption
    cons_prof = np.repeat(yearly_cons, len(titles['profile_type']), axis = 1)
    cons_prof_size = np.repeat(cons_prof, len(titles['cons_size']), axis = 2)
    cons_prof_size_azi = np.repeat(cons_prof_size, len(titles['azimuth']), axis = 3)

    profile_sum = np.expand_dims(data['profiles'][:, :, :, :, :, :, :].sum(axis = 6).sum(axis = 5), axis = (5, 6))

    data['consumption_adj'] = cons_prof_size_azi * profile_sum * cons_size
    data['battery_size_adj'] = data['battery_size'] * data['consumption_adj'] / data['consumption']
    data['pv_size_adj'] = data['pv_size'] * data['consumption_adj'] / data['consumption']


    # Adjust profile with consumption profiles
    adj_profile = data['profiles'][:, :, :, :, 0, :, :] / profile_sum[:, :, :, :, 0, :, :]
    data['profiles_adj'] = adj_profile[:, :, np.newaxis, :, :, :, :] * data['consumption_adj'][:, :, :, :, :, :, :]

    # Adjust solar profile to meet annual consumption
    pv_size = data['pv_size_adj'][:, :, :, :, 0, 0, 0]
    # data['pv_size_adj'][:, :, :, :, 0, 0, 0] = pv_size
    data['pv_gen_adj'] = data['pv_gen'][:, :, :, :, :, :, :] * pv_size[:, :, :, :, np.newaxis, np.newaxis, np.newaxis]
    # Set battery size
    battery_size = data['battery_size_adj'][:, :, :, :, 0, 0, 0]


    for i, country in enumerate(titles['country']):
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


        for d, day in enumerate(titles['date']):

            for h, hour in enumerate(titles['hour']):
                # Add charge to battery and adjust for efficiency
                if h > 0:
                    prev_charge_level = charge_level[:, :, :, d, h - 1]
                    charge_level[:, :, :, d, h]  = prev_charge_level + np.minimum(overprod[:, :, :, d, h] * battery_eff, reg_pv_size / 2)
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
                    # Do not allow battery to go below 20%
                    # Calculate discharge potential
                    discharge_potential[:, s, :] = np.maximum(0, charge_level[:, s, :, d, h] - (1 - dod) * battery_size[i, :, s, :])

                # Calculate hourly charge
                if h > 0:
                    prev_charge_level = charge_level[:, :, :, d, h - 1]
                    charge[:, :, :, d, h] = (charge_level[:, :, :, d, h] - prev_charge_level) / battery_eff

                elif h == 0 and d > 0:
                    last_h = max(list(titles['hour_short']))
                    prev_charge_level = charge_level[:, :, :, d - 1, last_h]
                    charge[:, :, :, d, h] = (charge_level[:, :, :, d, h] - prev_charge_level) / battery_eff
                else:
                    charge[:, :, :, d, h] = (charge_level[:, :, :, d, h]) / battery_eff


                # Calculate discharge
                discharge[:, :, :, d, h] = np.minimum(discharge_potential[:, :, :], residual_demand[:, :, :, d, h])

                # Remove discharge
                charge_level[:, :, :, d, h] = charge_level[:, :, :, d, h] - discharge[:, :, :, d, h]

        data['charge'][i, :, :, :, :, :, 0] = charge[:, :, :, :, :]
        data['charge_level'][i, :, :, :, :, :, 0] = charge_level[:, :, :, :, :]
        data['discharge'][i, :, :, :, :, :, 0] = discharge[:, :, :, :, :]
        data['charge_baseline'][i, :, :, :, :, :, 0] = charge[:, :, :, :, :]
        data['charge_level_baseline'][i, :, :, :, :, :, 0] = charge_level[:, :, :, :, :]
        data['discharge_baseline'][i, :, :, :, :, :, 0] = discharge[:, :, :, :, :]


    return data