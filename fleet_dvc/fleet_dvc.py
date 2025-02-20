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
from collections import defaultdict
from itertools import combinations
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
    'Skandi Niterói': Counter(SKN_BUOYS),
    'Skandi Búzios': Counter(SKB_BUOYS),
    'Skandi Açu': Counter(SKA_BUOYS),
    'Skandi Vitória': Counter(SKV_BUOYS),
    'Skandi Recife': Counter(SKR_BUOYS),
    'Skandi Olinda': Counter(SKO_BUOYS),
    'Coral do Atlântico': Counter(CDA_BUOYS)
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

'Convergence admissible error'
ERROR = 10 ** -6

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

'Clearance range, in metters'
CLEARANCE_SUP = .6
CLEARANCE_INF = .5

'Rotation range, in degrees'
ROTATION_INF = -.5
ROTATION_SUP = .5

'Line pace - when line changes (paying or retrieving line)'
PAY_RET_MIN = .2
PAY_RET_MAX = .5

'Submerged mass limit, in kg, for buoys'
BUOYANCY_LIMIT = 2_000
SMALL_BUOY = 150

'Number of buoyancy increments for 1st addition of buoys in the model'
N_INCREMENT = 5     # see the loop while before looping

'Maximum number of buoys for each position'
N_BUOYS_POS = 2     # automation changes it to 3, if doesn't find a solution

'Looping method results - saved configurations already tryed'
LOOPING_RESULTS = []        # that helps avoid infinite loops created by the alternation of only two configurations

'Buoys positions'
NEAR_VCM_POSITIONS = [3, 6, 9]
FAR_VCM_POSITIONS = [4, 8, 12]

'Buoyancy factors'
BUOYANCY_FACTOR_1 = 1.5     # Reason between one buoyancy and next
BUOYANCY_FACTOR_2 = 2       # Reason between one buoyancy and previous

'Buoyancy changing in each iteration, in kg'
BUOY_VARIATION = 50

'Pace for buoys position changes'
BUOY_PACE = .5

'Typical A/R cable length in DVC analysis'
AR_LENGTH = 10

'Counter that controls static handler stdout'
STATIC_HANDLER_CONTER = 0

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
RT_NUMBER = RESULTS_SHEET['C21'].value + "_AutomationResults"
RT_PATH = os.path.join(THIS_PATH, RT_NUMBER)
os.makedirs(RT_PATH, exist_ok=True)


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

def StaticProgHandler(
        _,
        progress
        ):

    """
    Description:
        Method to handle statics calculations
    Parameters:
        model: OrcaFlex model
        progress: convergence error, for each iteration
    Return:
        True for stop CalculateStatics, False for not
    """

    global STATIC_HANDLER_CONTER

    try:

        static_error = progress.split()

        if progress.startswith('Full statics for Line (no torsion)'):
            index = 10
        elif progress.startswith('Full statics for Line'):
            index = 8
        elif progress.startswith('Whole system statics'):
            index = 7
        elif progress.startswith('Converged with error'):
            index = 4

        error = static_error[index].replace(',', '.')
        final_error = round(float(error), DECIMAL)

        STATIC_HANDLER_CONTER += 1
        if STATIC_HANDLER_CONTER // 10 == 0:
            print(f"Last error: {final_error}")
        
        if final_error < ERROR:
            if index == 4:
                print(f"\nWhole system statics converged with error: {final_error}")

        if final_error > MAX_ERROR:
            return True
        else:
            return False
    
    except Exception as e:
        print(f"Convergence failed.")
        return False

