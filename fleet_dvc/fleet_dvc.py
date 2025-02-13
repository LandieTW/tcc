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

'Suggestion for initial configuration'
rl_config = [
    [3, 6],         # Positions [m]
    [1800, 1000]      # Submerged mass [kg]
    ]

'Structural limits for each analysis case'
structural_limits = {
    "2": [6.90, -10.47, 13.11],      # Normal, Shear force, Bend moment
    "3i": [3.37, -8.02, 30.67],
    "3ii": [6.68, -10.74, 11.84]
    }

# LIBRARIES ---------------------------------------------------------------

import time
import os
import sys

from collections import Counter
from io import StringIO
from glob import glob
from warnings import simplefilter
from openpyxl import load_workbook

import OrcFxAPI as orca
import numpy as np

# CONSTANTS ---------------------------------------------------------------

'Ignoring openpyxl user_warning'
simplefilter("ignore", UserWarning)

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
    
VESSEL_INITIALISM = {
        'Skandi Niterói': 'SKN',
        'Skandi Búzios': 'SKB',
        'Skandi Açu': 'SKA',
        'Skandi Vitória': 'SKV',
        'Skandi Recife': 'SKR',
        'Skandi Olinda': 'SKO',
        'Coral do Atlântico': 'TOP'
        }

'Static calculation counter'
N_RUN = 0
N_RUN_LIMIT = 50
N_RUN_ERROR = 0

'Number of decimal places'
DECIMAL = 3

'Maximum admissible error in numerical analysis'
MAX_ERROR = 10_000

'Maximum number of iterations'
STATICS_MAX_ITERATIONS = 400

'Damping range for static convergence'
STATICS_MIN_DAMPING = 1
STATICS_MAX_DAMPING = 10

'Static parameters for validation'
ROTATION = 0
CLEARANCE = 0
HEIGTH_ERROR = 0

'Elements displacing, in metters'
DISPLACING_X = 25

'Line pace - when line changes (paying or retrieving line)'
PAY_RET_MIN = .2
PAY_RET_MAX = .5

'Submerged mass limit, in kg, for buoys'
BUOYANCY_LIMIT = 2_000
SMALL_BUOY = 100

'Number of buoyancy increments for 1st addition of buoys in the model'
N_INCREMENT = 5

'Maximum number of buoys for each position'
N_BUOYS_POS = 2     # automation changes it to 3, if doesn't find a solution

'Heave up magnitudes, in metters'
HEAVE_UP = [2.5, 2.0, 1.8, 1.5]

'Time for dynamic simulation'
TOTAL_PERIOD = orca.SpecifiedPeriod(0, 112.15)

'This file path'
THIS_PATH = os.path.dirname(os.path.abspath(__file__))

'Excel sheets'
SHEET_PATH = os.path.join(THIS_PATH, glob(os.path.join(THIS_PATH, "*.xlsm"))[0])

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

def StaticProgHandler(model, progress):
    """
    Description:
        Method to handle statics calculations
    Parameters:
        model: OrcaFlex model
        progress: convergence error, for each iteration
    Return:
        True for stop CalculateStatics, False for not
    """

    static_error = progress.split()

    if progress.startswith('Full statics for Line (no torsion)'):
        index = 10
    elif progress.startswith('Full statics for Line'):
        print(progress)
        index = 8
    elif progress.startswith('Whole system statics'):
        index = 7
    elif progress.startswith('Converged with error'):
        print(progress)
        index = 4

    error = static_error[index].replace(',', '.')

    if round(float(error), DECIMAL) > MAX_ERROR:
        return True
    else:
        return False

