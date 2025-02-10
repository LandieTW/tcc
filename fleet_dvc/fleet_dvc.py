"""
LTC DVC ANALYSIS
(AUTOMATION FOR CASES 2, 3I, 3II, AND CONTINGENCY)

OBJECTIVE:
    This script aims to define a configuration that verticalizes the VCM under static conditions to align it with the subsea equipment hub.
    Then, it runs dynamic simulations to verify whether the VCM flange loads are within admissible limits.
    Additionally, it assesses the feasibility of contingency cases.

To achieve this, two alternatives are provided:
    ALTERNATIVE 1: The user inputs some data directly into the script.
    ALTERNATIVE 2: The user inputs data in the DVC sheet file.

DATA INPUTS REQUIRED FOR AUTOMATION:
    - Structural analysis limits from the Petrobras report.
    - Bathymetric variation (for dredging cases).
        Note: The user can modify it directly in the 'Estatico.dat' file or input it in the script.
    - Available vessel buoys (if different from the data below).
    - Flexible pipe section length (for jumper DVC analysis).

UPDATE IDEAS
    - Study how to improove convergence when calculating statics convergences, to avoid the max iteration limit.
    - Create a function that model the dredging points
"""

# INPUTS ------------------------------------------------------------------

# 1st suggestion for initial configuration
rl_config = [
    [3, 6],         # Positions [m]
    [800, 400]      # Submerged mass [kg]
    ]

# LIBRARIES ---------------------------------------------------------------

import time
import os
import sys
import warnings
from collections import Counter
from collections import defaultdict
from io import StringIO
from openpyxl import load_workbook
import OrcFxAPI as orca

# CONSTANTS ---------------------------------------------------------------

'Ignoring openpyxl user_warning'
warnings.simplefilter("ignore", UserWarning)

'Vessels set of buoys'
CDA_BUOYS = [1252, 1252, 1252, 973, 828, 573, 573, 573, 283, 283, 283, 205, 205, 205, 205, 118, 118, 118, 118, 118, 118, 100]
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
VESSEL_INITIALISM = {
        'Skandi Niterói': 'SKN',
        'Skandi Búzios': 'SKB',
        'Skandi Açu': 'SKA',
        'Skandi Vitória': 'SKV',
        'Skandi Recife': 'SKR',
        'Skandi Olinda': 'SKO',
        'Coral do Atlântico': 'CDA'
        }

'Static calculation counter'
N_RUN = 0

'Static calculation counter limit'
N_RUN_LIMIT = 25

'Number of decimal places'
DECIMAL = 2

'Maximum number of iterations'
STATICS_MAX_ITERATIONS = 400

'Damping range for static convergence'
STATICS_MIN_DAMPING = 1
STATICS_MAX_DAMPING = 10

'Error correction counter'
N_RUN_ERROR = 0

'VCMs rotation, in degrees'
ROTATION = 0

'Line to soil clearance, in metters'
CLEARANCE = 0

'Elements displacing, in metters'
DISPLACING_X = 25

'MCV flange height error, in metters'
DELTA_FLANGE = 0

'Submerged mass limit, in kg, for a combination of buoys'
BUOYANCY_LIMIT = 2_000

'Submerged mass limit, in kg for a small buoy'
SMALL_BUOY = 100

'Number of buoyancy increments for 1st addition of buoys in the model'
N_INCREMENT = 5

'Maximum number of buoys for each position'
N_BUOYS = 2     # automation changes it to 3, if doesn't find a solution

'Heave up magnitudes, in metters'
HEAVE_UP = [2.5, 2.0, 1.8, 1.5]

'This file path'
THIS_PATH = os.path.dirname(os.path.abspath(__file__))

'Excel sheets'
SHEET_PATH = os.path.join(THIS_PATH, [sheet 
                                      for sheet in os.listdir(THIS_PATH) 
                                      if sheet.endswith(".xlsm")][0])
EXCEL = load_workbook(filename=SHEET_PATH, data_only=True)

VALUES_SHEET = EXCEL['Values']
MCV_SHEET = EXCEL['MCV e Guindaste']
RESULTS_SHEET = EXCEL['Results']

'Analysis paths'
STATIC_PATH = os.path.join(THIS_PATH, "Estatico.dat")
RT_NUMBER = RESULTS_SHEET['C21'].value
RT_PATH = os.path.join(THIS_PATH, RT_NUMBER)
RT_DIR = os.makedirs(RT_PATH, exist_ok=True)