def run_static(
        model: orca.Model,
        general: orca.OrcaFlexObject,
        line: orca.OrcaFlexLineObject,
        vert: orca.OrcaFlexObject,
        vcm: orca.OrcaFlexObject,
        water_depth: float,
        vcm_height: float,
        ini_time: float,
        final: bool,
        ):
    
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
        global N_RUN, N_RUN_ERROR, ROTATION, CLEARANCE, DELTA_FLANGE, prog_handler_count

        if N_RUN > N_RUN_LIMIT:
            print(f"\nSorry, wasn't possible to find a solution.")
            return

        print(f"\nTrying static convergence\n")
        model.staticsProgressHandler = StaticProgHandler
        model.CalculateStatics()
        
        line_nc = verify_normalised_curvature(line)     # necessary verification to avoid crazy convergences...
        if line_nc > .75 and CLEARANCE > 0 and abs(ROTATION) < .5:
            print(f"Crazy convergence. Need to redefine")
            model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
            line.StaticsStep1 = "Catenary"
            model.staticsProgressHandler = StaticProgHandler
            model.CalculateStatics()
        
        if final:
            print(f"\nProcess finished.")
            return
        
        end_time = time.time()
        print(f"\nTime: {round(end_time - ini_time, DECIMAL)}s")        # end time for calculate statics

        ROTATION = round(vcm.StaticResult("Rotation 2"), DECIMAL)
        CLEARANCE = verify_clearance(line)
        DELTA_FLANGE = verify_flange_height(line, water_depth, vcm_height)

        N_RUN += 1
        save_simulation = os.path.join(RT_PATH, str(N_RUN) + "_" + "Static.sim")
        model.SaveSimulation(save_simulation)

        print(f"Simulation: {str(N_RUN)}"f"_Static.sim")     # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        verify_flange_loads(line, structural_limits, '2')

        verify_normalised_curvature(vert)

        model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)

        print(f"\nRotation: {ROTATION}")
        print(f"Clearance: {CLEARANCE}")

        # default parameters
        vcm.DegreesOfFreedomInStatics = 'All'
        N_RUN_ERROR = 0
        prog_handler_count = 0
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
        ) -> float:
    
    """
    Description:
        Verify element's normalised curvature value
    Parameters:
        element: OrcaFlex object (Line or bend restrictor)
        magnitude: 'Mean' for static calculation
    Returns:
        Element's normalised curvature value
    """

    n_curve = element.RangeGraph('Normalised curvature').Mean

    if element.name == "Line":
        return round(max(n_curve), DECIMAL)
    
    if round(max(n_curve), DECIMAL) >= 1:

        verify_br_loads(element)

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
        line: orca.OrcaFlexLineObject,
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

    global N_RUN_ERROR, N_RUN
    
    if N_RUN_ERROR == 0:
        if model["Environment"].SeabedNormalStiffness != 0:
            print(f"\nERROR\nRemoving line x soil interation.")
            model["Environment"].SeabedNormalStiffness = 0
        else:
            N_RUN_ERROR += 1

    if N_RUN_ERROR == 1:
        print(f"\nERROR\nRemoving VCM's rotational degrees of freedom")
        vcm.DegreesOfFreedomInStatics = 'X,Y,Z'

    if N_RUN_ERROR == 2:
        print(f"\nERROR\nIncreasing 5 times the Static Damping Range")
        general.StaticsMinDamping = 5 * STATICS_MIN_DAMPING
        general.StaticsMaxDamping = 5 * STATICS_MAX_DAMPING

    if N_RUN_ERROR == 3:
        print(f"\nERROR\nDisplacing VCM")
        vcm.InitialX -= DISPLACING_X
    
    if N_RUN_ERROR == 4:
        print(f"\nERROR\nChanging Line's Static policy to Catenary.")
        line.StaticsStep1 = "Catenary"

    if N_RUN_ERROR == 5:
        print(f"\nERROR\nIncreasing 5 times the Number of iterations")
        general.StaticsMaxIterations = 5 * STATICS_MAX_ITERATIONS

    if N_RUN_ERROR == 6:
        N_RUN = N_RUN_LIMIT + 1

    N_RUN_ERROR += 1
    model.staticsProgressHandler = False

def verify_flange_loads(
        line: orca.OrcaFlexLineObject,
        limits: dict,
        case: str,
        ) -> bool:
    
    """
    Description:
        Verify if flange's loads are admissible
    Parameters:
        line: Flexible pipe
        limits: Structural limits for flange
        case: Load case analysis - (2)
    Returns
        True if loads < limits, False if loads > limits.
    """

    loads = [
        abs(round(line.StaticResult("End Ez force", orca.oeEndB), DECIMAL)),
        abs(round(line.StaticResult("End Ex force", orca.oeEndB), DECIMAL)),
        abs(round(line.StaticResult("End Ey moment", orca.oeEndB), DECIMAL))
    ]

    print(f"""
          Normal force: {loads[0]}kN;
          Shear force: {loads[1]}kN;
          Bend moment: {loads[2]}kN.m;
          """)

    structural_limits = limits[case]

    check = np.array(loads) < np.abs(np.round(structural_limits, DECIMAL))
    
    if all(check):
        print(f"\nFlange's loads aprooved!\n")
    else:
        print(f"\nFlange's loads reprooved!\n")
        

