# -*- coding: utf-8 -*-
"""
Created on Sat Feb 28 10:11:41 2026

@author: hartv
"""


import pandas as pd
import numpy as np
import os
from datetime import datetime
from scipy.stats import norm

def npv_calculation_battery(data, controlled_share, scenario, titles, period):

    # Set main parameters
    # Assume no subsidy before 2024
    subsidy_all = data['subsidy'][:, 0, 0, 0, 0, 0, 0].copy()
    if period < 16:
        # subsidy = 0.5
        subsidy_all[:] = 0


    yearly_cons = data['consumption'][:, :, :, :, :, :, :]
    cons_size = np.array([1.5, 1, 0.75])[np.newaxis, np.newaxis, :, np.newaxis, np.newaxis, np.newaxis, np.newaxis]
    battery_size = data['battery_size_adj'][:, :, :, :, 0, 0, 0]
    pgr_idx = titles['battery_data'].index('elec_price_growth')
    price_gr = data['battery_specs'][pgr_idx, 0, 0, 0, 0, 0, 0]
    eff_idx = titles['battery_data'].index('efficiency')
    battery_eff = data['battery_specs'][eff_idx, 0, 0, 0, 0, 0, 0]
    dod_idx = titles['battery_data'].index('depth_of_discharge')
    dod = data['battery_specs'][dod_idx, 0, 0, 0, 0, 0, 0]
    disc_idx = titles['battery_data'].index('discount_rate')
    discount_rate = data['battery_specs'][disc_idx, 0, 0, 0, 0, 0, 0]
    bc_idx = titles['battery_data'].index('battery_cost')
    battery_cost = data['battery_specs'][bc_idx, 0, 0, 0, 0, 0, 0]
    bcp_idx = titles['battery_data'].index('battery_cost_power')
    battery_power_cost = data['battery_specs'][bcp_idx, 0, 0, 0, 0, 0, 0]
    lc_idx = titles['battery_data'].index('labour_cost')
    labour_cost = data['battery_specs'][lc_idx, 0, 0, 0, 0, 0, 0]
    lt_idx = titles['battery_data'].index('lifetime')
    lifetime = data['battery_specs'][lt_idx, 0, 0, 0, 0, 0, 0]

    battery_price_chng = data['battery_price'][2, 0, 0, 0, 0, 0, period]
    battery_cost = battery_cost * battery_price_chng
    battery_power_cost = battery_power_cost * battery_price_chng


    for i, country in enumerate(titles['country']):
        # Get county profiles and solar generation
        adj_profile = data['profiles_adj'][i, :, :, :, 0, :, :]
        adj_pv_gen = data['pv_gen_adj'][i, :, :, :, 0, :, :]
        pv_size = data['pv_size_adj'][i, :, :, :, 0, 0, 0]
        if 'flex' in scenario:
            discharge = data['discharge_baseline'][i, :, :, :, :, :, 0]
            charge = data['charge_baseline'][i, :, :, :, :, :, 0]
        else:
            discharge = data['discharge'][i, :, :, :, :, :, 0]
            charge = data['charge'][i, :, :, :, :, :, 0]
        peak_h = data['peak_h'][i, :, 0, 0, 0, 0, period].astype(int)
        valley_h = data['valley_h'][i, :, 0, 0, 0, 0, period].astype(int)

        subsidy = subsidy_all[i]
        # Calculate PV overproduction
        overprod = adj_pv_gen - adj_profile
        overprod[overprod < 0] = 0
        data['pv_overprod'] = overprod
        
        # Calculate residual load
        residual_demand = adj_profile - adj_pv_gen
        residual_demand[residual_demand < 0] = 0
        # Calculate feed-in from batteries
        grid_feedin = discharge - residual_demand
        grid_feedin[grid_feedin < 0] = 0

        # Calculate actual price
        consumption = data['consumption_adj'][i, :, :, :, 0, 0, 0]
        price = data['electricity_price'][i, :, 0, 0, 0, 0, 0]
        dyn_price = data['dyn_elec_price'][i, :, 0, 0, 0, 0, :]
        feed_in_tariff = data['feed_in_tariff'][i, 0, 0, 0, 0, 0, 0]
        vat = data['vat'][i, 0, 0, 0, 0, 0, 0] / 100


        # Annuity factor for NPV
        annuity_factor = (1 - ((1 + price_gr) / (1 + discount_rate)) ** lifetime) / (discount_rate - price_gr)
        # Price difference between electricity price and feed-in-tariff (benefit from 1 kWh energy stored)
        price_diff = price - feed_in_tariff
        # Total benefits from battery
        # npv_benefit = (discharge * price[np.newaxis, :, np.newaxis] 
        #                - charge * feed_in_tariff) * annuity_factor

        # Total benefits from battery
        # Create dynamic prices for peak hours
        hourly_price = np.ones(24)
        hourly_price = hourly_price[np.newaxis, np.newaxis, np.newaxis, :] * price[np.newaxis, :, np.newaxis, np.newaxis]
        hourly_fit = np.ones(24)
        hourly_fit = hourly_fit[np.newaxis, np.newaxis, np.newaxis, :] * feed_in_tariff
        if 'flex' in scenario:
            npv_benefit = ((((discharge.sum(axis = 3) - grid_feedin.sum(axis = 3)) * dyn_price[np.newaxis, :, np.newaxis, :]) +
                           (grid_feedin.sum(axis = 3) * hourly_fit) - 
                           (charge.sum(axis = 3) * hourly_fit)).sum(axis = 3) + 
                           battery_size[i, :, :, :] * controlled_share * 365 * (price[np.newaxis, :, np.newaxis] - feed_in_tariff)) * annuity_factor

        elif 'peak' in scenario:
            hourly_fit = np.ones_like(hourly_price)
            hourly_fit = hourly_fit * feed_in_tariff
            # Assume that FiT equals to electricity prices at peak hours
            hourly_fit[:, :, :, peak_h]  = dyn_price[np.newaxis, :, np.newaxis, peak_h]
            # hourly_fit = np.minimum(hourly_fit, price.reshape(1, 3, 1, 1))            
            npv_benefit = ((((discharge.sum(axis = 3) - grid_feedin.sum(axis = 3)) * hourly_price) +
                           (grid_feedin.sum(axis = 3) * hourly_fit) - 
                           (charge.sum(axis = 3) * feed_in_tariff)).sum(axis = 3)) * annuity_factor
        elif 'dyn' in scenario:          
            npv_benefit = ((((discharge.sum(axis = 3) - grid_feedin.sum(axis = 3)) * dyn_price[np.newaxis, :, np.newaxis, :]) +
                           (grid_feedin.sum(axis = 3) * hourly_fit) - 
                           (charge.sum(axis = 3) * feed_in_tariff)).sum(axis = 3)) * annuity_factor
        
        else:
            # hourly_fit = np.minimum(hourly_fit, price.reshape(1, 3, 1, 1))            
            npv_benefit = ((((discharge.sum(axis = 3) - grid_feedin.sum(axis = 3)) * hourly_price) +
                           (grid_feedin.sum(axis = 3) * hourly_fit) - 
                           (charge.sum(axis = 3) * feed_in_tariff)).sum(axis = 3)) * annuity_factor
        
        
        
            
            discharge_baseline = data['discharge_baseline'][i, :, :, :, :, :, 0]
            charge_baseline = data['charge_baseline'][i, :, :, :, :, :, 0]
            # Calculate feed-in from batteries
            grid_feedin_baseline = discharge_baseline - residual_demand
            grid_feedin_baseline[grid_feedin_baseline < 0] = 0
            npv_benefit_baseline = ((((discharge_baseline.sum(axis = 3) - grid_feedin_baseline.sum(axis = 3)) * hourly_price) +
                           (grid_feedin_baseline.sum(axis = 3) * hourly_fit) - 
                           (charge_baseline.sum(axis = 3) * feed_in_tariff)).sum(axis = 3)) * annuity_factor
        
            
            # discharge_baseline = data['discharge_baseline'][i, :, :, :, :, :, 0]
            # charge_baseline = data['charge_baseline'][i, :, :, :, :, :, 0]
            # # Calculate feed-in from batteries
            # grid_feedin_baseline = discharge_baseline - residual_demand
            # grid_feedin_baseline[grid_feedin_baseline < 0] = 0
            # npv_benefit_baseline = ((((discharge_baseline.sum(axis = 3) - grid_feedin_baseline.sum(axis = 3)) * hourly_price) +
            #                (grid_feedin_baseline.sum(axis = 3) * hourly_fit) - 
            #                (charge_baseline.sum(axis = 3) * feed_in_tariff)).sum(axis = 3)) * annuity_factor
        
            
            
        
        data['battery_benefit'][i, :, :, :, 0, 0, period] = npv_benefit

        # Adjustment of labour cost with country labour costs
        lab_cost_ratio = data['labour_cost'][i, 0, 0, 0, 0, 0, 0] / data['labour_cost'][:, 0, 0, 0, 0, 0, 0].mean()
        # vat = data['vat'][i, 0, 0, 0, 0, 0, 0] / data['vat'][:, 0, 0, 0, 0, 0, 0].mean()

        # inv = (battery_cost + labour_cost * lab_cost_ratio) * battery_size * (1 - subsidy)

        # Adjustment of cost with country VAT rates
        inv = ((battery_cost * battery_size[i, :, :, :] + battery_power_cost * pv_size / 2) * (1 + vat) + labour_cost * lab_cost_ratio) * (1 - subsidy)
        # inv = (battery_cost * battery_size * (1 + vat) + labour_cost * lab_cost_ratio) * (1 - subsidy)
        # op_cost = (battery_output / 1000 * 1.72 + (pv_size - 0.5) * 5.73) / (discount_rate - price_gr) * annuity_factor
        # Calculae subsidy
        # Assume that realtive subsidy provides subsidy until NPV = 0
        # Therefore covers the subsidy % of the benefits
        subs = npv_benefit / (1 - subsidy) * subsidy
        # subs = (battery_cost + labour_cost * inc_ratio) * battery_size * subsidy
        # Extend investment array with profile_type dimension
        # inv_3d = np.repeat(np.repeat(np.expand_dims(inv, axis = (0, 2)), len(titles['profile_type']), axis = 0), len(titles['azimuth']), axis = 2)
        data['battery_investment'][i, :, :, :, 0, 0, period] = inv # + op_cost
        # subs_2d = np.repeat(np.expand_dims(subs, axis = (0)), len(titles['profile_type']), axis = 0)


        # NPV
        npv = np.subtract(npv_benefit, inv)
        data['battery_npv'][i, :, :, :, 0, 0, period] = npv
        data['battery_subsidy'][i, :, :, :, 0, 0, period] = subs

    return data