RT_STATIC_PATH = os.path.join(RT_PATH, "1. Static")
RT_STATIC_DIR = os.makedirs(RT_STATIC_PATH, exist_ok=True)

RT_DYNAMIC_PATH = os.path.join(RT_PATH, "2. Dynamic")
RT_DYNAMIC_DIR = os.makedirs(RT_DYNAMIC_PATH, exist_ok=True)

RT_CONTINGENCY_PATH = os.path.join(RT_PATH, "3. Contingency")
RT_CONTINGENCY_DIR = os.makedirs(RT_CONTINGENCY_PATH, exist_ok=True)

# CLASSES -----------------------------------------------------------------

class DualOutput:
    """
    Description:
        This class is used to print in console and save in a buffer at the same time.
    """

    def __init__(self, original_stdout, buffer):
        self.original_stdout = original_stdout
        self.buffer = buffer

    def write(self, message):
        """
        Description:
            This method writes the message in the console and in the buffer.
        """
        self.original_stdout.write(message)
        self.buffer.write(message)

    def flush(self):
        """
        Description:
            This method flushes (force) the buffer.
        """
        self.original_stdout.flush()

# METHODS -----------------------------------------------------------------

def run_static_before_looping(
        model: orca.Model,
        general: orca.OrcaFlexObject,
        env: orca.OrcaFlexObject,
        line: orca.OrcaFlexObject,
        vcm: orca.OrcaFlexObject,
        water_depth: float,
        vcm_height: float,
        ini_time: float,
        ) -> None:
    """
    Description:
        Runs static simulation before the 'looping'.
    Parameters:
        model: OrcaFlex model
        general: OrcaFlex general
        env: OrcaFlex environmental conditions
        line: Flexible pipe
        vcm: Vertical connection module
        water_depth: Water depth
        vcm_height: flange to soil height, in mm
        ini_time: Static calculation start time, in seconds
    """
    try:
        global N_RUN_ERROR, ROTATION, CLEARANCE, DELTA_FLANGE

        vcm.DegreesOfFreedomInStatics = 'X,Y,Z'
        model.CalculateStatics()

        model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)

        vcm.DegreesOfFreedomInStatics = 'All'
        model.CalculateStatics()

        # necessary verification to avoid crazy convergences...
        line_nc = verify_normalised_curvature(line, 'Mean')
        if line_nc > .75:
            model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
            line.StaticsStep1 = "Catenary"
            model.CalculateStatics()
        
        # end time for calculate statics
        end_time = time.time()
        print(f"\nTime: {end_time - ini_time}s")

        ROTATION = round(vcm.StaticResult("Rotation 2"), DECIMAL)
        CLEARANCE = verify_clearance(line)
        DELTA_FLANGE = verify_flange_height(line, water_depth, vcm_height)

        print(f"Rotation: {ROTATION}")
        print(f"Clearance: {CLEARANCE}")

        # default error count
        N_RUN_ERROR = 0

        # Saving simularion
        model.SaveSimulation(RT_STATIC_PATH)
    
    except Exception:

        error_treatment(general, env, line, vcm)

        run_static_before_looping(model, general, env, line, vcm, water_depth, vcm_height, ini_time)

def verify_normalised_curvature(
        element: orca.OrcaFlexObject,
        magnitude: str,
        ) -> float:
    """
    Description:
        Verify element's normalised curvature value
    Parameters:
        element: OrcaFlex object (Line or bend restrictor)
        magnitude: 'Mean' for static calculation and 'Max' for simulation
    Returns:
        Element's normalised curvature value
    """
    if magnitude == 'Mean':
        n_curve = element.RangeGraph('Normalised curvature')
        nc = [nc for _, nc in enumerate(n_curve.Mean)]      # Static calculation
    
    elif magnitude == 'Max':
        n_curve = element.RangeGraph('Normalised curvature', period=orca.PeriodNum.WholeSimulation)
        nc = [nc for _, nc in enumerate(n_curve.Max)]       # Simulation
    
    return round(max(nc), DECIMAL)

def verify_clearance(
        element: orca.OrcaFlexObject
        ) -> float:
    """
    Description:
        Verify element's clearance value, in metters
    Parameters:
        element: OrcaFlex object (Line, and others)
    Returns
        Element's clearance value
    """
    clearance = element.RangeGraph('Seabed clearance')
    seabed_clearance = [sc for _, sc in enumerate(clearance.Mean)]

    return round(min(seabed_clearance), DECIMAL)

