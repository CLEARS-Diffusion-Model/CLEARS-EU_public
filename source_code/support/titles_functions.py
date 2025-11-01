# -*- coding: utf-8 -*-
"""
titles_functions.py
=========================================
Functions to load classification titles.

Functions included in the file:
    - load_titles
        Load model classifications and titles.
"""

# Standard library imports
import os
import sys
# Third party imports
import pandas as pd

# Local library imports
#from support.input_functions import input_file_missing


def load_titles():
    """ Load model classifications and titles. """
    # Declare file name
    titles_file = 'classification_titles.xlsx'

    # Check that classification titles workbook exists
    titles_path = os.path.join('utilities', titles_file)
    if not os.path.isfile(titles_path):
        input_file_missing(titles_file, titles_path)

    titles_wb = pd.ExcelFile(titles_path)
    sn = titles_wb.sheet_names
    sn.remove('Cover')

    # Iterate through worksheets and add to titles dictionary
    titles = {}
    for sheet in sn:
        active = titles_wb.parse(sheet, keep_default_na=False, na_values='')
        for i, value in active.items():
            if value.name == 'Full name':
                titles['{}'.format(sheet)] = tuple(value[0:].astype(str))
            if value.name == 'Short name':
                titles['{}_short'.format(sheet)] = tuple(value[0:])
            if value.name == 'Initials':
                titles['{}_initials'.format(sheet)] = tuple(value[0:])

    # Return titles dictionary
    return titles


def input_file_missing(file, filepath):
    """ Print information for a given missing input file, and exit run. """

    print('Input file missing')
    print('File: {}'.format(file))
    print('Filepath: {}'.format(filepath))

    sys.exit('Model run terminated. See error above.')

    return None

if __name__ == "__main__":

    # This is blank. Here for testing.
    print('hello world')