def npv_calculation_pv(data, titles, period):

    # Assume no subsidy before 202
    subsidy_all = data['subsidy'][:, 0, 0, 0, 0, 0, 0].copy()
    if period < 16:
        # subsidy = 0.5
        subsidy_all[:] = 0

    # Set main parameters
    yearly_cons = data['consumption'][:, :, :, :, :, :, :]
    cons_size = np.array([1.5, 1, 0.75])[np.newaxis, np.newaxis, :, np.newaxis, np.newaxis, np.newaxis, np.newaxis]
    pgr_idx = titles['pv_data'].index('elec_price_growth')
    price_gr = data['pv_specs'][pgr_idx, 0, 0, 0, 0, 0, 0]
    disc_idx = titles['pv_data'].index('discount_rate')
    discount_rate = data['pv_specs'][disc_idx, 0, 0, 0, 0, 0, 0]
    pvc_idx = titles['pv_data'].index('pv_cost')
    pv_cost = data['pv_specs'][pvc_idx, 0, 0, 0, 0, 0, 0]
    pvopc_idx = titles['pv_data'].index('pv_op_cost')
    pv_op_cost = data['pv_specs'][pvopc_idx, 0, 0, 0, 0, 0, 0]
    lc_idx = titles['pv_data'].index('labour_cost')
    labour_cost = data['pv_specs'][lc_idx, 0, 0, 0, 0, 0, 0]
    lt_idx = titles['pv_data'].index('lifetime')
    lifetime = data['pv_specs'][lt_idx, 0, 0, 0, 0, 0, 0]
    pv_price_chng = data['pv_price'][1, 0, 0, 0, 0, 0, period]
    pv_cost = pv_cost * pv_price_chng
    pv_op_cost = pv_op_cost * pv_price_chng

    for i, country in enumerate(titles['country']):
        # Get county profiles and solar generation
        adj_profile = data['profiles_adj'][i, :, :, :, 0, :, :]
        adj_pv_gen = data['pv_gen_adj'][i, :, :, :, 0, :, :]
        pv_size = data['pv_size_adj'][i, :, :, :, 0, 0, 0]
        subsidy = subsidy_all[i]
        # Calculate PV overproduction
        overprod = adj_pv_gen - adj_profile
        overprod[overprod < 0] = 0
        # Calculate PV self-consumption
        grid_cons = adj_profile - adj_pv_gen
        grid_cons[grid_cons < 0] = 0
        self_cons = adj_profile - grid_cons

        # Calculate actual price
        consumption = data['consumption_adj'][i, :, :, :, 0, 0, 0]
        price = data['electricity_price'][i, :, 0, 0, 0, 0, 0]
        feed_in_tariff = data['feed_in_tariff'][i, 0, 0, 0, 0, 0, 0]
        vat = data['vat'][i, 0, 0, 0, 0, 0, 0] / 100

        # Annuity factor for NPV
        annuity_factor = (1 - ((1 + price_gr) / (1 + discount_rate)) ** lifetime) / (discount_rate - price_gr)
        # Total benefits from battery
        npv_benefit = (self_cons.sum(axis = 3).sum(axis = 3) * price[:, np.newaxis, np.newaxis] + overprod.sum(axis = 3).sum(axis = 3) * feed_in_tariff) * annuity_factor
        gamma = data['gamma'][i, 0, 0, 0, 0, 0, 0]
        data['pv_benefit'][i, :, :, :, 0, 0, period] = npv_benefit + gamma

        # Adjustment of labour cost with country labour costs
        lab_cost_ratio = data['labour_cost'][i, :, 0, 0] / data['labour_cost'][:, :, 0, 0].mean()
        inv = (pv_cost * (1 + vat) + labour_cost * lab_cost_ratio) * pv_size * (1 - subsidy) + annuity_factor * adj_pv_gen.sum(axis = 3).sum(axis = 3) * pv_op_cost

        # Calculae subsidy
        # Assume that realtive subsidy provides subsidy until NPV = 0
        # Therefore covers the subsidy % of the benefits
        subs = npv_benefit / (1 - subsidy) * subsidy
        # subs = (battery_cost + labour_cost * inc_ratio) * battery_size * subsidy
        # Extend investment array with profile_type dimension
        data['pv_investment'][i, :, :, :, 0, 0, period] = inv
        # subs_2d = np.repeat(np.expand_dims(subs, axis = (0)), len(titles['profile_type']), axis = 0)


        # NPV
        npv = np.subtract(npv_benefit, inv)
        data['pv_npv'][i, :, :, :, 0, 0, period] = npv
        data['pv_subsidy'][i, :, :, :, 0, 0, period]= subs

    return data