def run_static(
        model: orca.Model,
        general: orca.OrcaFlexObject,
        line: orca.OrcaFlexObject,
        vert: orca.OrcaFlexObject,
        vcm: orca.OrcaFlexObject,
        water_depth: float,
        vcm_height: float,
        ini_time: float,
        final: bool,
        ) -> None:
    """
    Description:
        Runs static simulation before the 'looping'.
    Parameters:
        model: OrcaFlex model
        general: OrcaFlex general
        line: Flexible pipe
        vert: Bend Restrictor
        vcm: Vertical connection module
        water_depth: Water depth
        vcm_height: flange to soil height, in mm
        ini_time: Static calculation start time, in seconds
        final: If true, define last static calculation
    """
    try:
        global N_RUN, N_RUN_ERROR, ROTATION, CLEARANCE, DELTA_FLANGE

        if N_RUN > N_RUN_LIMIT:
            print(f"\nSorry, wasn't possible to find a solution.")
            return

        print(f"\nRunning 3 DoF")
        vcm.DegreesOfFreedomInStatics = 'X,Y,Z'
        model.CalculateStatics()

        if model.staticsProgressHandler:
            error_treatment(model, general, line, vcm)
            run_static(model, general, line, vert, vcm, lda, vcm_coord_a, ini_time, False)

        CLEARANCE = verify_clearance(line)

        if CLEARANCE < 0:
            model["Environment"].SeabedNormalStiffness = 0       # remove line x soil interation
            line.Length[0] -= PAY_RET_MAX
            model.CalculateStatics()        

        if model.staticsProgressHandler:
            error_treatment(model, general, line, vcm)
            run_static(model, general, line, vert, vcm, lda, vcm_coord_a, ini_time, False)

        model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)

        print(f"\nRunning 6 DoF")
        vcm.DegreesOfFreedomInStatics = 'All'
        model.CalculateStatics()
        
        line_nc = verify_normalised_curvature(line, 'Mean')     # necessary verification to avoid crazy convergences...
        if line_nc > .75:
            print(f"Crazy convergence. Need to redefine")
            model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
            line.StaticsStep1 = "Catenary"
            model.CalculateStatics()

            if model.staticsProgressHandler:
                error_treatment(model, general, line, vcm)
                run_static(model, general, line, vert, vcm, lda, vcm_coord_a, ini_time, False)
        
        if final:
            print(f"\nProcess finished.")
            return
        
        end_time = time.time()
        print(f"\nTime: {end_time - ini_time}s")        # end time for calculate statics

        ROTATION = round(vcm.StaticResult("Rotation 2"), DECIMAL)
        CLEARANCE = verify_clearance(line)
        DELTA_FLANGE = verify_flange_height(line, water_depth, vcm_height)

        N_RUN += 1
        save_simulation = os.path.join(RT_STATIC_PATH, str(N_RUN) + "_" + "Static.sim")
        model.SaveSimulation(save_simulation)

        flange_loads = verify_flange_loads(line, structural_limits, '2')

        if (br_nc := verify_normalised_curvature(vert, 'Mean')) >= 1:
            br_load = verify_br_loads(vert, 'Mean')

        model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)

        print(f"\nRotation: {ROTATION}")
        print(f"Clearance: {CLEARANCE}")

        # default parameters
        N_RUN_ERROR = 0
        model["Environment"].SeabedNormalStiffness = 100
        general.StaticsMinDamping = STATICS_MIN_DAMPING
        general.StaticsMaxDamping = STATICS_MAX_DAMPING
        general.StaticsMaxIterations = STATICS_MAX_ITERATIONS
    
    except Exception as e:

        print(e)

        error_treatment(model, general, line, vcm)
        run_static(model, general, line, vert, vcm, lda, vcm_coord_a, ini_time, False)

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
        n_curve = element.RangeGraph('Normalised curvature').Mean
    
    elif magnitude == 'Max':
        n_curve = element.RangeGraph('Normalised curvature', period=orca.PeriodNum.WholeSimulation).Max
    
    return round(max(n_curve), DECIMAL)

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
    clearance = element.RangeGraph('Seabed clearance').Mean

    return round(min(clearance), DECIMAL)

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
        model: orca.OrcaFlexObject,
        general: orca.OrcaFlexObject,
        line: orca.OrcaFlexObject,
        vcm: orca.OrcaFlexObject,
        ):
    """
    Description:
        Tentatives to get convergence in static calculation, after it fails 
    Parameters:
        model: OrcaFlex model.
        general: OrcaFlex general config.
        line: Flexible pipe
        vcm: Vertical connection module
    """
    global N_RUN_ERROR, N_RUN, N_RUN_LIMIT

    if N_RUN_ERROR == 0:
        print(f"\nERROR\nIncreasing 5 times the Static Damping Range")
        general.StaticsMinDamping = 5 * STATICS_MIN_DAMPING
        general.StaticsMaxDamping = 5 * STATICS_MAX_DAMPING

    if N_RUN_ERROR == 1:
        print(f"\nERROR\nTrying line in spline configuration")
        line.StaticsStep1 = "Spline"
        line.SplineControlPointX[1] = line.SplineControlPointX[1] + DISPLACING_X
        line.SplineControlPointX[2] = line.SplineControlPointX[2] + DISPLACING_X

    if N_RUN_ERROR == 2:
        print(f"\nERROR\nDisplacing VCM")
        vcm.InitialX -= DISPLACING_X
    
    if N_RUN_ERROR == 3:
        print(f"\nERROR\nChanging Line's Static policy to Catenary.")
        line.StaticsStep1 = "Catenary"

    if N_RUN_ERROR == 4:
        print(f"\nERROR\nIncreasing 5 times the Number of iterations")
        general.StaticsMaxIterations = 5 * STATICS_MAX_ITERATIONS

    if N_RUN_ERROR == 5:
        N_RUN = N_RUN_LIMIT + 1

    N_RUN_ERROR += 1
    model.staticsProgressHandler = False