def verify_flange_height(
        element: orca.OrcaFlexObject,
        water_depth: float,
        vcm_height: float,
        ) -> float:
    """
    Description:
        Verify flange's height error, in metters.
    Parameters:
        element: OrcaFlex object (Line, and others)
        water_depth: water depth, in metters
        vcm_height: flange to soil height, in mm
    Returns:
        Flange's height error
    """
    correct_depth = - water_depth + vcm_height / 1_000
    depth_verified = element.StaticResult('Z', orca.oeEndB)
    return round(correct_depth - depth_verified, DECIMAL)

def error_treatment(
        general: orca.OrcaFlexObject,
        env: orca.OrcaFlexObject,
        line: orca.OrcaFlexObject,
        vcm: orca.OrcaFlexObject,
        ):
    """
    Description:
        Tentatives to get convergence in static calculation, after it fails 
    Parameters:
        general: OrcaFlex general config.
        env: OrcaFlex environmental conditions
        line: Flexible pipe
        vcm: Vertical connection module
    """
    global N_RUN_ERROR, N_RUN, N_RUN_LIMIT

    if N_RUN_ERROR == 0:
        print(f"\nERROR\nIncreasing 5 times the Static Damping Range")
        general.StaticsMinDamping = 10 * STATICS_MIN_DAMPING
        general.StaticsMaxDamping = 10 * STATICS_MAX_DAMPING

    if N_RUN_ERROR == 1:
        if CLEARANCE <= 0:
            print(f"\nERROR\nRemoving interation between line and seabed")
            env.SeabedNormalStiffness = 0
        else:
            N_RUN_ERROR += 1

    if N_RUN_ERROR == 2:
        print(f"\nERROR\nChanging Line's Static policy to Catenary.")
        line.StaticsStep1 = "Catenary"

    if N_RUN_ERROR == 3:
        print(f"\nERROR\nDisplacing VCM")
        vcm.InitialX -= DISPLACING_X

    if N_RUN_ERROR == 4:
        print(f"\nERROR\nIncreasing 5 times the Number of iterations")
        general.StaticsMaxIterations = 10 * STATICS_MAX_ITERATIONS

    if N_RUN_ERROR == 5:
        N_RUN = N_RUN_LIMIT + 1

    N_RUN_ERROR += 1

def user_specified(
        model: orca.Model,
        id: str,
        path: str,
        ):
    """
    Description:
        Set calculated positions in line's static-step policy
        and saves the convergence case
    Parameters:
        model: OrcaFlex model
        id: analysis id
        path: directory path
    """
    model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
    file_name = id + '.dat'
    save_path = os.path.join(path, file_name)
    model.SaveData(save_path)