def potential_population_battery(data, titles, period):

    size_w = np.expand_dims([0.25, 0.5, 0.25], axis = (0, 1, 3))
    azi_w = np.expand_dims([1], axis = (0, 1, 2))

    # p_ratios = data['p'][:, 0, 0, 0, 0, 0, 0] / data['p'][:, 0, 0, 0, 0, 0, 0].mean()
    innovators = 0.025 # * p_ratios

    b_rel_std_idx = titles['battery_data'].index('battery_cost_std')
    battery_cost_rel_std = data['battery_specs'][b_rel_std_idx, 0, 0, 0, 0, 0, 0]

    # Gather relevant variables
    inv_4d = data['battery_investment'][:, :, :, :, 0, 0, period]
    cost_std = inv_4d * battery_cost_rel_std
    benefits = data['battery_benefit'][:, :, :, :, 0, 0, period]

    # Calculate the potential population
    # Use the cumulative distribution function of normal distribution
    # To find the probability of finding a battery with investment cost
    # where NPV is positive
    # + add the share of innovators to the potential population
    pot_population_share = 1 - norm.cdf(inv_4d, benefits, cost_std)

    for reg, country in enumerate(titles['country']):
        reg_pop_share = pot_population_share[reg, :, :, :]
        reg_pop_share[reg_pop_share < innovators] = innovators
        reg_pop_share[reg_pop_share > 1] = 1
        data['battery_potential_pop_share'][reg, :, :, :, 0, 0, period] = reg_pop_share
    # pot_population_share[pot_population_share < innovators] = innovators
    pot_population_share[pot_population_share > 1] = 1
    data['battery_potential_pop_share'][:, :, :, :, 0, 0, period] = pot_population_share


    # Calculate number of households by profile_type
    # Extend house nurmber array with profile_type dimension
    # nr_houses_4d = np.repeat(data['hh_nr'][:, :, :, :, 0, 0, 0], len(titles['profile_type']), axis = 1)
    # nr_houses_4d = np.repeat(nr_houses_4d, len(titles['cons_size']), axis = 2)
    # nr_houses_4d = np.repeat(nr_houses_4d, len(titles['azimuth']), axis = 3)

    # nr_houses_profile = data['profile_shares'][:, :, :, :, 0, 0, 0] * nr_houses_4d
    # nr_houses_profile = size_w * nr_houses_profile
    # nr_houses_profile = azi_w * nr_houses_profile

    # data['nr_houses_profile'][:, :, :, :, 0, 0, period] = nr_houses_profile

    # Potential population where NPV is positive, so they might buy battery
    pot_population = pot_population_share * data['hh_nr'][:, :, :, :, 0, 0, 0]
    data['battery_potential_pop'][:, :, :, :, 0, 0, period] = pot_population

    return data


