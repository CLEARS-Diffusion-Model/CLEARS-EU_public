# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 21:58:37 2024

@author: adh
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime


def total_battery_use(data, titles, timeline, period, year, f, scenario):

    if 'flex' in scenario:
        data['charge_total'][:, 0, 0, 0, :, :, period] = (data['charge'][:, :, :, :, :, :, 0].sum(axis = 1).sum(axis = 1).sum(axis = 1) +
                                                          (data['charge_baseline'][:, :, :, :, :, :, 0] * data['battery_cum'][:, :, :, :, f, np.newaxis, :, period]).sum(axis = 1).sum(axis = 1).sum(axis = 1))
        data['discharge_total'][:, 0, 0, 0, :, :, period] = (data['discharge'][:, :, :, :, :, :, 0].sum(axis = 1).sum(axis = 1).sum(axis = 1) +
                                                          (data['discharge_baseline'][:, :, :, :, :, :, 0] * data['battery_cum'][:, :, :, :, f, np.newaxis, :, period]).sum(axis = 1).sum(axis = 1).sum(axis = 1))    
      
    else:
        data['charge_total'][:, :, :, :, :, :, period] = (data['charge'][:, :, :, :, :, :, 0] * data['battery_cum'][:, :, :, :, f, np.newaxis, :, period])
        data['discharge_total'][:, :, :, :, :, :, period] = (data['discharge'][:, :, :, :, :, :, 0] * data['battery_cum'][:, :, :, :, f, np.newaxis, :, period])
      
    data['charge_total_2050'][:, :, :, :, :, :, f] = data['charge'][:, :, :, :, :, :, 0] * data['battery_cum'][:, :, :, :, f, np.newaxis, :, period]
    data['discharge_total_2050'][:, :, :, :, :, :, f] = data['discharge'][:, :, :, :, :, :, 0] * data['battery_cum'][:, :, :, :, f, np.newaxis, :, period]

    data['ldc'][:, 0, 0, :, :, :, period] = data['load'][:, 0, 0, 0, :, :, :] + (data['charge_total'][:, :, :, :, :, :, period].sum(axis = 1).sum(axis = 1)
                                                                                 - data['discharge_total'][:, :, :, :, :, :, period].sum(axis = 1).sum(axis = 1)) / 1000


    if year <= 2024:
        data['battery_cap_est'][:, 0, 0, 0, f, 0, period] = data['battery_cap'][:, 0, 0, 0, 0, 0, period]
        # Calibrate battery sizes
        if year == 2024:
            cap_est = (data['battery_cum'][:, :, :, :, f, 0, period] * data['battery_size_adj'][:, :, :, :, 0, 0, 0]).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000
            data['battery_size_adj'][:, :, :, 0, 0, 0, 0]  = data['battery_size_adj'][:, :, :, 0, 0, 0, 0] / (cap_est / data['battery_cap'][:, 0, 0, 0, 0, 0, period])[:, np.newaxis, np.newaxis]

    else:
        data['battery_cap_est'][:, 0, 0, 0, f, 0, period] = (data['battery_cum'][:, :, :, :, f, 0, period] * data['battery_size_adj'][:, :, :, :, 0, 0, 0]).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000

    return data

def total_pv_generation(data, titles, timeline, period, year, f):

    if f == 10:
        data['pv_gen_total'][:, :, :, :, :, :, period] = data['pv_gen_adj'][:, :, :, :, 0, :, :] * data['pv_cum'][:, :, :, :, f, np.newaxis, :, period]
    data['pv_gen_total_2050'][:, :, :, :, :, :, f] = data['pv_gen_adj'][:, :, :, :, 0, :, :] * data['pv_cum'][:, :, :, :, f, np.newaxis, :, period]

    if year <= 2024:
        data['pv_cap_est'][:, 0, 0, 0, f, 0, period] = data['pv_cap'][:, 0, 0, 0, 0, 0, period]

        # Calibrate battery sizes
        if year == 2024:
            cap_est = (data['pv_cum'][:, :, :, :, f, 0, period] * data['pv_size_adj'][:, :, :, :, 0, 0, 0]).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000
            data['pv_size_adj'][:, :, :, 0, 0, 0, 0]  = data['pv_size_adj'][:, :, :, 0, 0, 0, 0] / (cap_est / data['pv_cap'][:, 0, 0, 0, 0, 0, period])[:, np.newaxis, np.newaxis]

    else:
        data['pv_cap_est'][:, 0, 0, 0, f, 0, period] = (data['pv_cum'][:, :, :, :, f, 0, period] * data['pv_size_adj'][:, :, :, :, 0, 0, 0]).sum(axis = 1).sum(axis = 1).sum(axis = 1) / 1000

    return data

def self_consumption(data, titles, timeline, period, f):
    for c, cty in enumerate(titles['country']):
        pv_gen = data['pv_gen_total_2050'][c, :, :, :, :, :, f]
        total_load = data['pv_cum'][c, :, :, :, f, np.newaxis, :, period] * data['profiles_adj'][c, :, :, :, 0, :, :]
        battery_charge = data['charge_total_2050'][c, :, :, :, :, :, f]
        grid_cons = total_load - pv_gen
        grid_cons[grid_cons < 0] = 0
        self_cons_no_battery = total_load - grid_cons
        self_cons_no_battery = self_cons_no_battery.sum() / pv_gen.sum()

        self_cons_battery = total_load + battery_charge - grid_cons
        data['self_consumption'][c, 0, 0, 0, f, 0, period]  = self_cons_battery.sum() / pv_gen.sum()

    return data