def buoy_combination(b_set: list) -> dict:
    """
    Description:
        Generate all possible buoy's combination, considering:
        1 - Each combination must have, at maximum, n_buoys buoys.
        2 - Each combination must have less than buoyancy_limit of submerged mass.
        3 - Combinations with 3 buoys must have at least one buoy ≤ small_buoy_limit.
    Parameter:
        set_of_buoys (list): The available vessel buoys, in the format [[quantities], [buoyancies]].
    Returns:
        dict: A dictionary with all possible buoy combinations.
    """
    # Creating a list of buoys with repeated elements based on their frequency
    buoys = [str(b_set[0][i]) for i in range(len(b_set[0])) for _ in range(b_set[1][i])]
    
    small_buoys = [b for b in buoys if float(b) <= SMALL_BUOY]

    # One buoy combinations
    one_buoy = {buoy: float(buoy) for buoy in buoys}

    # Two buoy combinations
    two_buoys = {}
    for i, buoy1 in enumerate(buoys):
        for _, buoy2 in enumerate(buoys[i+1:], start=i+1):  # Avoid repeating combinations
            combined_buoy = one_buoy[buoy1] + one_buoy[buoy2]
            if combined_buoy <= BUOYANCY_LIMIT:
                two_buoys[f"{buoy1}+{buoy2}"] = combined_buoy

    # Three buoy combinations (with at least one small buoy)
    three_buoys = {}
    for i, buoy1 in enumerate(buoys):
        for _, buoy2 in enumerate(buoys[i+1:], start=i+1):  # Avoid repeating combinations
            for small_buoy in small_buoys:                  # 3st buoy has to be a small buoy
                combined_buoy = one_buoy[buoy1] + one_buoy[buoy2] + float(small_buoy)
                if combined_buoy <= BUOYANCY_LIMIT:
                    three_buoys[f"{buoy1}+{buoy2}+{small_buoy}"] = combined_buoy

    # Combine all based on n_buoys
    combination = {}
    if n_buoys == 2:
        combination.update(one_buoy)
        combination.update(two_buoys)
    elif n_buoys == 3:
        combination.update(one_buoy)
        combination.update(two_buoys)
        combination.update(three_buoys)
    
    return dict(sorted(combination.items(), key=lambda item: item[1], reverse=False))

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
    
    set_of_buoys = VESSEL_BUOYS[vessel_name]
    available_buoys = dict(zip(set_of_buoys[0], set_of_buoys[1]))
    selection = {}
    
    # Generate all valid buoy combinations
    combination_buoys = buoy_combination(set_of_buoys)  # { '100+150': 250, '200+100': 300, ... }
    sorted_combinations = sorted(combination_buoys.items(), key=lambda x: x[1])  # Sort by total buoyancy
    
    for required_buoyancy in buoy_config[1]:
        original_required = required_buoyancy  # Store original value for reference
        
        while required_buoyancy >= 0.9 * original_required:
            best_combo = None
            
            for combo, total_buoyancy in sorted_combinations:
                if total_buoyancy >= required_buoyancy:
                    selected_boias = list(map(int, combo.split('+')))
                    
                    # Verify stock availability
                    temp_available = available_buoys.copy()
                    valid_selection = True
                    
                    for buoy in selected_boias:
                        if temp_available.get(buoy, 0) > 0:
                            temp_available[buoy] -= 1
                        else:
                            valid_selection = False
                            break
                    
                    if valid_selection:
                        best_combo = combo
                        available_buoys = temp_available  # Update stock
                        break  # Stop searching once a valid option is found
            
            if best_combo:
                selection[best_combo] = combination_buoys[best_combo]
                break  # Move to the next required buoyancy
            
            # Reduce the required buoyancy by 10% if no valid combination was found
            required_buoyancy *= 0.9
    
    return selection

def buoys_treatment(
        rl_config: list, 
        selected_buoys: dict,
        name: str,
        ) -> dict:
    """
    Description:
        Get the Dict result (selection) from 'buoyancy' and transforms it in Orcaflex attachments
    Parameters:
        rl_config: configuration suggested
        selected_buoys: selected buoys
        name: Vessel's name
    Return:
        Orcaflex attachments equivalents to selection
    """
    initialism = VESSEL_INITIALISM[name]

    keys = [[f"{initialism}_{subkey}" 
             for subkey in key.split("+")] 
             for key in selected_buoys.keys()]

    return {
        rl_config[0][i]: keys[i]
        for i in range(len(keys))
    }

def number_of_buoys(
        buoys_attachment: dict
        ) -> int:
    """
    Description:
        Get the number of attachments in tha Dict result (treated_buoys) from 'buoyancy_treatment'
    Parameters:
        buoys_attachment: buoys that goes to model
    Return:
        Number of attachments
    """
    return len([buoy[i] for buoy in buoys_attachment.values() for i in range(len(buoy))])

def putting_buoys_in_model(
        element: orca.OrcaFlexObject,
        n_buoys: int,
        attachments: dict,
        ):
    """
    Description:
        Insert the attachments from the Dict result (treated_buoys) from 'buoyancy_treatment' in the model.
    Parameters:
        element: Flexible pipe
        n_buoys: number of attachments
        attachments: attachment to insert in model
    """
    element.NumberOfAttachments = int(n_buoys + 1)
    ibs_key = tuple(attachments.keys())
    ibs_val = tuple(attachments.values())

    ibs_2 = [ibs_val[i][j] 
             for i in range(len(ibs_val)) 
             for j in range(len(ibs_val[i]))]
    
    b = 1
    for buoy in ibs_2:
        element.AttachmentType[b] = buoy        # insert attachments
        b += 1

    ibs_1 = [ibs_key[z] 
             for z in range(len(ibs_val)) 
             for _ in range(len(ibs_val[z]))]
    p = 1
    for n in ibs_1:
        element.Attachmentz[p] = n          # insert attachment's position
        p += 1

# CODING ------------------------------------------------------------------

# Starting stdout and buffer
original_stdout = sys.stdout
buffer = StringIO()
sys.stdout = DualOutput(original_stdout, buffer)

# Starting time count
start_time = time.time()