def potential_population_pv(data, titles, period):

    # p_ratios = data['p'][:, 0, 0, 0, 0, 0, 0] / data['p'][:, 0, 0, 0, 0, 0, 0].mean()
    innovators = 0.025 # * p_ratios

    pv_rel_std_idx = titles['pv_data'].index('pv_cost_std')
    pv_cost_rel_std = data['pv_specs'][pv_rel_std_idx, 0, 0, 0, 0, 0, 0]

    # Gather relevant variables
    inv_4d = data['pv_investment'][:, :, :, :, 0, 0, period]
    cost_std = inv_4d * pv_cost_rel_std
    benefits = data['pv_benefit'][:, :, :, :, 0, 0, period]

    # Calculate the potential population
    # Use the cumulative distribution function of normal distribution
    # To find the probability of finding a battery with investment cost
    # where NPV is positive
    # + add the share of innovators to the potential population
    pot_population_share = 1 - norm.cdf(inv_4d, benefits, cost_std)

    for reg, country in enumerate(titles['country']):
        reg_pop_share = pot_population_share[reg, :, :, :]
        reg_pop_share[reg_pop_share < innovators] = innovators
        reg_pop_share[reg_pop_share > 1] = 1
        data['pv_potential_pop_share'][reg, :, :, :, 0, 0, period] = reg_pop_share
    # pot_population_share[pot_population_share < innovators] = innovators
    pot_population_share[pot_population_share > 1] = 1
    data['pv_potential_pop_share'][:, :, :, :, 0, 0, period] = pot_population_share

    # Potential population where NPV is positive, so they might buy battery
    pot_population = pot_population_share * data['hh_nr'][:, :, :, :, 0, 0, 0]
    data['pv_potential_pop'][:, :, :, :, 0, 0, period] = pot_population

    return data