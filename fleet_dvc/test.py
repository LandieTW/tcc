
from collections import Counter
import os
from openpyxl import load_workbook
from glob import glob

'Suggestion for initial configuration'
rl_config = [
    [3, 6],         # Positions [m]
    [1800, 1000]      # Submerged mass [kg]
    ]

'Submerged mass limit, in kg, for buoys'
BUOYANCY_LIMIT = 2_000
SMALL_BUOY = 100

'Number of buoyancy increments for 1st addition of buoys in the model'
N_INCREMENT = 5

'Maximum number of buoys for each position'
N_BUOYS_POS = 2     # automation changes it to 3, if doesn't find a solution

'This file path'
THIS_PATH = os.path.dirname(os.path.abspath(__file__))

'Excel sheets'
SHEET_PATH = os.path.join(THIS_PATH, glob(os.path.join(THIS_PATH, "*.xlsm"))[0])

EXCEL = load_workbook(filename=SHEET_PATH, data_only=True)
VALUES_SHEET = EXCEL['Values']
MCV_SHEET = EXCEL['MCV e Guindaste']
RESULTS_SHEET = EXCEL['Results']

'Vessels set of buoys'
CDA_BUOYS = [1252, 1252, 1252, 973, 828, 573, 573, 573, 283, 283, 283, 205, 205, 205, 205, 118, 118, 118, 118, 118, 118]
SKA_BUOYS = [1416, 1376, 1345, 1323, 1320, 871, 741, 741, 660, 647, 381, 377, 155, 104, 101, 100]
SKB_BUOYS = [1508, 1451, 1428, 1425, 1416, 1320, 760, 726, 708, 385]
SKN_BUOYS = [1000, 1000, 1000, 1000, 1000, 500, 500, 500, 343, 100, 100, 100, 100, 100]
SKO_BUOYS = [1213, 1213, 1213, 1213, 1213, 576, 576, 576, 576, 576, 381, 381, 381,381,381, 100, 100, 100, 100, 100]
SKR_BUOYS = [1000, 1000, 1000, 1000, 1000, 500, 500, 500, 250, 250, 100, 100, 100, 100, 100]
SKV_BUOYS = [1000, 1000, 1000, 1000, 1000, 500, 500, 500, 300, 100, 100, 100, 100, 100]

VESSEL_BUOYS = {
    'Skandi Niterói': [list(Counter(SKN_BUOYS).keys()), list(Counter(SKN_BUOYS).values())], 
    'Skandi Búzios': [list(Counter(SKB_BUOYS).keys()), list(Counter(SKB_BUOYS).values())], 
    'Skandi Açu': [list(Counter(SKA_BUOYS).keys()), list(Counter(SKA_BUOYS).values())], 
    'Skandi Vitória': [list(Counter(SKV_BUOYS).keys()), list(Counter(SKV_BUOYS).values())], 
    'Skandi Recife': [list(Counter(SKR_BUOYS).keys()), list(Counter(SKR_BUOYS).values())], 
    'Skandi Olinda': [list(Counter(SKO_BUOYS).keys()), list(Counter(SKO_BUOYS).values())], 
    'Coral do Atlântico': [list(Counter(CDA_BUOYS).keys()), list(Counter(CDA_BUOYS).values())]
    }

def buoy_combination(b_set: list) -> dict:
    """
    Description:

        Receive: [[buoys - b1, b2, b3, ...], [quantity - q1, q2, q3, ...]]
        Return: {'100+150': 250, '200+100': 300, ... }

        Generate all possible buoy's combination, considering:
        1 - Each combination must have, at maximum, n_buoys buoys.
        2 - Each combination must have less than buoyancy_limit of submerged mass.
        3 - Combinations with 3 buoys must have at least one buoy ≤ small_buoy_limit.
    Parameter:
        set_of_buoys (list): The available vessel buoys, in the format [[quantities], [buoyancies]].
    Returns:
        dict: A dictionary with all possible buoy combinations.
    """
    
    

def buoyancy(buoy_config: list, vessel_name: str) -> dict:
    """
    Description:
        Select the best set of buoys from the available vessel stock that fits buoy_config,
        while ensuring the selection does not exceed the available quantity.
    Parameters:
        buoy_config: Suggestion for buoy configuration.
        vessel_name: Name of the vessel whose buoys will be used.
    Return:
        selection: Group of buoys that fits buoy_config within the vessel's available stock.
    """
    
    set_of_buoys = VESSEL_BUOYS[vessel_name]    # [[buoys - b1, b2, b3, ...], [quantity - q1, q2, q3, ...]]
    
    # Generate all valid buoy combinations
    combination_buoys = buoy_combination(set_of_buoys)  # { '100+150': 250, '200+100': 300, ... }
    
    return selection

# define set of buoys
vessel_name = RESULTS_SHEET['C6'].value

# select the best set of buoys of combined_buoys that fits the rl_config_partial
selection = buoyancy(rl_config, vessel_name)    # {'973+828': 1801.0, '573+573': 1146.0}

print(selection)