def verify_flange_loads(
        line: orca.OrcaFlexObject,
        limits: dict,
        case: str,
        ) -> bool:
    """
    Description:
        Verify if flange's loads are admissible
    Parameters:
        line: Flexible pipe
        limits: Structural limits for flange
        case: Load case analysis - (2, 3i, 3ii)
    Returns
        True if loads < limits, False if loads > limits.
    """

    if case == '2':
        loads = [
            abs(round(line.StaticResult("End Ez force", orca.oeEndB), DECIMAL)),
            abs(round(line.StaticResult("End Ex force", orca.oeEndB), DECIMAL)),
            abs(round(line.StaticResult("End Ey moment", orca.oeEndB), DECIMAL))
        ]
    else:
        loads = [
            max(
                abs(round(min(line.TimeHistory('End Ez force', TOTAL_PERIOD, orca.oeEndB)), DECIMAL)), 
                abs(round(max(line.TimeHistory('End Ez force', TOTAL_PERIOD, orca.oeEndB)), DECIMAL))
                ), 
            max(
                abs(round(min(line.TimeHistory('End Ex force', TOTAL_PERIOD, orca.oeEndB)), DECIMAL)), 
                abs(round(max(line.TimeHistory('End Ex force', TOTAL_PERIOD, orca.oeEndB)), DECIMAL))
                ), 
            max(
                abs(round(min(line.TimeHistory('End Ey moment', TOTAL_PERIOD, orca.oeEndB)), DECIMAL)), 
                abs(round(max(line.TimeHistory('End Ey moment', TOTAL_PERIOD, orca.oeEndB)), DECIMAL))
                )
            ]

    print(f"""
          Normal force: {loads[0]}kN;
          Shear force: {loads[1]}kN;
          Bend moment: {loads[2]}kN.m;
          """)

    structural_limits = limits[case]

    check = np.array(loads) < np.abs(np.round(structural_limits, DECIMAL))
    
    if (result := all(check)) == False:
        print("Flange's loads reprooved!")
    else:
        print("Flange's loads aprooved!")
    
    return result

def verify_br_loads(
    vert: orca.OrcaFlexObject,
    magnitude: str,
    ) -> bool:
    """
    Description:
        Verify if vert's loads are admissible
        (Just if limits were given)
    Parameter:
        vert: Bend restrictor
        magnitude: 'Mean' for static and 'Max' for dynamic
    Return:
        True if loads < limits, False if loads > limtis.
    """
    structural_limits = [
        VALUES_SHEET['C29'].value,      # Shear force limit
        VALUES_SHEET['C28'].value       # Bend moment limit
    ]

    check = []

    for i in range(2):
        
        if structural_limits[i]:    # limit was given
            
            if i == 0:      # shear force limit case
                
                if magnitude == 'Mean':
                    shear = vert.RangeGraph("Shear Force").Mean
                else:
                    shear = vert.RangeGraph("Shear Force", period=orca.PeriodNum.WholeSimulation).Max

                shear = round(max(abs(min(shear)), max(shear)), DECIMAL)

                check.append(shear < structural_limits[i])
            
            if i == 1:      # bend moment limit case

                if magnitude == 'Max':
                    moment = vert.RangeGraph("Bend moment").Mean
                else:
                    moment = vert.RangeGraph("Bend moment", period=orca.PeriodNum.WholeSimulation).Max
                
                moment = round(max(abs(min(moment)), max(moment)), DECIMAL)

                check.append(moment < structural_limits[i])
        
        else:
            if i == 0:
                print("Shear force limit for bend restrictor was not found.")
            if i == 1:
                print("Bend moment limit for bend restrictor was not found.")
            pass    # limit was not given
    
    if (result := all(check)):
        print("\nVert's loads aprooved!")
    else:
        print("\nVert's loads reprooved!")
    
    return result
                

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
    if N_BUOYS_POS == 2:
        combination.update(one_buoy)
        combination.update(two_buoys)
    elif N_BUOYS_POS == 3:
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
model.staticsProgressHandler = StaticProgHandler

general = model['General']
line = model['Line']
bend_restrictor = model['Stiffener1']
for object in model.objects:
    if object.type == orca.ObjectType.Buoy6D:
        vcm = object
winch = model['Guindaste']
a_r = model['A/R']

ini_time = time.time()
lda = VALUES_SHEET['C3'].value
vcm_coord_a = MCV_SHEET['B8'].value
'''
# Removing bend restrictor
initial_position = line.Attachmentz[0]  # saving initial position
line.NumberOfAttachments = 0

# Calculating statics - 1st time without bend restrictor
print(f"\nRUNNING WITHOUT BEND RESTRICTOR")

run_static(model, general, line, bend_restrictor, vcm, lda, vcm_coord_a, ini_time, False)

# Putting back bend restrictor
line.NumberOfAttachments = 1
line.AttachmentType[0] = "Vert"
line.Attachmentz[0] = initial_position
line.AttachmentzRelativeTo[0] = "End B"
'''
# Calculatin statics - 2st time with bend restrictor
ini_time = time.time()

print(f"\nRUNNING WITH BEND RESTRICTOR")
run_static(model, general, line, bend_restrictor, vcm, lda, vcm_coord_a, ini_time, False)

# define set of buoys
vessel_name = RESULTS_SHEET['C6'].value

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
    putting_buoys_in_model(line, n_buoys, treated_selection)

    # Calculatin statics - Inserting suggested buoys
    ini_time = time.time()

    print(f"\nRUNNNIG AND INPUTING BUOYANCY")
    run_static(model, general, line, bend_restrictor, vcm, lda, vcm_coord_a, ini_time, False)

    k += 1
