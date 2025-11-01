# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 23:14:04 2023

@author: adh

input_functions.py
=========================================
Collection of functions written for model inputs.


"""

# Standard library imports
import os
import copy
import sys
import warnings

# Third party imports
import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline

# Local library imports
import support.titles_functions as titles_f
import support.dimensions_functions as dimensions_f
from support.titles_functions import input_file_missing


def load_data(titles, dims, timeline):
    """
    Load all model data for all variables and all years.

    Extended summary here if required.

    Parameters
    ----------
    titles : dict of {str: list}
        Dictionary containing all title classifications.
    dimensions : dict of {str: tuple of (str, str, str, str)}
        Variable classifications by dimension.
    timeline : list of int
        Years of both historical data and forecast period
    scenarios:

    Returns
    ----------
    data_return : dictionary of numpy arrays
        Dictionary containing all required model input variables.
    """



    ##%%
    ##############
    # Read titles
    ##############

    titles['timeline'] = timeline
    titles['timeline_short'] = timeline




    # Create container with the correct dimensions

    data = {v: np.zeros([len(titles[dims[v][d]]) for d in range(7)]) for v in dims}

    # Start reading CSVs
    directory = os.path.join('input', 'Baseline')

    for root, dirs, files in os.walk(directory):

        # Loop through all the files in the directory
        for file in files:
            if file.endswith(".csv"):
                # Read the csv
                read = pd.read_csv(os.path.join(root, file), header=0,
                                   skiprows=3).fillna(0)

                var = file[:-4]
                # print(var)
                if var not in data.keys():
                    msg = 'Variable {} is present in the folder as a csv but is not included in VariableListing, so it will be ignored'.format(var)
                    print(msg)

                else:
                    # Get dimension names and titles
                    dim_nm = list(dims[var])
                    dim_dict = {d: dims[var][d] for d in range(7)}
                    titles_ = {d: list(titles[dims[var][d]]) for d in range(7)}

                    # Get short dimension names and short titles
                    dim_nm_short = [x + '_short' for x in dim_nm]
                    dim_dict_short = {d: dim_nm[d] + '_short' for d in range(7)}
                    titles_short = {d: list(titles[dim_nm_short[d]]) for d in range(7)}

                    # Get length of dimensions
                    len_d = [len(list(titles_.values())[d]) for d in range(7)]
                    len_d = list(np.array(len_d))
                    # Get the nr of dimensions
                    # Get dims that are longer than 1
#                    active_d = [dim for dim, l in len_d.items() if l > 1]
#                    passive_d = [dim for dim, l in len_d.items() if l <= 1]
#                    nr_d = len(active_d)

                    # Check for missing or inconsistent data
                    for dim in dim_nm:
                        if dim != 'NA':
                            print(var)
                            inconsistent_titles = list(set(read[dim].astype(str).unique()) - set(map(str, titles[dim])))
                            if len(inconsistent_titles) > 0:
                                print(f'Inconsistent titles found for dimension {dim} in file {file}')
                    # Sort values to match titles
                    sort_dims = []
                    dim_order = []
                    for dim in dim_nm:
                        if dim != 'NA' and dim != 'date':
                            read[dim] = read[dim].astype("category")
                            # read[dim] = read[dim].cat.set_categories(titles[dim])
                            dim_order.append(dim)
                            sort_dims.append(dim)

                        if dim == 'date':
                            try:
                                read[dim] = pd.to_datetime(read[dim], dayfirst = False)
                            except:
                                read[dim] = pd.to_datetime(read[dim], dayfirst = True)

                            read = read.sort_values('date')
                            dim_order.append(dim)
                            sort_dims.append(dim)


                    dim_order = dim_order + ['Value']
                    read = read[dim_order]
                    read = read.sort_values(sort_dims)
                    if 'timeline' in dim_nm:
                        years = read.timeline.unique()
                        timeline_len_d = len_d
                        timeline_len_d = timeline_len_d[:-1]
                        for y in years:
                            if y in titles['timeline']:
                                y_idx = titles['timeline'].index(y)
                                y_read = read.loc[read.timeline == y, :]
                                data[var][:, :, :, :, :, :, y_idx] = y_read.Value.to_numpy().reshape(timeline_len_d)

                    else:
                        data[var][:, :, :, :, :, :, :] = read.Value.to_numpy().reshape(len_d)



    data_return = copy.deepcopy(data)

    # Return data
    return data_return

def load_converters():
    """ Load model converters."""

    # Declare file name
    conv_file = 'converters.xlsx'

    # Check that converters workbook exists
    conv_path = os.path.join('utilities', conv_file)
    if not os.path.isfile(conv_path):
        input_file_missing(conv_file, conv_path)

    converters = pd.read_excel(conv_path, index_col=0, header=0,
                               sheet_name=None)

    return converters
