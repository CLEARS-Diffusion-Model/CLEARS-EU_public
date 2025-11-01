# -*- coding: utf-8 -*-
"""
Created on Wed Aug  6 22:43:31 2025

@author: hartv
"""


import pandas as pd
import numpy as np
import os
import time
import copy
from scipy.optimize import minimize

def peak_hours(data, titles, period, f):
    

    # Calculate LDC
    load = data['load'][:, 0, 0, 0, 0, :, :].copy()
    
    # Adjust solar profile to meet annual consumption
    pv_size = data['pv_size_adj'][:, :, :, :, 0, 0, 0]
    # data['pv_size_adj'][:, :, :, :, 0, 0, 0] = pv_size
    data['pv_gen_adj'] = data['pv_gen'][:, :, :, :, :, :, :] * pv_size[:, :, :, :, np.newaxis, np.newaxis, np.newaxis]
    
    # Get county profiles and solar generation
    adj_profile = data['profiles_adj'][:, :, :, :, 0, :, :]
    adj_pv_gen = data['pv_gen_adj'][:, :, :, :, 0, :, :]
    # Calculate PV overproduction
    overprod = adj_pv_gen - adj_profile
    overprod[overprod < 0] = 0
    # Total PV overgeneration
    total_pv_overprod = (overprod * data['battery_cum'][:, :, :, :, f, 0, period, np.newaxis, np.newaxis]).sum(axis = 1).sum(axis = 1).sum(axis = 1)

    # Get day-ahead load
    load = data['load'][:, 0, 0, 0, 0, :, :].copy()
    residual_load = load - total_pv_overprod / 1000
    # day_ahead_median = np.percentile(residual_day_ahead_load, 50, axis=2)

    countries, days, hours = residual_load.shape

    
    # Flatten day and hour dimensions: shape -> (27, 8760)
    data_flat = residual_load.reshape(countries, -1)
    

    top_n = 1000
    top_k = len(titles['peak_h'])

    # Output container: preallocate for speed
    top_hours_per_country = np.empty((countries, top_k), dtype=int)

    for i in range(countries):
        # Get top 700 flat indices (fast partial sort)
        top_indices = np.argpartition(data_flat[i], -top_n)[-top_n:]
    
        # Get the hour indices directly from flat indices
        hour_indices = top_indices % hours  # Since it's (365, 24), mod 24 gives hour
    
        # Fast frequency count
        hour_counts = np.bincount(hour_indices, minlength=hours)
    
        # Sort by count descending, get top hours
        top_hours = np.argsort(-hour_counts)
    
        # Repeat if needed (only happens if < 5 unique hours in top 700)
        repeated = np.tile(top_hours, (top_k + len(top_hours) - 1) // len(top_hours))
    
        # Save top 5
        top_hours_per_country[i] = repeated[:top_k]
    
      
    
    data['peak_h'][:, :, 0, 0, 0, 0, period] = top_hours_per_country

    

    return data
