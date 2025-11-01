# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 21:11:06 2023

@author: adh
"""


import pandas as pd
import numpy as np
import os
import itertools

# os.chdir("C:/Users/adh/OneDrive - Cambridge Econometrics/ADH CE/Phd/ÚNKP_2023/data")


def Bass_param_estimation(data, titles):

    validation_years = [int(year) for year in titles['pv_hist_year']]
    start_year = int(min(data['battery_start_year']))
    # Create datafrane for PVs
    pv = pd.DataFrame(0, index = titles['country'], columns = range(start_year, max(validation_years)))
    pv[validation_years] = data['battery_hist'][:, :, 0, 0, 0, 0, 0]
    # Annual PV installations
    pv_diff = pv.diff(axis = 1)
    # Potential population for PVs
    nr_houses = pd.Series(data['hh_nr'][:, :, :, :, 0, 0, 0].sum(axis = 1).sum(axis = 1).sum(axis = 1), index = titles['country'])

    # Create grid for parameter tuning
    # Getting all permutations of list_1
    # with length of list_2
    qs = np.array([i / 1000 for i in list(range(1, 701, 10))])**2
    ps= np.array([i / 10000 for i in range(1, 701, 10)])**2
    c = list(itertools.product(qs, ps))

    p_list = []
    q_list = []

    for cty, cty_pv in pv.iterrows():
        i = titles['country'].index(cty)
        # Change t0 depending on the number of PVs in first year
        first_year = int(data['battery_start_year'][i, 0, 0, 0, 0, 0, 0])
        validation_years = list(range(first_year, 2025))
        m = nr_houses[i]

        df = pd.DataFrame(0, columns = range(first_year, 2025), index = c)


        for ix, ind in enumerate(df.index):
            # p is the coefficient of innovation
            # q is the coefficient of imitation
            q = ind[0]
            p = ind[1]

            pred = []
            for t in df.columns:
                t = int(t) - first_year + 1
                # Estimate diffusion with p, q combination
                pred_t = (m * (1 - np.exp(-(p+q)*(t)))/(1+q/p*np.exp(-(p+q)*(t))))
                pred = pred + [pred_t]

            df.iloc[ix, :] = pred

        # Find the p and q combination with the smallest squared error
        min_ind = np.argmin((df[validation_years].subtract(cty_pv[validation_years], axis = 1) ** 2).sum(axis = 1))
        min_values = df.index[min_ind]
        q = min_values[0]
        p = min_values[1]
        q_list = q_list + [q]
        p_list = p_list + [p]

        print('    Innovation and imitation parameters for', cty)
        print('      p:', p)
        print('      q:', q)

        # pred = []
        # for t in range(2008, 2023):
        #     t = t - 2007
        #     pred_t = (m * (1 - np.exp(-(p+q)*(t-t0)))/(1+q/p*np.exp(-(p+q)*(t-t0))))
        #     pred = pred + [pred_t]

        # test = pd.Series(pred, index = range(2008, 2023))
        # test.plot()


        # pred = []
        # for t in range(2008, 2051):
        #     t = t - 2007 + t0
        #     pred_t = (m*(1 - np.exp(-(p+q)*(t-t0)))/(1+q/p*np.exp(-(p+q)*(t-t0))))
        #     pred = pred + [pred_t]

        # test = pd.Series(pred, index = range(2008, 2051))
        # test.plot()
        # reg_pv.plot()

    data['battery_p'][:, 0, 0, 0, 0, 0, 0] = p_list
    data['battery_q'][:, 0, 0, 0, 0, 0, 0] = q_list

    return data


def simulate_diffusion_battery(data, titles, year, period, f):

    battery_cum_lag = data['battery_cum'][:, :, :, :, f, 0, period - 1]
    battery_cum_lag2 = data['battery_cum'][:, :, :, :, f, 0, period - 2]

    # t0 = simulation_start
    # t_current = year - simulation_start

    if year <= 2024:
        if str(year) in list(titles['pv_hist_year']):
            hist_idx = titles['pv_hist_year'].index(str(year))
            for i, country in enumerate(titles['country']):
                # Distribute PV based on potential population
                battery_cum = data['battery_hist'][i, hist_idx, 0, 0, 0, 0, 0]
                m = data['battery_potential_pop'][i, :, :, :, 0, 0, period]
                # Use different size weights for history
                # Assume that higher share of the installations belong to large consumers
                hist_size_w = np.array([0.25, 0.5, 0.25])
                azi_w = np.array([1])
                prof_shares = data['profile_shares'][i, :, 0, 0, 0, 0, 0]
                m_shares = prof_shares[:, np.newaxis, np.newaxis] * hist_size_w[np.newaxis, :, np.newaxis] * azi_w[np.newaxis, np.newaxis, :]
                data['battery_cum'][i, :, :, :, f, 0, period] = battery_cum * m_shares
                if year >= 2022:
                    battery_new = battery_cum * m_shares - battery_cum_lag[i, :, :, :]
                    battery_new[battery_new < 0] = 0
                    data['battery_new'][i, :, :, :, f, 0, period] = battery_new

    else:

        for i, country in enumerate(titles['country']):
            # Check if there is forecast data
            if year < 2030:
                forecast_idx = titles['forecast_year'].index(str(year))
            else:
                forecast_idx = 0
            # If there is forecast data then calculate number of adopters from that
            if (data['battery_market_forecast'][i, forecast_idx, 0, 0, 0, 0, 0] > 0) and (year < 2030):
                # Distribute battery based on potential population
                m = data['battery_potential_pop'][i, :, :, :, 0, 0, period]
                # Use different size weights for history
                # Assume that higher share of the installations belong to large consumers
                hist_size_w = np.array([0.25, 0.5, 0.25])
                azi_w = np.array([1])
                prof_shares = data['profile_shares'][i, :, 0, 0, 0, 0, 0]
                m_shares = prof_shares[:, np.newaxis, np.newaxis] * hist_size_w[np.newaxis, :, np.newaxis] * azi_w[np.newaxis, np.newaxis, :]
                data['battery_new'][i, :, :, :, f, 0, period] = (data['battery_market_forecast'][i, forecast_idx, 0, 0, 0, 0, 0] / 
                                                                 data['battery_size_adj'][i, :, :, :, 0, 0, 0]) * 1000 * m_shares
            # If there is no forecast data then use Bass model
            else:
                p = data['battery_p'][i, 0, 0, 0, 0, 0, 0]
                q = data['battery_q'][i, 0, 0, 0, 0, 0, 0]
        
                m = data['battery_potential_pop'][i, :, :, :, 0, 0, period]
                country_bat_lag = battery_cum_lag[i, :, :, :].sum()
                country_bat_lag2 = battery_cum_lag2[i, :, :, :].sum()

                # Find diffusion year
                t_sim = np.array(range(0, 500)) / 10
                m_total = m.sum()
        
        
                pred_sim = (m_total * (1 - np.exp(-(p+q)*(t_sim)))/(1+q/p*np.exp(-(p+q)*(t_sim))))
        
                # Find closest value
                t_prev = np.argmin(abs(pred_sim - country_bat_lag))
                t_prev2 = np.argmin(abs(pred_sim - country_bat_lag2))
                t = (t_prev + t_prev2) / 2 / 10 + 1.5
    
        
                # Estimate diffusion
                pred_t = (m * (1 - np.exp(-(p+q)*(t)))/(1+q/p*np.exp(-(p+q)*(t))))
                # if t > t0:
                #     pred_lag = (m * (1 - np.exp(-(p+q)*(t_lag-t0)))/(1+q/p*np.exp(-(p+q)*(t_lag-t0))))
                # else:
                #     pred_lag = np.zeros(len(titles['profile_type']))
                # Calculate new batteries
                battery_new = pred_t - battery_cum_lag[i, :, :, :]
                battery_new[battery_new < 0] = 0
                data['battery_new'][i, :, :, :, f, 0, period] = battery_new

    
        # Remove batteries over their lifetime
        lt_idx = titles['battery_data'].index('lifetime')
        lifetime = data['battery_specs'][lt_idx, 0, 0, 0, 0, 0, 0]
        scrap_year = int(period - lifetime)
        battery_new = data['battery_new'][:, :, :, :, f, 0, period]
        if scrap_year > 0:
            battery_scrap = data['battery_new'][:, :, :, :, f, 0, scrap_year]
            data['battery_scrap'][:, :, :, :, 0, 0, period] = battery_scrap
            data['battery_cum'][:, :, :, :, f, 0, period] = battery_cum_lag + battery_new #- battery_scrap
        else:
            data['battery_cum'][:, :, :, :, f, 0, period] = battery_cum_lag + battery_new
        # Limit the number of battery adopters by the number of PV adopters
        # if np.any(data['battery_cum'][:, :, :, :, f, 0, period] > data['pv_cum'][:, :, :, :, f, 0, period]):
        #     limit_battery_adopters = np.minimum(data['battery_cum'][:, :, :, :, f, 0, period], data['pv_cum'][:, :, :, :, f, 0, period])
        #     data['battery_new'][:, :, :, :, f, 0, period] -= data['battery_cum'][:, :, :, :, f, 0, period] - limit_battery_adopters
        #     data['battery_cum'][:, :, :, :, f, 0, period] = limit_battery_adopters

    # Calculate share of battery owners
    hh_shares = data['hh_share'][:, :, :, :, 0, 0, 0]
    nr_houses = hh_shares * data['hh_nr'][:, :, :, :, 0, 0, 0]
    data['battery_share'][:, :, :, :, f, 0, period] = data['battery_cum'][:, :, :, :, f, 0, period] / nr_houses
    return data


def simulate_pv_diffusion(data, titles, year, period, f):


    pv_cum_lag = data['pv_cum'][:, :, :, :, f, 0, period - 1]
    # t0 = simulation_start
    # t_current = year - simulation_start


    if year <= 2024:
        if str(year) in list(titles['pv_hist_year']):
            hist_idx = titles['pv_hist_year'].index(str(year))
            for i, country in enumerate(titles['country']):
                # Distribute PV based on potential population
                pv_cum = data['pv_hist'][i, hist_idx, 0, 0, 0, 0, 0]
                m = data['pv_potential_pop'][i, :, :, :, 0, 0, period]
                # Use different size weights for history
                # Assume that higher share of the installations belong to large consumers
                hist_size_w = np.array([0.25, 0.5, 0.25])
                azi_w = np.array([1])
                prof_shares = data['profile_shares'][i, :, 0, 0, 0, 0, 0]
                m_shares = prof_shares[:, np.newaxis, np.newaxis] * hist_size_w[np.newaxis, :, np.newaxis] * azi_w[np.newaxis, np.newaxis, :]
                data['pv_cum'][i, :, :, :, f, 0, period] = pv_cum * m_shares
                if year >= 2022:
                    data['pv_new'][i, :, :, :, f, 0, period] = pv_cum * m_shares - pv_cum_lag[i, :, :, :]

    else:
        for i, country in enumerate(titles['country']):
            p = data['pv_p'][i, 0, 0, 0, 0, 0, 0]
            q = data['pv_q'][i, 0, 0, 0, 0, 0, 0]

            m = data['pv_potential_pop'][i, :, :, :, 0, 0, period]
            country_pv_lag = pv_cum_lag[i, :, :, :].sum()
            # Find diffusion year
            t_sim = np.array(range(0, 500)) / 10
            m_total = m.sum()


            pred_sim = (m_total * (1 - np.exp(-(p+q)*(t_sim)))/(1+q/p*np.exp(-(p+q)*(t_sim))))

            # Find closest value
            t_prev = np.argmin(abs(pred_sim - country_pv_lag))
            t = t_prev / 10 + 1

            # if country == 'Pest':
                # print('    Potential population:', country, ':', m_total)
                # print('    Diffusion year', country, ':', t)

            # Estimate diffusion
            pred_t = (m * (1 - np.exp(-(p+q)*(t)))/(1+q/p*np.exp(-(p+q)*(t))))
            # if t > t0:
            #     pred_lag = (m * (1 - np.exp(-(p+q)*(t_lag-t0)))/(1+q/p*np.exp(-(p+q)*(t_lag-t0))))
            # else:
            #     pred_lag = np.zeros(len(titles['profile_type']))
            # Calculate new batteries
            new = pred_t - pv_cum_lag[i, :, :, :]
            new[new < 0] = 0
            data['pv_new'][i, :, :, :, f, 0, period] = new

        # Remove batteries over their lifetime
        lt_idx = titles['pv_data'].index('lifetime')
        lifetime = data['pv_specs'][lt_idx, 0, 0, 0, 0, 0, 0]
        scrap_year = int(period - lifetime)
        pv_new = data['pv_new'][:, :, :, :, f, 0, period]
        if scrap_year > 0:
            pv_scrap = data['pv_new'][:, :, :, :, f, 0, scrap_year]
            data['pv_scrap'][:, :, :, :, 0, 0, period] = pv_scrap
            data['pv_cum'][:, :, :, :, f, 0, period] = pv_cum_lag + pv_new #- battery_scrap
        else:
            data['pv_cum'][:, :, :, :, f, 0, period] = pv_cum_lag + pv_new
    # Calculate share of battery owners
    data['pv_share'][:, :, :, :, f, 0, period] = data['pv_cum'][:, :, :, :, f, 0, period] / data['hh_nr'][:, :, :, :, 0, 0, 0]
    return data