def verify_br_loads(
    vert: orca.OrcaFlexObject,
    ) -> bool:

    """
    Description:
        Verify if vert's loads are admissible
        (Just if limits were given)
    Parameter:
        vert: Bend restrictor
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
                
                shear = vert.RangeGraph("Shear Force").Mean
                shear = round(max(abs(min(shear)), max(shear)), DECIMAL)
                check.append(shear < structural_limits[i])
                print(f"Vert - Shear force: {shear}")
            
            if i == 1:      # bend moment limit case

                moment = vert.RangeGraph("Bend moment").Mean
                moment = round(max(abs(min(moment)), max(moment)), DECIMAL)
                check.append(moment < structural_limits[i])
                print(f"Vert - Bend moment: {moment}")
        
        else:
            if i == 0:
                print("Shear force limit for bend restrictor was not found.")
            if i == 1:
                print("Bend moment limit for bend restrictor was not found.")
            pass    # limit was not given
    
    if all(check):
        print("\nVert's loads aprooved!")
    else:
        print("\nVert's loads reprooved!")
                
def select_buoy_combination(
        config: list,
        buoy_set: dict,
        ):
    """
    Description:
        Creates a combination of buoys and select the closer of config suggestion
    Parameters:
        config: list with reference for position and buoyancy
        buoy_set: Dict with vessel's buoys
    Return:
        Selection of buoy_combinations tha better fits config suggestion
    """

    def buoy_combination(
            buoys: list,
            ) -> list:
        
        """
        Description:
            Combines buoys, following next rules:
            1 - Each combination must have less than 2000 kg of submerged mass
            2 - Each combination must combine, at maximum, N_BUOY_POS buoys
            3 - Each combination must respect vessel's availability for each buoy
            4 - If a combination is done with N_BUOY_POS == 3, than, at least, one of this buoys is a small buoy (<150kg of submerged mass)
        Parameters:
            buoys: List with elements from buoy_set
        Return:
            A dict with this format {'b1+b2': b1+b2, ...}
        """

        comb = list(combinations(buoys, 1)) + list(combinations(buoys, 2))
        if N_BUOYS_POS == 3:
            comb += list(combinations(buoys, 3))
    
        final_comb = defaultdict(float)     # avoid reppeated combinations

        for combination in comb:
            if len(combination) == 1:
                val = combination[0]
                key = str(val)
                final_comb[key] = val
            elif len(combination) == 2:
                if (val := combination[0] + combination[1]) <= BUOYANCY_LIMIT:      # < 2000kg
                    key = str(combination[0]) + "+" + str(combination[1])
                    final_comb[key] = val
            elif len(combination) == 3:
                if combination[0] <= SMALL_BUOY or combination[1] <= SMALL_BUOY or combination[2] <= SMALL_BUOY:      # < 2000kg
                    if (val := combination[0] + combination[1] + combination[2]) <= BUOYANCY_LIMIT:     # one of three is small
                        key = str(combination[0]) + "+" + str(combination[1]) + "+" + str(combination[2])
                        final_comb[key] = val
        
        return dict(sorted(final_comb.items(), key=lambda item: item[1], reverse=True))     # all combinations

    b = list(buoy_set.elements())

    selection = {}

    for ref in config[1]:

        if ref == BUOYANCY_LIMIT:       # treating a possible error
            ref = .9 * ref

        buoy_comb = buoy_combination(b)     # combining buoys
        
        buoys = list(buoy_comb.keys())
        buoyancy = list(buoy_comb.values())

        # making selection
        buoyancy.append(ref)
        buoyancy.sort(reverse=True)
        i = buoyancy.index(ref)
        
        if i == 0:
        
            buoyancy_options = [buoyancy[i + 1]]

            buoyancy_selected = buoyancy_options[0]
            index = i + 1

        elif i == len(buoyancy) - 1:
        
            buoyancy_options = [buoyancy[i - 1]]

            buoyancy_selected = buoyancy_options[0]
            index = i - 1

        else:
        
            buoyancy_options = [buoyancy[i - 1], buoyancy[i + 1]]
        
            if abs(ref - buoyancy_options[0]) < abs(ref - buoyancy_options[1]):
                buoyancy_selected = buoyancy[i - 1]
                index = i - 1
            else:
                buoyancy_selected = buoyancy[i + 1]
                index = i
        
        selection[buoys[index]] = buoyancy_selected

        # excluding chosen buoys, for next selection
        buoys = buoys[index].split("+")
        for buoy in buoys:
            b.remove(int(buoy))
    
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
    for pos in ibs_1:
        element.Attachmentz[p] = pos          # insert attachment's position
        p += 1

def looping(
        model: orca.Model,
        general: orca.OrcaFlexObject,
        line: orca.OrcaFlexLineObject,
        vert: orca.OrcaFlexObject,
        vcm: orca.OrcaFlexObject,
        winch: orca.OrcaFlexObject,
        a_r: orca.OrcaFlexObject,
        lda: float,
        vcm_coord_a: float,
        selection: dict,
        buoy_set: list,
        rl_config: list,
        vessel: str,
        ):
    
    """
    Description:
        This is a loop that controls changes in model, in each iteration, calling commands in reason of last obtained results
        1 - Payout / Retrieve line or A/R everytime clearance (soil to line minimum distance) is out of range [50; 65]cm
        2 - Changes buoy's position of set of buoys everytime VCM's inclination is out of range [-0.5; 0.5]°
            2.1 - First tries to change buoy's position;
            2.2 - Then, changes buoys
        3 - Adjust flange height, changing winch length
    Parameters:
        model: OrcaFlex model
        general: General data of OrcaFlex
        line: Flexible pipe
        vert: Bend Restrictor
        vcm: Vertical Connection Module
        winch: Winch cable
        a_r: A/R cable
        lda: Water depth
        vcm_coord_a: Flange's height
        selection: Dict with selected buoys
        buoy_set: Available buoys in the vessel
        vessel: Vessel's name
    """

    global N_RUN

    if N_RUN > N_RUN_LIMIT:
        return
    
    number = line.NumberOfAttachments

    position = []
    k = 1
    for _ in range(1, number):
        position.append(line.Attachmentz[k])
        k += 1
    buoys = list(selection.values())
    
    buoy_model = [position, buoys]

    if buoy_model not in LOOPING_RESULTS:
        LOOPING_RESULTS.append(buoy_model)
    
    n_positions = len(buoy_model[0])

    unique_positions = list(Counter(position).keys())

    pointer = make_pointer(len(unique_positions), unique_positions)

    # 1st criteria - Clearance between line and soil controlled between [.5; .65]m
    if CLEARANCE < CLEARANCE_INF or CLEARANCE > CLEARANCE_SUP:

        if CLEARANCE < 0:       # line touching seabed
            delta = - PAY_RET_MAX
        elif CLEARANCE > CLEARANCE_INF - .1 and CLEARANCE < CLEARANCE_INF:      # clearance almost 50cm
            delta = - PAY_RET_MIN / 4
        elif CLEARANCE < CLEARANCE_INF - .1:     # line too close to soil
            delta = - PAY_RET_MIN
        elif CLEARANCE > CLEARANCE_SUP:     # line so far from soil
            delta = PAY_RET_MAX

        payout_retrieve_line(line, a_r, delta)

        N_RUN -= 1       # Doesn't count this iterations
    
        ini_time = time.time()

        run_static(model, general, line, vert, vcm, lda, vcm_coord_a, ini_time, False)

        looping(model, general, line, vert, vcm, winch, a_r, lda, vcm_coord_a, selection, buoy_set, rl_config, vessel)
    
    # 2st criteria - VCM rotation controlled between [-.5; .5]°
    if ROTATION > ROTATION_SUP or ROTATION < ROTATION_INF:

        if ROTATION > ROTATION_SUP:     # VCM inclined in line's direction

            limits_position = [FAR_VCM_POSITIONS[i]
                               for i in range(len(unique_positions))]
            
            if unique_positions[pointer] > limits_position[pointer]:        # condition for change buoys position

                new_positions = [buoy_position - BUOY_PACE
                                 for buoy_position in unique_positions]     # new_positions are far from VCM
                
                change_buoy_position(line, new_positions, pointer, n_positions, position)

                N_RUN -= 1       # Doesn't count this iterations
    
                ini_time = time.time()

                run_static(model, general, line, vert, vcm, lda, vcm_coord_a, ini_time, False)

                looping(model, general, line, vert, vcm, winch, a_r, lda, vcm_coord_a, selection, buoy_set, rl_config, vessel)
            
            else:       # Condition for change the buoy's set

                selection = call_changing_buoys(line, unique_positions, buoy_set, buoy_model, rl_config, selection, vessel)
    
                ini_time = time.time()

                run_static(model, general, line, vert, vcm, lda, vcm_coord_a, ini_time, False)

                looping(model, general, line, vert, vcm, winch, a_r, lda, vcm_coord_a, selection, buoy_set, rl_config, vessel)

        elif ROTATION < ROTATION_INF:       # VCM inclined away of line's direction

            limits_position = [NEAR_VCM_POSITIONS[i]
                               for i in range(len(unique_positions))]
            
            if unique_positions[pointer] < limits_position[pointer]:        # condition for change buoys position

                new_positions = [buoy_position + BUOY_PACE
                                 for buoy_position in unique_positions]     # new_positions are near from VCM

                change_buoy_position(line, new_positions, pointer, n_positions, position)

                N_RUN -= 1      # Doesn't count this iterations

                ini_time = time.time()

                run_static(model, general, line, vert, vcm, lda, vcm_coord_a, ini_time, False)

                looping(model, general, line, vert, vcm, winch, a_r, lda, vcm_coord_a, selection, buoy_set, rl_config, vessel)
            
            else:       # Condition for change the buoy's set
                
                selection = call_changing_buoys(line, unique_positions, buoy_set, buoy_model, rl_config, selection, vessel)

                ini_time = time.time()

                run_static(model, general, line, vert, vcm, lda, vcm_coord_a, ini_time, False)

                looping(model, general, line, vert, vcm, winch, a_r, lda, vcm_coord_a, selection, buoy_set, rl_config, vessel)
    
    # 3st criteria - Perfect adjustment of flange's height
    if DELTA_FLANGE != 0:

        if DELTA_FLANGE > .1:
            LOOPING_RESULTS.clear()     # This case, sometimes, demands retry some tentatives
        
        if DELTA_FLANGE > 0:
            print(f"\nPaying out {DELTA_FLANGE}m from the winch,"
                  f"from {round(winch.StageValue[0], DECIMAL)} to {round(winch.StageValue[0] + DELTA_FLANGE, DECIMAL)}.")
        else:
            print(f"\nRetrieving {DELTA_FLANGE}m from the winch,"
                  f"from {round(winch.StageValue[0], DECIMAL)} to {round(winch.StageValue[0] + DELTA_FLANGE, DECIMAL)}.")
        
        winch.StageValue[0] = round(winch.StageValue[0] - DELTA_FLANGE, DECIMAL)

        general.StaticsMinDamping = 5 * STATICS_MIN_DAMPING
        general.StaticsMaxDamping = 5 * STATICS_MAX_DAMPING
        general.StaticsMaxIterations = 5 * STATICS_MAX_ITERATIONS

        ini_time = time.time()

        run_static(model, general, line, vert, vcm, lda, vcm_coord_a, ini_time, False)

        looping(model, general, line, vert, vcm, winch, a_r, lda, vcm_coord_a, selection, buoy_set, rl_config, vessel)

def make_pointer(
        n: int,
        positions: list,
        ) -> int:
    
    """
    Description:
        Creates a pointer for buoy_set's position, when it's being prioritized to change some position in a set of buoys
        If we need to add (+) buoyancy...
            See how many buoys we have in the position that gonna be changed
                Then, choose to change buoyancy in nearest to VCM position, moving it away from VCM 
                (without infringe minimum distance between positions)
        If we need to reduce (-) buoyancy...
            See how many buoys we have in the position that gonna be changed
                Then, choose to change buoyancy in far from VCM position, moving it near to the VCM
                (without infringe minimum distance between positions)
    Parameters:
        n: Number of positions with buoys
        positions: actual positions in line, where we have buoys
    Return:
        Selected index-position for change buoyancy
    """

    if ROTATION > 0:

        pointer = 0

        if n == 2:      # there are 2 positions with buoys
            if positions[pointer] <= NEAR_VCM_POSITIONS[pointer]:
                pointer = 1
        
        if n == 3:      # there are 3 positions with buoys
            if positions[pointer] <= NEAR_VCM_POSITIONS[pointer]:
                pointer = 1
                if positions[pointer] <= NEAR_VCM_POSITIONS[pointer]:
                    pointer = 2
    
    elif ROTATION < 0:

        pointer = n - 1

        if n == 2:      # there are 2 positions with buoys
            if positions[pointer] >= FAR_VCM_POSITIONS[pointer]:
                pointer = 0
        
        elif n == 3:        # there are 3 positions with buoys
            if positions[pointer] >= FAR_VCM_POSITIONS[pointer]:
                pointer = 1
                if positions[pointer] >= FAR_VCM_POSITIONS[pointer]:
                    pointer = 0

    return pointer

def payout_retrieve_line(
        line: orca.OrcaFlexLineObject,
        a_r: orca.OrcaFlexObject,
        delta: float,
        ):

    """
    Description:
        Controls the way how line is payed or retrieved
    Parameters:
        line: Flexible pipe
        a_r: A/R cable
        delta: payout or retrieve quantity of line or A/R
    """

    if a_r.StageValue[0] == AR_LENGTH:

        if delta > 0:
            print(f"\nPaying out {delta}m of line,"
                  f"\nfrom {round(line.CumulativeLength[-1], DECIMAL)}m to {round(line.CumulativeLength[-1] + delta, DECIMAL)}m")
        else:
            print(f"\nRetrieving out {-delta}m of line,"
                  f"\nfrom {round(line.CumulativeLength[-1], DECIMAL)}m to {round(line.CumulativeLength[-1] + delta, DECIMAL)}m")
        
        new_length = line.Length[0] + delta
        new_segment = new_length / 100

        line.Length[0] = round(new_length, DECIMAL)
        line.TargetSegmentLength[0] = round(new_segment, DECIMAL)
    
    else:

        new_length = a_r.StageValue[0]  + delta

        if delta > 0:
            print(f"\nPaying out {delta}m of A/R cable,"
                  f"\nfrom {round(a_r.StageValue[0], DECIMAL)}m to {round(new_length, DECIMAL)}m")
        else:
            print(f"\nRetrieving out {-delta}m of A/R cable,"
                  f"\nfrom {round(a_r.StageValue[0], DECIMAL)}m to {round(new_length, DECIMAL)}m")

        a_r.StageValue[0] = round(new_length, DECIMAL)

def change_buoy_position(
        line: orca.OrcaFlexLineObject,
        new_positions: list,
        i: int,
        n: int,
        actual_positions: list
        ):
    
    """
    Description:
        Changes position of buoys in pointer position
    Parameters:
        line: Flexible pipe
        new_positions: the new positions for buoys
        i: index of the position to be changed
        n: number of buoys in model
        actual_positions: actual buoy's set's position in model
    """

    temp = []

    for z in range(0, n):

        # Condition that satisfies at least 3m of distance between buoys
        if actual_positions[z] + BUOY_PACE == new_positions[i] or actual_positions[z] - BUOY_PACE == new_positions[i]:

            if new_positions[i] not in temp:        # Avoid reppeated positions (because there's more than 1 buoy in the same postion)

                temp.append(new_positions[i])
                print(f"\nChanging buoys positioned at {line.Attachmentz[z]}m"
                      f"\nPositioning them at {new_positions[i]}m")
            
            line.Attachmentz[z] = new_positions[i]

def call_changing_buoys(
        line: orca.OrcaFlexLineObject,
        positions: list,
        buoy_set: list,
        buoy_model: list,
        rl_config: dict,
        selection: dict,
        vessel: str,
        ):
    
    """
    Description:
        Controls how buoy's set changes...
        Obs.: Remember each tentative (configuration) is saved in LOOPING_RESULTS
        1st - Check if actual buoy_set is equal last tentative (buoy_model == LOOPING_RESULTS[-1])
            If yes... That means it's equal some last tentative, what occurs as a consequence of the possible reppeated combination of buoys
            2st - So, just try changing buoyancy reference (new_rl_config = changing_buoyancy(positions, rl_config))
                If it works... we have new_buoys
                If not (buoyancy > 2Tf), them...
            If not (buoyancy > 2Tf), them...
                3st - Check what to do consideering the two next options:
                    3.1 - Try configurations with 3 buoys in each position (default: N_BUOYS = 2)
                    3.2 - Try configurations with 3 positions for buoys (default: N_BUOYS = 2)
    Parameters:
        line: Flexible pipe
        positions: Positions where buoys are in the model
        buoy_set: Actual set of buoys in model
        buoy_model: Actual configuration in model
        rl_config: Actual (old) reference for buoy's configuration
        selection: Actual (old) selection of buoys
        vessel: Vessel's name
    Return:
        New selection of buoys
    """

    global N_RUN, N_BUOYS_POS

    if buoy_model == LOOPING_RESULTS[-1]:       # 1st

        new_rl_config = changing_buoyancy(positions, rl_config)     # 2st

        if type(new_rl_config) == list:     # changing_buoyancy worked

            old_selection = selection
            selection = changing_buoys(selection, buoy_set, new_rl_config, line, vessel)

            if old_selection == selection:
                N_RUN -= 1      # do not count this iteration
            
    elif buoy_model != LOOPING_RESULTS[-1] or type(new_rl_config) == str:      # 3st (changing_buoyancy failed)

        if len(selection) < 3:

            if N_BUOYS_POS == 2:
                
                N_BUOYS_POS += 1        # try config. with 3 buoys / position

                selection = changing_buoys(selection, buoy_set, rl_config, line, vessel)
            
            elif N_BUOYS_POS == 3:      
                
                N_BUOYS_POS -= 1        # try config. with 2 buoys / position

                rl_config[0].append(rl_config[0][-1] + 3)
                rl_config[1].append(100)
                new_rl_config = rl_config       # adding one position for buoys

                selection = changing_buoys(selection, buoy_set, new_rl_config, line, vessel)
        
        if len(selection) == 3:

            if N_BUOYS_POS == 2:

                N_BUOYS_POS += 1        # try config. with 3 buoys / position

                selection = changing_buoys(selection, buoy_set, rl_config, line, vessel)
            
            elif N_BUOYS_POS == 3:

                N_RUN = N_RUN_LIMIT + 1     # failed to find a solution
    
    return selection
    
def changing_buoyancy(
        position: list,
        reference: list,
        ) -> list:
    
    """
    Description:
        Controlls how buoyancy reference changes
        1st - Check if we need to add / reduce buoyancy
        2st - See how many buoys, in a position, we have to add / reduce buoyancy
        3st - Consideer add / reduce 50kg in submerged mass in the 'pointed' position
        Obs.:   Try to make it in a way that respect the 1st and 2st buoyancy factors
                Each buoyancy factor consideer the reason buoyancy in the pointer position and its next or previous
                When we want to add buoyancy: BUOYANCY_FACTOR_1 - Reason between one buoy and its next
                When we want to reduce buoyancy: BUOYANCY_FACTOR_2 - Reason between one buoy and its previous
    Parameters:
        position: Positions where we have buoys installed
        reference: RL_configuration suggestion
    """

    total_buoyancy = reference[1]

    if ROTATION > 0:        # we gonna add buoyancy

        if len(total_buoyancy) == 1:
            if (total := total_buoyancy[0] + BUOY_VARIATION) < BUOYANCY_LIMIT:
                print(f"\nChanging buoyancy reference: {total_buoyancy[0]}kg, in {BUOY_VARIATION}kg")
                total_buoyancy[0] = total
            else: 
                return 'fail'
        
        elif len(total_buoyancy) == 2:
            if total_buoyancy[0] >= BUOYANCY_FACTOR_1 * total_buoyancy[1]:
                if (total := total_buoyancy[1] + BUOY_VARIATION) < BUOYANCY_LIMIT:
                    print(f"\nChanging 2st buoyancy reference: {total_buoyancy[1]}kg, in {BUOY_VARIATION}kg")
                    total_buoyancy[1] = total
                else:
                    return 'fail'
            else:
                if (total := total_buoyancy[0] + BUOY_VARIATION) < BUOYANCY_LIMIT:
                    print(f"\nChanging 1st buoyancy reference: {total_buoyancy[0]}kg, in {BUOY_VARIATION}kg")
                else:
                    return 'fail'
        
        elif len(total_buoyancy) == 3:
            if total_buoyancy[0] >= BUOYANCY_FACTOR_1 * total_buoyancy[1]:
                if total_buoyancy[1] >= BUOYANCY_FACTOR_1 * total_buoyancy[2]:
                    if (total := total_buoyancy[2] + BUOY_VARIATION) < BUOYANCY_LIMIT:
                        print(f"\nChanging 3st buoyancy reference: {total_buoyancy[2]}kg, in {BUOY_VARIATION}kg")
                        total_buoyancy[2] = total
                    else:
                        return 'fail'
                else:
                    if (total := total_buoyancy[1] + BUOY_VARIATION) < BUOYANCY_LIMIT:
                        print(f"\nChanging 2st buoyancy reference: {total_buoyancy[1]}kg, in {BUOY_VARIATION}kg")
                        total_buoyancy[1] = total
                    else:
                        return 'fail'
            else:
                if (total := total_buoyancy[0] + BUOY_VARIATION) < BUOYANCY_LIMIT:
                    print(f"\nChanging 1st buoyancy reference: {total_buoyancy[0]}kg, in {BUOY_VARIATION}kg")
                    total_buoyancy[0] = total
                else:
                    return 'fail'
    
    elif ROTATION < 0:      # we gonna reduce buoyancy

        if len(total_buoyancy) == 1:
            if (total := total_buoyancy[0] - BUOY_VARIATION) > 0:
                print(f"\nChanging buoyancy reference: {total_buoyancy[0]}kg, in {-BUOY_VARIATION}kg")
                total_buoyancy[0] = total
            else:
                return 'fail'
        
        elif len(total_buoyancy) == 2:
            if total_buoyancy[0] >= BUOYANCY_FACTOR_2 * total_buoyancy[1]:
                if (total := total_buoyancy[0] - BUOY_VARIATION) > 0:
                    print(f"\nChanging 1st buoyancy reference: {total_buoyancy[0]}kg, in {-BUOY_VARIATION}kg")
                    total_buoyancy[0] = total
                else:
                    return 'fail'
            else:
                if (total := total_buoyancy[1] - BUOY_VARIATION) > 0:
                    print(f"\nChanging 2st buoyancy reference: {total_buoyancy[1]}kg, in {-BUOY_VARIATION}kg")
                    total_buoyancy[1] = total
                else:
                    return 'fail'
        
        elif len(total_buoyancy) == 3:
            if total_buoyancy[1] >= BUOYANCY_FACTOR_2 * total_buoyancy[2]:
                if total_buoyancy[0] >= BUOYANCY_FACTOR_2 * total_buoyancy[1]:
                    if (total := total_buoyancy[0] - BUOY_VARIATION) > 0:
                        print(f"\nChanging 1st buoyancy reference: {total_buoyancy[0]}kg, in {-BUOY_VARIATION}kg")
                        total_buoyancy[0] = total
                    else:
                        return 'fail'
                else:
                    if (total := total_buoyancy[1] - BUOY_VARIATION) > 0:
                        print(f"\nChanging 2st buoyancy reference: {total_buoyancy[1]}kg, in {-BUOY_VARIATION}kg")
                        total_buoyancy[1] = total
                    else:
                        return 'fail'
            else:
                if (total := total_buoyancy[2] - BUOY_VARIATION) > 0:
                    print(f"\nChangin 3st buoyancy reference: {total_buoyancy[2]}kg, in {-BUOY_VARIATION}kg")
                    total_buoyancy[2] = total
                else:
                    return 'fail'
    
    return [position, total_buoyancy]

def changing_buoys(
        selection: dict,
        buoy_set: list,
        new_rl_config: list,
        line: orca.OrcaFlexLineObject,
        vessel: str,
        ) -> dict:
    
    """
    Description:
        Resume the work of changing buoys in model
    Parameters:
        selection: Old reference for changing buoys
        buoy_set: Actual model's configuration
        new_rl_config: New reference for configuration
        line: Flexible pipe
        vessel: Vessel name
    Return
        New selection (reference) based on new_rl_config
    """

    print(f"\nChanging selection of buoys"
          f"\nOld selection: {list(selection.keys())} = Total buoyancy: {list(selection.values())}")

    selection = select_buoy_combination(new_rl_config, buoy_set)

    print(f"\nNew selection: {list(selection.keys())} = Total buoyancy: {list(selection.values())}")

    treated_buoys = buoys_treatment(new_rl_config, selection, vessel)
    num_buoys = number_of_buoys(treated_buoys)
    putting_buoys_in_model(line, num_buoys, treated_buoys)

    return selection

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

print(f"\nRUNNING 1st AUTOMATION'S PART")
run_static(model, general, line, bend_restrictor, vcm, lda, vcm_coord_a, ini_time, False)

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
    selection = select_buoy_combination(rl_config_partial, buoy_set)

    # treats selection for putting it in Orca
    treated_selection = buoys_treatment(rl_config_partial, selection, vessel_name)

    n_buoys = number_of_buoys(treated_selection)

    # putting buoys in model
    putting_buoys_in_model(line, n_buoys, treated_selection)

    # Calculatin statics - Inserting suggested buoys
    ini_time = time.time()

    print(f"\nINSTALLING SUGGESTED BUOY'S CONFIGURATION...")
    run_static(model, general, line, bend_restrictor, vcm, lda, vcm_coord_a, ini_time, False)

    k += 1

if rl_config != rl_config_partial:
    rl_config = rl_config_partial

print(f"\nRUNNING 2ST AUTOMATION'S PART")
looping(model, general, line, bend_restrictor, vcm, winch, a_r, lda, vcm_coord_a, selection, buoy_set, rl_config, vessel_name)

static_end_time = time.time()
exec_static_time = round(static_end_time - start_time, DECIMAL)

print(f"\nAUTOMATION'S END."
      f"\nTotal execution time: {exec_static_time:.2f}s")

sys.stdout = original_stdout

captured_text = buffer.getvalue()

output_path = os.path.join(RT_PATH, "output.txt")
with open(output_path, 'w', encoding='utf-8') as file:
    file.write(captured_text)
