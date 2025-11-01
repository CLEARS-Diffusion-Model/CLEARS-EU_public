"""
dimensions_functions.py
=========================================
Functions to load dimensions names.

Functions included:
    - load_dim
        Load model dimensions from the VariablesListing workbook.
"""

# Standard library imports
import os

# Third party imports
import pandas as pd

# Local library imports
from support.titles_functions import input_file_missing


def load_dims():
    """ Load model dimensions from the variables workbook. """

    # Declare file name
    dims_file = 'variables.xlsx'

    # Check that classification titles workbook exists
    dims_path = os.path.join('utilities', dims_file)
    if not os.path.isfile(dims_path):
        input_file_missing(dims_file, dims_path)

    dims_wb = pd.ExcelFile(dims_path)
    sn = dims_wb.sheet_names

    # Iterate through worksheets and add to titles dictionary
    dims = {}
    histend = {}
    for sheet in sn:
        active = dims_wb.parse(sheet, keep_default_na=False, na_values='')
        for i, value in active.iterrows():
            dims[value[0]] = tuple(value[3:10])
            histend[value[0]] = value[12]

    # Return titles dictionary
    return dims, histend