# Modeling orcaflex elements
model = orca.Model(STATIC_PATH)
general = model['General']
environment = model['Environment']
line = model['Line']
bend_restrictor = model['Stiffener1']
mcv_name = MCV_SHEET['B3'].value
vcm = model[mcv_name]
winch = model['Guindaste']
a_r = model['A/R']

# Removing bend restrictor
line.NumberOfAttachments = 0

# Calculating statics - 1st time without bend restrictor
ini_time = time.time()
lda = VALUES_SHEET['C3'].value
vcm_coord_a = MCV_SHEET['B8'].value

print(f"\nRUNNING WITHOUT BEND RESTRICTOR")
run_static_before_looping(model, general, environment, line, vcm, lda, vcm_coord_a, ini_time)
user_specified(model, RT_NUMBER, RT_STATIC_PATH)

# Reset default damping range and number of iterations
if general.StaticsMinDamping != STATICS_MIN_DAMPING:
    general.StaticsMinDamping = STATICS_MIN_DAMPING
    general.StaticsMaxDamping = STATICS_MAX_DAMPING
    general.StaticsMaxIterations = STATICS_MAX_ITERATIONS

# Recover line x soil interation
if environment.SeabedNormalStiffness != 100:
    environment.SeabedNormalStiffness = 100

# Need to define bend restrictor initial position in line for putting it back
bend_restrictor_initial_position = VALUES_SHEET['C38'].value / 1_000       # end fitting length, in metters

if VALUES_SHEET['A24'].value == "PU":
    bend_restrictor_initial_position += VALUES_SHEET['C64'].value / 1_000       # rigid zone length, in metters

if VALUES_SHEET['A53'].value:
    bend_restrictor_initial_position += VALUES_SHEET['C51'].value / 1_000     # flange adapter length, in metters

# Putting back bend restrictor
print("Bend restrictor initial position")
print(bend_restrictor_initial_position)

line.NumberOfAttachments = 1
line.AttachmentType[0] = "Vert"
line.Attachmentz[0] = bend_restrictor_initial_position
line.AttachmentzRelativeTo[0] = "End B"

# Calculatin statics - 2st time with bend restrictor
ini_time = time.time()

print(f"\nRUNNING WITH BEND RESTRICTOR")
run_static_before_looping(model, general, environment, line, vcm, lda, vcm_coord_a, ini_time)
user_specified(model, RT_NUMBER, RT_STATIC_PATH)

# Reset default damping range and number of iterations
if general.StaticsMinDamping != STATICS_MIN_DAMPING:
    general.StaticsMinDamping = STATICS_MIN_DAMPING
    general.StaticsMaxDamping = STATICS_MAX_DAMPING
    general.StaticsMaxIterations = STATICS_MAX_ITERATIONS

# Recover line x soil interation
if environment.SeabedNormalStiffness != 100:
    environment.SeabedNormalStiffness = 100

# define set of buoys
vessel_name = RESULTS_SHEET['C6'].value
buoy_set = VESSEL_BUOYS[vessel_name]

# putting buoys in line (partially)
k = 1
while k <= N_INCREMENT:

    # each increment creates a partial buoyancy of rl_config
    rl_config_partial = [
        rl_config[0],
        [round(k * x / N_INCREMENT, 0) for x in rl_config[1]]
    ]

    # select the best set of buoys of combined_buoys that fits the rl_config_partial
    selection = buoyancy(rl_config_partial, vessel_name)

    # treats selection for putting it in Orca
    treated_selection = buoys_treatment(rl_config_partial, selection, vessel_name)

    n_buoys = number_of_buoys(treated_selection)

    # putting buoys in model
    putting_buoys_in_model(line, n_buoys, treated_selection, vessel_name)

    # Calculatin statics - Inserting suggested buoys
    ini_time = time.time()

    print(f"\nRUNNNIG AND INPUTING BUOYANCY")
    run_static_before_looping(model, general, environment, line, vcm, lda, vcm_coord_a, ini_time)
    user_specified(model, RT_NUMBER, RT_STATIC_PATH)

    # Reset default damping range and number of iterations
if general.StaticsMinDamping != STATICS_MIN_DAMPING:
    general.StaticsMinDamping = STATICS_MIN_DAMPING
    general.StaticsMaxDamping = STATICS_MAX_DAMPING
    general.StaticsMaxIterations = STATICS_MAX_ITERATIONS

    # Recover line x soil interation
    if environment.SeabedNormalStiffness != 100:
        environment.SeabedNormalStiffness = 100
    
    k += 1
