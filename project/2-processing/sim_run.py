"""
Simulation methods for the automation.
"""

# LIBS

import OrcFxAPI
import os
import methods
import time
from collections import Counter

# CONSTANTS

'b_1/b_2 - rotation > 0'  # reason between one buoyancy and next
b_factor_1 = 1.5
'b_1/b_2 - rotation < 0'  # reason between one buoyancy and before
b_factor_2 = 2
'Buoyancy variation for each iteration'
buoy_var = 50
'How many buoys / position'
n_buoys = 2
'Static running counter'
n_run = 0
'Limit number of tentatives to converge'
n_run_limit = 25
'Error correction counter'
n_run_error = 0
'Previous n_run to comparison'
prev_n_run = 0
'Analysis criterias'
rotation = 0
clearance = 0
delta_flange = 0
'Aproove / reproove flange loads verification'
flange_loads = True
'Aproove / reproove bend restrictor loads verification'
br_loads = True
'Verify if bend restrictor is locked'
normalised_curvature = 0
'Loads in bend restrictor'
shear_force = 0
bend_moment = 0
'VCM rotation superior/inferior limit criteria'
vcm_rotation_sup_limit = .5
vcm_rotation_inf_limit = -.5
'Line clearance superior/inferior limit range criteria'
clearance_limit_inf = .5
clearance_limit_sup = .65
'Error in flange height to the seabed criteria'
delta_flange_error_limit = 0
'Buoyancy limits in each point'
small_buoy_buoyancy_limit = 100
buoyancy_limit = 2_000
'Buoy movement - when position changes'
buoy_position_pace = .5
'Buoy position limits'
buoy_position_near_vcm = [3, 6, 9]
buoy_position_far_vcm = [4, 8, 12]
'Line pace - when line changes'
payout_retrieve_pace_min = .2
payout_retrieve_pace_max = .5
'Minimum distance between buoys and VCM o others buoys'
min_distance_buoys = 3
'VCM displacing - when trying to improove convergence'
vcm_delta_x = 20
'Maximum number of iterations'
statics_max_iterations = 400
'Damping range'
statics_min_damping = 5
statics_max_damping = 15
'Heave up heights'
heave_up = [2.5, 2.0, 1.8, 1.5]
'Time for dynamic simulation'
total_period = OrcFxAPI.SpecifiedPeriod(0, 72.15)
'looping results - when trying to avoid configuration loops'
looping_results = []

# METHODS

def previous_run_static(
        model: OrcFxAPI.Model, 
        general: OrcFxAPI.OrcaFlexObject, 
        line_type: OrcFxAPI.OrcaFlexObject, 
        vcm: OrcFxAPI.OrcaFlexObject,
        object_line: methods.Line, 
        object_vcm: methods.Vcm, 
        ini_time: float
        ) -> None:
    """
    Description
        Runs static simulation before its in looping
    Parameters:
        model: Orcaflex model
        general: Orcaflex general to be passed for error correction
        line_type: Orcaflex line in the model
        vcm: Orcaflex vcm in the model
        ini_time: time that runs started
    Return:
        Nothing
    """

    try:
        global n_run_error, rotation, clearance, delta_flange
        
        vcm.DegreesOfFreedomInStatics = 'X,Y,Z'
        model.CalculateStatics()

        model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
        vcm.DegreesOfFreedomInStatics = 'All'
        model.CalculateStatics()

        line_nc = verify_normalised_curvature(line_type, 'Mean')
        if line_nc > .75:
            model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
            line_type.StaticsStep1 = "Catenary"
            model.CalculateStatics()
        
        end_time = time.time()
        print(f"\nTime: {end_time - ini_time}s")

        rotation = verify_vcm_rotation(vcm)
        clearance = verify_line_clearance(line_type)
        delta_flange = verify_flange_height(line_type, object_line, object_vcm)

        n_run_error = 0

    except Exception:
        error_correction(general, line_type, vcm, model)
        previous_run_static(model, general, line_type, vcm, object_line, object_vcm, ini_time)

def run_static(model: OrcFxAPI.Model, rt_number: str, vcm: OrcFxAPI.OrcaFlexObject, line_type: OrcFxAPI.OrcaFlexObject, bend_restrictor_model: OrcFxAPI.OrcaFlexObject, line_obj: methods.Line, 
               bend_restrictor_object: methods.BendRestrictor, vcm_obj: methods.Vcm, general: OrcFxAPI.OrcaFlexObject, file_path: str, structural_limits: dict, static_dir: str, ini_time: float, 
               *final: str) -> None:
    """
    Description
        Runs static simulation in looping
        and verify the results
    Parameters
        model: Orcaflex model
        rt_number: RT identification
        vcm: Orcaflex VCM in the model
        line_type: Orcaflex line in the model
        bend_restrictor_model: Orcaflex bend_restrictor in the model
        line_obj: Line object in the methods.py
        bend_restrictor_object: Bend_restrictor in the methods.py
        vcm_obj: VCM object in the methods.py
        general: Orcaflex general to be passed for error correction
        file_path: Path where static runs are saved
        structural_limits: structural limits informed in RL
        static_dir: path to save files
        final: last run_static command to get VCM fixed, and runs dynamics
        ini_time: time that runs started
    Return:
        Nothing
    """
    try:
        global n_run, rotation, clearance, delta_flange, shear_force, bend_moment, n_run_error, prev_n_run, normalised_curvature, flange_loads, br_loads

        vcm.DegreesOfFreedomInStatics = 'X,Y,Z'
        model.CalculateStatics()
        
        model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
        vcm.DegreesOfFreedomInStatics = 'All'
        model.CalculateStatics()
        
        line_nc = verify_normalised_curvature(line_type, 'Mean')
        if line_nc >= 1:
            model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
            line_type.StaticsStep1 = "Catenary"
            model.CalculateStatics()

        n_run_error = 0

        if final:
            return
        
        end_time = time.time()
        print(f"\n>>>>>>>>\nTime: {end_time - ini_time}s.")

        print("\n__________________________________________________________________")
        print("_________________________RUNNING..._______________________________")
        print("__________________________________________________________________")

        rotation = verify_vcm_rotation(vcm)
        clearance = verify_line_clearance(line_type)
        delta_flange = verify_flange_height(line_type, line_obj, vcm_obj)

        file_name = str(n_run + 1) + "-" + rt_number + ".sim"
        save_simulation = os.path.join(static_dir, file_name)
        model.SaveSimulation(save_simulation)

        n_run += 1

        if n_run != prev_n_run:
            print(f"\n>>>>>>>>\nRunning {n_run}th time.")
            prev_n_run = n_run
        print(f"Results"
              f"\n    VCM Rotation: {rotation}°."
              f"\n    Line Clearance: {clearance}m."
              f"\n    Flange Height error: {delta_flange}m.")
        
        flange_loads = verify_flange_loads(line_type, structural_limits, '2')
        normalised_curvature = verify_normalised_curvature(bend_restrictor_model, "Mean")   
        if normalised_curvature >= 1:
            br_load = verify_br_loads(bend_restrictor_model, bend_restrictor_object, "Mean")

    except Exception:
        error_correction(general, line_type, vcm, model)
        run_static(model, rt_number, vcm, line_type, bend_restrictor_model, line_obj, bend_restrictor_object, vcm_obj, general, file_path, structural_limits, static_dir, ini_time)

def error_correction(general: OrcFxAPI.OrcaFlexObject, line_type: OrcFxAPI.OrcaFlexObject, vcm: OrcFxAPI.OrcaFlexObject, model: OrcFxAPI.Model) -> None:
    """
    Description:
        Sequence of tentatives to improove convergence when Static Simulations fails
        1st - Increase 5 times the Static damping range
        2st - Remove interation between line and seabed (just if they're touching)
        3st - Change line's static policy to Catenary
        4st - Increase 5 times the Maximum number of iterations
    Parameters:
        general: Orcaflex general
        line_type: Orcaflex line
        vcm: Orcaflex VCM
        model: Orcaflex model
    Return:
        Nothing
    """
    global n_run_error, n_run, n_run_limit

    if n_run_error == 0:
        print(f"\nERROR\nIncreasing 5 times the Static Damping Range")
        general.StaticsMinDamping = 5 * statics_min_damping
        general.StaticsMaxDamping = 5 * statics_max_damping
        general.StaticsMaxIterations = 3 * statics_max_iterations

    if n_run_error == 1:
        if clearance <= 0:
            print(f"\nERROR\nRemoving interation between line and seabed")
            model_environment = model["Environment"]
            model_environment.SeabedNormalStiffness = 0
        else:
            n_run_error += 1

    if n_run_error == 2:
        print(f"\nERROR\nChanging Line's Static policy to Catenary.")
        line_type.StaticsStep1 = "Catenary"

    if n_run_error == 3:
        print(f"\nERROR\nDisplacing VCM")
        vcm.InitialX -= vcm_delta_x

    if n_run_error == 4:
        print(f"\nERROR\nIncreasing 5 times the Number of iterations")
        general.StaticsMaxIterations = 5 * statics_max_iterations

    if n_run_error == 5:
        n_run = n_run_limit + 1

    n_run_error += 1

def user_specified(model: OrcFxAPI.Model, rt_number: str, file_path: str) -> None:
    """
    Description:
        Set calculated positions in Line's StaticStep Policy
    Parameters:
        model: Orcaflex model
        rt_number: RT identification
        file_path: Path where static runs are saved
    Return:
        Nothing
    """
    model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
    file_name = rt_number + ".dat"
    save_data = os.path.join(file_path, file_name)
    model.SaveData(save_data)

def buoy_combination(b_set: list) -> dict:
    """
    Description:
        Make combinations with 1 to 3 buoys, below 2 tf of buoyancy
    Parameters:
        b_set: Vessel's buoys
    Return:
        All possible combinations of 1 to 3 vessel's buoys
        {'buoy_1 + buoy_2 + buoy_3': total_buoyancy}
    """
    buoys = [str(b_set[1][i]) for i in range(len(b_set[0])) for _ in range(b_set[0][i])]
    small_buoys = [b for b in buoys if float(b) <= small_buoy_buoyancy_limit]

    one_buoy = {buoy: float(buoy) for buoy in buoys}
    small_one_buoy = {buoy: float(buoy) for buoy in small_buoys}
    two_buoys = {f"{buoy1}+{buoy2}": one_buoy[buoy1] + one_buoy[buoy2] 
                 for i, buoy1 in enumerate(buoys) 
                 for j, buoy2 in enumerate(buoys) 
                 if i < j if one_buoy[buoy1] + one_buoy[buoy2] <= buoyancy_limit}
    three_buoys = {f"{buoy1}+{buoy2}+{buoy3}": one_buoy[buoy1] + one_buoy[buoy2] + small_one_buoy[buoy3] 
                   for i, buoy1 in enumerate(buoys) 
                   for j, buoy2 in enumerate(buoys) 
                   for k, buoy3 in enumerate(small_buoys)
                   if i >= j >= k if one_buoy[buoy1] + one_buoy[buoy2] + small_one_buoy[buoy3] <= buoyancy_limit}

    combination = {}
    if n_buoys == 1:
        combination = {**one_buoy}
    elif n_buoys == 2:
        combination = {**one_buoy, **two_buoys}
    elif n_buoys == 3:
        combination = {**one_buoy, **two_buoys, **three_buoys}
    combination_buoys = {key: value for key, value in combination.items()}
    combination_buoys = dict(sorted(combination_buoys.items(), key=lambda item: item[1], reverse=False))
    return combination_buoys

def buoyancy(buoys_config: list, combination_buoys: dict) -> dict:
    """
    Description:
        Gives the best combination of buoys based on the initial suggestion
    Parameters:
        buoys_config: RL's configuration suggestion
        combination_buoys: Dict result from 'buoy_combination'
    Return:
        Better available combination, that fits with RL's configuration suggestion
    Updates:
        Make comb_keys get inside loop for 'k' and, in final, exclude the used buoys
        in the creation of comb_keys, to avoid use combinations with more buoys of a 
        type than the number the vessel has.
    """
    try:
        selection = {}
        comb_keys = list(combination_buoys.keys())
        for k in range(len(buoys_config[1])):
            j = 0
            while j < len(comb_keys) - 1 and \
            (combination_buoys[comb_keys[j]] < buoys_config[1][k] and \
             combination_buoys[comb_keys[j + 1]] < buoys_config[1][k]):
                j += 1
            if j < len(comb_keys):
                selection[comb_keys[j]] = combination_buoys[comb_keys[j]]
                comb_keys.pop(j)
        return selection

    except IndexError:
        buoys_config[1][k] = 0.9 * buoys_config[1][k]
        selection = {}
        comb_keys = list(combination_buoys.keys())
        for k in range(len(buoys_config[1])):
            j = 0
            while j < len(comb_keys) - 1 and (combination_buoys[comb_keys[j]] < buoys_config[1][k] and combination_buoys[comb_keys[j + 1]] < buoys_config[1][k]):
                j += 1
            if j < len(comb_keys):
                selection[comb_keys[j]] = combination_buoys[comb_keys[j]]
                comb_keys.pop(j)
        return selection

def buoyancy_treatment(buoys_config: list, selection: dict) -> dict:
    """
    Description:
        Get the Dict result (selection) from 'buoyancy' and transforms it in Orcaflex attachments
    Parameters:
        buoys_config: RL's configuration suggestion
        selection: Dict result from 'buoyancy'
    Return
        Orcaflex attachments equivalents to selection
    """
    treated_buoys = {buoys_config[0][i]: list(selection.keys())[i].split("+") for i in range(len(list(selection.keys())))}
    return treated_buoys


def number_buoys(treated_buoys: dict) -> int:
    """
    Description:
        Get the number of attachments in tha Dict result (treated_buoys) from 'buoyancy_treatment'
    Parameters:
        treated_buoys: Dict result from 'buoyancy_treatment'
    Return:
        Number of attachments
    """
    packs = [buoy[i] for buoy in treated_buoys.values() for i in range(len(buoy))]
    return len(packs)


def input_buoyancy(line_type: OrcFxAPI.OrcaFlexObject, num_buoys: float, treated_buoys: dict, vessel: str) -> None:
    """
    Description:
        Insert the attachments from the Dict result (treated_buoys) from 'buoyancy_treatment' in the model.
    Parameters:
        line_type: Orcaflex line
        num_buoys: Int result from 'number_buoys'
        treated_buoys: Dict result from 'buoyancy_treatment'
        vessel: Vessel name
    Return:
        Nothing
    """
    line_type.NumberOfAttachments = int(num_buoys + 1)
    ibs_key = tuple(treated_buoys.keys())
    ibs_val = tuple(treated_buoys.values())

    ibs_2 = [ibs_val[i][j] 
             for i in range(len(ibs_val)) 
             for j in range(len(ibs_val[i]))]
    b = 1
    for m in ibs_2:
        buoy = vessel + "_" + str(m)
        line_type.AttachmentType[b] = buoy
        b += 1

    ibs_1 = [ibs_key[z] 
             for z in range(len(ibs_val)) 
             for _ in range(len(ibs_val[z]))]
    p = 1
    for n in ibs_1:
        line_type.Attachmentz[p] = n
        p += 1


def verify_line_clearance(line_model: OrcFxAPI.OrcaFlexObject) -> float:
    """
    Description:
        Verify minimum line's clearance value
    Parameters:
        line_model: Orcaflex line
    Return:
        Minimum line's clearance value
    """
    line_clearance = line_model.RangeGraph("Seabed clearance")
    list_vsc = [vsc for _, vsc in enumerate(line_clearance.Mean)]
    vsc_min = round(min(list_vsc), 3)
    if vsc_min <= 0:
        print(f"\n>>>>>>>>\nLine's in contact with seabed")
    return vsc_min


def verify_vcm_rotation(vcm: OrcFxAPI.OrcaFlexObject) -> float:
    """
    Description:
        Verify VCM's rotation value
    Parameters:
        vcm: Orcaflex VCM
    Return:
        VCM's rotation
    """
    vcm_rotation = round(vcm.StaticResult("Rotation 2"), 3)
    return vcm_rotation


def verify_flange_height(
        line_model: OrcFxAPI.OrcaFlexObject, 
        line_obj: methods.Line, 
        vcm_obj: methods.Vcm) -> float:
    """
    Description:
        Verify flange's height error
    Parameters:
        line_model: Orcaflex model
        line_obj: Line object in methods.py
        vcm_obj: VCM object in methods.py
    Return:
        Flange's height error
    """
    correct_depth = - line_obj.lda + (vcm_obj.a / 1_000)
    depth_verified = line_model.StaticResult("Z", OrcFxAPI.oeEndB)
    delta = round(correct_depth - depth_verified, 3)
    return delta


def verify_flange_loads(line_model: OrcFxAPI.OrcaFlexObject, structural_limits: dict, case: str, *f_loads: list) -> bool:
    """
    Description:
        Verify if VCM' flange loads are admissible
    Parameters:
        line_model: Orcaflex line
        structural_limits: RL structural limits
        case: load case verified
        f_loads: flange loads for dynamic specified periods
    Return:
        True if loads are admissible, False if not.
    """
    if case == "2":
        load_case = structural_limits[case]

        normal = abs(round(line_model.StaticResult("End Ez force", OrcFxAPI.oeEndB), 3))
        shear = abs(round(line_model.StaticResult("End Ex force", OrcFxAPI.oeEndB), 3))
        moment = abs(round(line_model.StaticResult("End Ey moment", OrcFxAPI.oeEndB), 3))
        print(f"\n        Normal force in flange's gooseneck: {normal}kN (Limit: {load_case[0]}kN)"
              f"\n        Shear force in flange's gooseneck: {shear}kN  (Limit: {load_case[1]}kN)"
              f"\n        Bend moment in flange's gooseneck: {moment}kN.m (Limit: {load_case[2]}kN)")
        flange_loads = (normal, shear, moment)

    else:
        flange_loads = f_loads[0]
        load_case = structural_limits[case]

        if case == "3":
            print(f"\nFor heave period...")
        elif case == "3i":
            print(f"\nFor transition period...")
        elif case == "3ii":
            print(f"\nFor TDP period...")

        print(f"\n        Normal force in flange's gooseneck: {flange_loads[0]}kN (Limit: {load_case[0]}kN)"
              f"\n        Shear force in flange's gooseneck: {flange_loads[1]}kN (Limit: {load_case[1]}kN)"
              f"\n        Bend moment in flange's gooseneck: {flange_loads[2]}kN.m (Limit: {load_case[2]}kN.m)")
    
    load_check = [flange_loads[i] < abs(round(load_case[i], 3)) for i in range(len(load_case))]
    
    if (loads := all(load_check)) == False:
        print("\nFlange loads reprooved!")
    else:
        print("\nFlange loads aprooved!")

    return loads

def verify_normalised_curvature(bend_restrictor_model: OrcFxAPI.OrcaFlexObject, magnitude: str) -> float:
    """
    Description:
        Verify bend restrictor normalised curvature value
    Parameters:
        bend_restrictor_model: Orcaflex bend restrictor
        magnitude: 'Mean' for static analysis and 'Max' for dynamic analysis
    Return:
        Bend restrictor maximum normalised curvature value
    """
    if magnitude == "Mean":
        n_curve = bend_restrictor_model.RangeGraph("Normalised curvature")
        nc = [nc for _, nc in enumerate(n_curve.Mean)]

    elif magnitude == "Max":
        n_curve = bend_restrictor_model.RangeGraph("Normalised curvature", period=OrcFxAPI.PeriodNum.WholeSimulation)
        nc = [nc for _, nc in enumerate(n_curve.Max)]

    nc_max = round(max(nc), 3)
    if nc_max >= 1:
        print(f"\n Bend Restrictor's locked")
    return nc_max

def verify_br_loads(bend_restrictor_model: OrcFxAPI.OrcaFlexObject, bend_restrictor_object: methods.BendRestrictor, magnitude: str) -> bool:
    """
    Description:
        Verify if bend restrictor's loads are admissible
    Parameters:
        bend_restrictor_model: Orcaflex bend restrictor
        bend_restrictor_object: Bend restrictor object in methods.py
        magnitude: 'Mean' for static analysis and 'Max' for dynamic analysis
    Return:
        True if bend restrictor's loads are admissible, False if not.
    """
    limit_sf, limit_bf = bend_restrictor_object.sf, bend_restrictor_object.bm

    if limit_sf == 0 or limit_bf == 0:
        print(f"\nIt's not possible to verify bend restrictor's loading.")
        if limit_sf == 0:
            print(f"Shear force limit not found")
        if limit_bf == 0:
            print(f"Bend moment limit not found")
        
        return True  # does not check

    else:
        if magnitude == "Mean":
            moment = bend_restrictor_model.RangeGraph("Bend moment")
            moment = [bm for _, bm in enumerate(moment.Mean)]
            shear = bend_restrictor_model.RangeGraph("Shear Force")
            shear = [sf for _, sf in enumerate(shear.Mean)]

        elif magnitude == "Max":
            moment = bend_restrictor_model.RangeGraph("Bend moment", period=OrcFxAPI.PeriodNum.WholeSimulation)
            moment = [bm for _, bm in enumerate(moment.Max)]
            shear = bend_restrictor_model.RangeGraph("Shear Force", period=OrcFxAPI.PeriodNum.WholeSimulation)
            shear = [sf for _, sf in enumerate(shear.Max)]

        max_moment = round(max(abs(min(moment)), max(moment)), 3)
        max_shear = round(max(abs(min(shear)), max(shear)), 3)

        print(f"\n      Shear force in bend_restrictor: {max_shear}kN (Limit: {limit_sf}kN)"
              f"\n      Bend moment in bend_restrictor: {max_moment}kN.m (Limit: {limit_bf}kN.m)")
        
        br_loads = [max_shear, max_moment]
        load_case = [limit_sf, limit_bf]
        load_check = [br_loads[i] < abs(round(load_case[i], 3)) for i in range(len(load_case))]
        if all(load_check):
            print("\nBend restrictor loads aprooved!")
        else:
            print("\nBend restrictor loads reprooved!")
        return all(load_check)

def looping(model_line_type: OrcFxAPI.OrcaFlexObject, selection: dict, model: OrcFxAPI.Model, bend_restrictor_model: OrcFxAPI.OrcaFlexObject, rt_number: str, vessel: str, rl_config: list, buoy_set: list, 
            model_vcm: OrcFxAPI.OrcaFlexObject, object_line: methods.Line, object_bend_restrictor: methods.BendRestrictor, object_vcm: methods.Vcm, winch: OrcFxAPI.OrcaFlexObject, general: OrcFxAPI.OrcaFlexObject, 
            environment: OrcFxAPI.OrcaFlexObject, file_path: str, structural: dict, a_r: OrcFxAPI.OrcaFlexObject, static_dir: str) -> None:
    """
    Description:
        This is a loop that controls all the changes in model, in each 'iteration', calling the commands in reason of the last obtained results values.
        1st - payout/retrieve line/A&R everytime clearance (between line and seabed) is out of the range: (.5, .65)
        2st - changes buoy positions or set of buoys everytime VCM's rotation is out of the range: (-.5, .5)
            The priority is to change buoys position.
        3st - changes buoys positions or set of buoys everytime bend restrictor's loads are not available
        4st - adjust VCM height changing the winch length
    Parameters:
        model_line_type: Orcaflex line
        selection: Dict result from 'buoyancy'
        model: Orcaflex model
        bend_restrictor_model: Bend restrictor model
        rt_number: RT identification
        vessel: Vessel name
        rl_config: RL's configuration suggestion
        buoy_set: Vessel's buoys
        model_vcm: Orcaflex VCM
        object_line: Line object from methods.py
        object_bend_restrictor: Bend restrictor object from methods.py
        object_vcm: VCM object from methods.py
        winch: Orcaflex winch
        general: Orcaflex general
        environment: Orcaflex environment
        file_path: Path where static runs are saved
        structural: RL structural limits for loading in VCM's flange
        a_r: Orcaflex A&R cable
        static_dir: path to save files
    Return:
        Nothing
    """
    global rotation, clearance, delta_flange, n_run, flange_loads, clearance_limit_sup, payout_retrieve_pace_min, vcm_rotation_inf_limit, n_buoys, looping_results

    environment.SeabedOriginX = model_vcm.InitialX  # restart configurations
    if general.StaticsMinDamping != statics_min_damping:
        general.StaticsMinDamping = statics_min_damping
        general.StaticsMaxDamping = statics_max_damping
        general.StaticsMaxIterations = statics_max_iterations
    if environment.SeabedNormalStiffness != 100:
        environment.SeabedNormalStiffness = 100

    if n_run >= n_run_limit:  # loop faills
        rotation = .45
        clearance = .52
        delta_flange = 0
        flange_loads = True
        print("\n>>>>>>>>\nSorry, it was not possible to converge.")
        return None

    number = model_line_type.NumberOfAttachments
    position = []
    k = 1
    for _ in range(1, number):
        position.append(model_line_type.Attachmentz[k])
        k += 1
    buoys = list(selection.values())
    buoy_model = [position, buoys]

    if buoy_model not in looping_results:
        looping_results.append(buoy_model)

    num_positions = len(buoy_model[0])
    unique_positions = list(Counter(position).keys())
    pointer = make_pointer(len(unique_positions), unique_positions)

    if clearance < clearance_limit_inf or clearance > clearance_limit_sup:

        if clearance < 0:  # line touching seabed
            payout_retrieve_line(model_line_type, -payout_retrieve_pace_max, object_line, a_r)

        elif clearance < clearance_limit_inf:  # line above of 50cm of seabed
            payout_retrieve_line(model_line_type, - payout_retrieve_pace_min, object_line, a_r)

        elif clearance > clearance_limit_sup:  # line can be payed-out, to avoid high VCM's flange loading
            payout_retrieve_line(model_line_type, payout_retrieve_pace_min, object_line, a_r)

        n_run = max(n_run - 1, 0)  # doesn't count this kind of model changing

        call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, 
                  buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, 
                  environment, file_path, structural, a_r, static_dir)


    if rotation > vcm_rotation_sup_limit:  # VCM inclined in line's direction

        limits = [buoy_position_far_vcm[i] 
                  for i in range(len(unique_positions))]  # limits for 'change position' of buoys

        if unique_positions[pointer] > limits[pointer]:  # condition that allows change buoy position
            new_positions = [buoy_position - buoy_position_pace 
                             for buoy_position in unique_positions]  # define new positions far from the VCM

            change_position(model_line_type, new_positions, pointer, num_positions, position)

            n_run = max(n_run - 1, 0)  # doesn't count this kind of model changing
            
            call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, 
                      object_bend_restrictor, object_vcm, winch, general, environment, file_path, structural, a_r, static_dir)
                
        else:  # change set of buoys

            call_change_buoys(unique_positions, rl_config, buoy_set, model_line_type, vessel, model_vcm, object_line, model, bend_restrictor_model, 
                              rt_number, object_bend_restrictor, object_vcm, winch, general, environment, file_path, structural, a_r, selection, 
                              buoy_model, static_dir)


    elif rotation < vcm_rotation_inf_limit:  # VCM inclined away of line's direction

        limits = [buoy_position_near_vcm[i] 
                  for i in range(len(unique_positions))]  # limits for 'change position' of buoys

        if unique_positions[pointer] < limits[pointer]:  # condition that allows change buoy position
            new_positions = [buoy_position + buoy_position_pace 
                             for buoy_position in unique_positions]  # define new positions near to the VCM

            change_position(model_line_type, new_positions, pointer, num_positions, position)

            n_run = max(n_run - 1, 0)  # doesn't count this kind of model changing
            
            call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, 
                      object_bend_restrictor, object_vcm, winch, general, environment, file_path, structural, a_r, static_dir)
                
        else:  # change set of buoys

            call_change_buoys(unique_positions, rl_config, buoy_set, model_line_type, vessel, model_vcm, object_line, model, bend_restrictor_model, 
                              rt_number, object_bend_restrictor, object_vcm, winch, general, environment, file_path, structural, a_r, selection, 
                              buoy_model, static_dir)


    if delta_flange != delta_flange_error_limit:

        if delta_flange > .1:
            looping_results.clear()

        flange_height_correction(winch, delta_flange)  # correct VCM's height

        general.StaticsMinDamping = 5 * statics_min_damping
        general.StaticsMaxDamping = 5 * statics_max_damping
        general.StaticsMaxIterations = 5 * statics_max_iterations

        call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, 
                  vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, 
                  object_vcm, winch, general, environment, file_path, structural, a_r, static_dir)

    if rotation < .1 and clearance > .55:
        payout_retrieve_line(model_line_type, payout_retrieve_pace_min / 5, object_line, a_r)
        
        n_run = max(n_run - 1, 0)  # doesn't count this kind of model changing

        call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, environment, 
                  file_path, structural, a_r, static_dir)
    
    ini_time = time.time()

    run_static(model, rt_number, model_vcm, model_line_type, bend_restrictor_model, object_line, object_bend_restrictor, object_vcm, general, file_path, structural, static_dir, ini_time, 'final')

def more_buoys(rl_config) -> list:
    """
    Description
        If, with the actual buoy's set, was shown impossibility to find a solution.
        Add one place more to apply buoyancy in the line
    Parameters
        rl_config: RL's configuration suggestion
    Return
        RL configuration with one more position to put the buoys
    """
    print(f"""\nProbably the suggestion of buoys was not that good. \nGonna change it a little to see if it works...""")

    new_position = rl_config[0][-1] + 3
    rl_config[0].append(new_position)
    new_buoy = 100
    rl_config[1].append(new_buoy)

    return [rl_config[0], rl_config[1]]
    
def call_loop(model_line_type: OrcFxAPI.OrcaFlexObject, selection: dict, model: OrcFxAPI.Model, bend_restrictor_model: OrcFxAPI.OrcaFlexObject, rt_number: str, vessel: str, rl_config: list, buoy_set: list, 
              model_vcm: OrcFxAPI.OrcaFlexObject, object_line: methods.Line, object_bend_restrictor: methods.BendRestrictor, object_vcm: methods.Vcm, winch: OrcFxAPI.OrcaFlexObject, general: OrcFxAPI.OrcaFlexObject, 
              environment: OrcFxAPI.OrcaFlexObject, file_path: str, structural: dict, a_r: OrcFxAPI.OrcaFlexObject, static_dir: str):
    """
    Description
        Resume methods: Run 'calculate statics' -> Save positions -> Run 'looping' again
    Parameters
        model_line_type: Orcaflex line
        selection: Dict result from 'buoyancy'
        model: Orcaflex model
        bend_restrictor_model: Bend restrictor model
        rt_number: RT identification
        vessel: Vessel name
        rl_config: RL's configuration suggestion
        buoy_set: Actual buoy set configuration tentative
        model_vcm: Orcaflex VCM
        object_line: Line object from methods.py
        object_bend_restrictor: Bend restrictor object from methods.py
        object_vcm: VCM object from methods.py
        winch: Orcaflex winch
        general: Orcaflex generalR
        environment: Orcaflex environment
        file_path: Path where static runs are saved
        structural: RL structural limits for loading in VCM's flange
        a_r: Orcaflex A&R cable
        static_dir: path to save file
    Return
        Nothing
    """
    ini_time = time.time()
    run_static(model, rt_number, model_vcm, model_line_type, bend_restrictor_model, object_line, object_bend_restrictor, object_vcm, general, file_path, structural, static_dir, ini_time)
    user_specified(model, rt_number, file_path)
    looping(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, environment, file_path, structural, a_r, static_dir)

def call_change_buoys(unique_positions: list, rl_config: dict, buoy_set: list, model_line_type: OrcFxAPI.OrcaFlexObject, vessel: str, model_vcm: OrcFxAPI.OrcaFlexObject, object_line: methods.Line, model: OrcFxAPI.Model,
                      bend_restrictor_model: OrcFxAPI.OrcaFlexObject, rt_number: str, object_bend_restrictor: methods.BendRestrictor, object_vcm: methods.Vcm, winch: OrcFxAPI.OrcaFlexObject, general: OrcFxAPI.OrcaFlexObject, 
                      environment: OrcFxAPI.OrcaFlexObject, file_path: str, structural: dict, a_r: OrcFxAPI.OrcaFlexObject, selection: dict, buoy_model: list, static_dir: str):
    """
    Description
        Controls how buoy's set will changes...
        Each set of buoys will be saved in list 'looping results'
        If actual buoy set is different of the last tentative
            Then, is verified if actual buoy set is not between the others tentatives
                If not, it means it's a new tentative.
                    In this case, priority is to change buoys position
                If it's not a new tentative...
                    Then, priority is to add one more buoy position
        If it's just differente of the last tentative...
            Then, priority is to changes the buoy set
        If something goes wrong...
            Probably the problem is that in one of the buoy's position the buoyancy exceeds 2Te...
            In this case, priority is to add one more buoy position
    Parameters
        unique_positions: list of buoy set's position, with no repeated values
        rl_config: RL's configuration suggestion
        buoy_set: Actual buoy set configuration tentative
        model_line_type: Orcaflex line
        vessel: Vessel name
        model_vcm: Orcaflex VCM
        object_line: Line object in methods.py
        model: Orcaflex model
        bend_restrictor_model: Orcaflex Bend restrictor
        rt_number: RT identification
        object_bend_restrictor: Bend restrictor object in methods.py
        object_vcm: VCM object in methods.py
        winch: Orcaflex winch
        general: Orcaflex general
        environment: Orcaflex environment
        file_path: Path where static runs are saved
        structural: RL structural limits for loading in VCM's flange
        a_r: Orcaflex A&R cable
        selection: Dict result from 'buoyancy'
        buoy_model: actual buoy set
        initial_rl: initial rl configuration (reference)
        old_buoy_model: last reference of buoy_model
    Return
        Nothing
    """
    global n_run, n_buoys

    if buoy_model == looping_results[-1]:  # or it's a new tentative, or it isn't, but it's equal the last

        new_rl_config = changing_buoyancy(unique_positions, rl_config)

        if type(new_rl_config) == list:  # changing buoyancy worked

            old_selection = selection
            selection = changing_buoys(selection, buoy_set, new_rl_config, model_line_type, vessel)

            if old_selection == selection:
                n_run = max(n_run - 1, 0)

            call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, new_rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, environment, 
                      file_path, structural, a_r, static_dir)
        
        if type(new_rl_config) == str:  # changing buoyancy failed

            if len(selection) < 3:

                if n_buoys == 2:  # if I have 2 positions with 2 buoys/position (4)
                    n_buoys += 1  # try 2 positions with 3 buoys/position (6)
                    selection = changing_buoys(selection, buoy_set, rl_config, model_line_type, vessel)
                    call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, 
                              environment, file_path, structural, a_r, static_dir)
                    
                elif n_buoys == 3:
                    n_buoys -= 1   # If I have 2 positions with 3 buoys/position (6)
                    new_rl_config = more_buoys(rl_config)  # try 3 positions with 2 buoys / position (6)
                    selection = changing_buoys(selection, buoy_set, new_rl_config, model_line_type, vessel)
                    call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, new_rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, 
                              environment, file_path, structural, a_r, static_dir)
                    
            elif len(selection) == 3:

                if n_buoys == 2:   # If I have 3 positions with 2 buoys/position (6)
                    n_buoys += 1   # try 3 positions with 3 buoys/position (9)
                    selection = changing_buoys(selection, buoy_set, rl_config, model_line_type, vessel)
                    call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, 
                              environment, file_path, structural, a_r, static_dir)
                    
                elif n_buoys == 3:
                    n_run = 50
                    call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, 
                              environment, file_path, structural, a_r, static_dir)
        
    else:  # it's not a new tentative
        
        if len(selection) < 3:

            if n_buoys == 2:  # if I have 2 positions with 2 buoys/position (4)
                n_buoys += 1  # try 2 positions with 3 buoys/position (6)
                selection = changing_buoys(selection, buoy_set, rl_config, model_line_type, vessel)
                call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, 
                            environment, file_path, structural, a_r, static_dir)
                
            elif n_buoys == 3:
                n_buoys -= 1   # If I have 2 positions with 3 buoys/position (6)
                new_rl_config = more_buoys(rl_config)  # try 3 positions with 2 buoys / position (6)
                selection = changing_buoys(selection, buoy_set, new_rl_config, model_line_type, vessel)
                call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, new_rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, 
                            environment, file_path, structural, a_r, static_dir)
                
        elif len(selection) == 3:

            if n_buoys == 2:   # If I have 3 positions with 2 buoys/position (6)
                n_buoys += 1  # try 3 positions with 3 buoys/position (9)
                selection = changing_buoys(selection, buoy_set, rl_config, model_line_type, vessel)
                call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, 
                            environment, file_path, structural, a_r, static_dir)
                
            elif n_buoys == 3:
                n_run = 50
                call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, 
                            environment, file_path, structural, a_r, static_dir)


def make_pointer(num_positions: float, positions: list) -> int:
    """
    Description
        It creates a pointer for the buoy set's position where it is being prioritized to change something
        If we need to add buoyancy
            see how much positions we have to insert buoyancy
                priority is to change the position nearest VCM, moving it away from the VCM
                but without infringe the minimum distance between positions
        if we need to reduce buoyancy
            see how much positions we have to insert buoyancy
                priority is to change the position far from VCM, moving it near to the VCM
                but without infringe the minimum distance between positions
    Parameters:
        num_positions: numbers of positions to insert buoyancy
        positions: actual buoy's set positions
    Return
        Pointer
    """
    if rotation > 0:  # if we need to add buoyancy

        pointer = 0  # case when there's 1 position to insert buoyancy

        if num_positions == 2:  # case when there's 2 positions to insert buoyancy
            if positions[pointer] <= buoy_position_near_vcm[pointer]:
                pointer = 1

        elif num_positions == 3:  # case when there's 3 positions to insert buoyancy
            if positions[pointer] <= buoy_position_near_vcm[pointer]:
                pointer = 1
                if positions[pointer] <= buoy_position_near_vcm[pointer]:
                    pointer = 2
    
    elif rotation < 0:  # if we need to reduce buoyancy

        pointer = num_positions - 1  # case when there's 1 position to insert buoyancy

        if num_positions == 2:  # case when there's 2 positions to insert buoyancy
            if positions[pointer] >= buoy_position_far_vcm[pointer]:
                pointer = 0

        elif num_positions == 3:  # case when there's 3 positions to insert buoyancy
            if positions[pointer] >= buoy_position_far_vcm[pointer]:
                pointer = 1
                if positions[pointer] >= buoy_position_far_vcm[pointer]:
                    pointer = 0
    
    return pointer

def change_position(line_model: OrcFxAPI.OrcaFlexObject, new_positions: list, pointer: int, num_positions: int, positions: list) -> None:
    """
    Description
        Changes the buoy's set position apointed by the pointer
    Parameters
        line_model: Orcaflex line
        new_positions: the buoys new positions
        pointer: Int result from 'make_pointer'
        num_positions: number of positions to insert buoynacy
        positions: actual buoy's set positions
    Return
        Nothing
    """
    p = 1
    temp = []
    for z in range(0, num_positions):
        if (positions[z] + buoy_position_pace == new_positions[pointer] or \
            positions[z] - buoy_position_pace == new_positions[pointer]):
            if new_positions[pointer] not in temp:
                temp.append(new_positions[pointer])
                print(f"\n>>>>>>>>\nChanging buoys positioned at {line_model.Attachmentz[p]}m"
                      f"\nPositioning them at {new_positions[pointer]}m")
            line_model.Attachmentz[p] = new_positions[pointer]
        p += 1

def changing_buoyancy(position: list, rl_config: list) -> list:
    """
    Description
        When it is needed, changes the buoyancy reference to select another buoy set
        Check if we need to add buoyancy
            see how much positions we have to add buoyancy
                consideer add 50kg of buoyancy in pointed buoy's set position
                when there's 2 or 3 positions...
                    try to make it in a way that positions near to VCM always have, at least, the double of buoyancy of the next far position
        Cheack if we need to reduce buoyancy
            see how much positions we have to reduce buoyancy
                consideer reduce 50kg of buoyancy in pointed buoy's set position
                when there's 2 or 3 positions...
                    try to make it in a way that position far to VCM always have, in maximum, the half of buoyancy of the last near position
    Parameter
        position: actual buoy's set positions
        rl_config: RL's configuration suggestion
    Return
        New reference to RL configuration
    """
    total_buoyancy = rl_config[1]

    if rotation > 0:  # we need to add buoyancy

        if len(total_buoyancy) == 1:  # case when there's 1 position to insert buoyancy
            if (total := buoy_var + total_buoyancy[0]) < buoyancy_limit:  # consideer add 50kg of buoyancy in buoy position
                print(f"Changing buoyancy reference, {total_buoyancy[0]}kg, in {buoy_var}kg")
                total_buoyancy[0] = total
            else:
                return 'fail'

        elif len(total_buoyancy) == 2:  # case when there's 2 position to insert buoyancy
            if total_buoyancy[0] >= b_factor_1 * total_buoyancy[1]:  # try to make it in a way that 1st position always have, at least, 150% greater of buoyancy of the 2st position
                if (total := buoy_var + total_buoyancy[1]) < buoyancy_limit:  # consideer add 50kg of buoyancy in 2st buoy position
                    print(f"Changing 2st buoyancy reference, {total_buoyancy[1]}kg, in {buoy_var}kg")
                    total_buoyancy[1] = total
                else:
                    return 'fail'
            else:
                if (total := buoy_var + total_buoyancy[0]) < buoyancy_limit:  # consideer add 50kg of buoyancy in 1st buoy position
                    print(f"Changing 1st buoyancy reference, {total_buoyancy[0]}kg, in {buoy_var}kg")
                    total_buoyancy[0] = total 
                else:
                    return 'fail' 

        elif len(total_buoyancy) == 3:  # case when there's 3 position to insert buoyancy
            if total_buoyancy[0] >= b_factor_1 * total_buoyancy[1]:  # try to make it in a way that 1st position always have, at least, 150% greater of buoyancy of the 2st position
                if total_buoyancy[1] >= b_factor_1 * total_buoyancy[2]:  # try to make it in a way that 2st position always have, at least, 150% greater of buoyancy of the 3st position
                    if (total := buoy_var + total_buoyancy[2]) < buoyancy_limit:  # consideer add 50kg of buoyancy in 3st buoy position
                        print(f"Changing 3st buoyancy reference, {total_buoyancy[2]}kg, in {buoy_var}kg")
                        total_buoyancy[2] = total
                    else:
                        return 'fail'
                else:
                    if (total := buoy_var + total_buoyancy[1]) < buoyancy_limit:  # consideer add 50kg of buoyancy in 2st buoy position
                        print(f"Changing 2st buoyancy reference, {total_buoyancy[1]}kg, in {buoy_var}kg")
                        total_buoyancy[1] = total
                    else:
                        return 'fail'
            else:
                if (total := buoy_var + total_buoyancy[0]) < buoyancy_limit:  # consideer add 50kg of buoyancy in 1st buoy position
                    print(f"Changing 1st buoyancy reference, {total_buoyancy[2]}kg, in {buoy_var}kg")
                    total_buoyancy[0] = total
                else:
                    return 'fail'

    elif rotation < 0:  # we need to reduce buoyancy

        if len(total_buoyancy) == 1:  # case when there's 1 position to insert buoyancy
            if (total := total_buoyancy[0] - buoy_var) > 0:  # consideer reduce 50kg of buoyancy in buoy position
                print(f"Changing buoyancy reference, {total_buoyancy[0]}kg, in {-buoy_var}kg")
                total_buoyancy[0] = total
            else:
                return 'fail'

        elif len(total_buoyancy) == 2:  # case when there's 2 position to insert buoyancy
            if total_buoyancy[0] >= b_factor_2 * total_buoyancy[1]:  # try to make it in a way that 2st always have, in maximum, the half of buoyancy of the 1st position
                if (total := total_buoyancy[0] - buoy_var) > 0:  # consideer reduce 50kg of buoyancy in 1st buoy position
                    print(f"Changing 1st buoyancy reference, {total_buoyancy[0]}kg, in {-buoy_var}kg")
                    total_buoyancy[0] = total
                else:
                    return 'fail'
            else:
                if (total := total_buoyancy[1] - buoy_var) > 0:  # consideer reduce 50kg of buoyancy in 2st buoy position
                    print(f"Changing 2st buoyancy reference, {total_buoyancy[1]}kg, in {-buoy_var}kg")
                    total_buoyancy[1] = total
                else:
                    return 'fail'

        elif len(total_buoyancy) == 3:  # case when there's 3 position to insert buoyancy
            if total_buoyancy[1] >= b_factor_2 * total_buoyancy[2]:  # try to make it in a way that 3st always have, in maximum, the half of buoyancy of the 2st position
                if total_buoyancy[0] >= b_factor_2 * total_buoyancy[1]:  # try to make it in a way that 2st always have, in maximum, the half of buoyancy of the 1st position
                    if (total := total_buoyancy[0] - buoy_var) > 0:  # consideer reduce 50kg of buoyancy in 1st buoy position
                        print(f"Changing 1st buoyancy reference, {total_buoyancy[0]}kg, in {-buoy_var}kg")
                        total_buoyancy[0] = total
                    else:
                        return 'fail'
                else:
                    if (total := total_buoyancy[1] - buoy_var) > 0:  # consideer reduce 50kg of buoyancy in 2st buoy position
                        print(f"Changing 2st buoyancy reference, {total_buoyancy[1]}kg, in {-buoy_var}kg")
                        total_buoyancy[1] = total
                    else:
                        return 'fail'
            else:
                if (total := buoy_var - total_buoyancy[2]) < buoyancy_limit:  # consideer reduce 50kg of buoyancy in 3st buoy position
                    print(f"Changing 4st buoyancy reference, {total_buoyancy[2]}kg, in {-buoy_var}kg")
                    total_buoyancy[2] = total
                else:
                    return 'fail'

    return [position, total_buoyancy]

def changing_buoys(selection: dict, buoy_set: list, new_rl_config: list, line_model: OrcFxAPI.OrcaFlexObject, vessel: str) -> dict:
    """
    Description
        Resume the work of change buoys in the model from 'new_rl_config'
    Parameters
        selection: Dict result from 'buoyancy'
        buoy_set: actual buoy's set
        new_rl_config: List result from 'changing_buoyancy'
        line_model: Orcaflex line
        vessel: Vessel name
    Return
        The new selection from 'new_rl_config'
    """
    global n_buoys
    
    print(f"\n>>>>>>>>\nChanging the selection of buoys"
          f"\nOld selection: {list(selection.keys())} = Total buoyancy: {list(selection.values())}")
    
    combination_buoys = buoy_combination(buoy_set)
    selection = buoyancy(new_rl_config, combination_buoys)

    print(f"New selection: {list(selection.keys())} = Total buoyancy: {list(selection.values())}")

    treated_buoys = buoyancy_treatment(new_rl_config, selection)
    num_buoys = number_buoys(treated_buoys)
    input_buoyancy(line_model, num_buoys, treated_buoys, vessel)

    return selection

def payout_retrieve_line(line_model: OrcFxAPI.OrcaFlexObject, delta: float, object_line: methods.Line, a_r: OrcFxAPI.OrcaFlexObject) -> None:
    """
    Description:
        Controls the way how line is payed out or retrieved
        Check if it's a normal 1st extremity DVC (payout/retieve line) or a 1st extremity DVC with jumper (payout/retrieve A&R)
    Parameters:
        line_model: Orcaflex line
        delta: quantity that line/A&R's gonna change
        object_line: Line object from methods.py
        a_r: Orcaflex A&R
    Return:
        Nothing
    """
    if clearance < clearance_limit_inf - .3 or clearance > clearance_limit_sup + .3:
        if delta > 0:
            delta = payout_retrieve_pace_max
        else:
            delta = - payout_retrieve_pace_max
    
    if object_line.length == object_line.lda:  # payout/retrieve line
        if delta > 0:
            print(f"\n>>>>>>>>\nPaying out {delta}m of line,"
                  f"\nfrom {round(line_model.Length[0], 2)} to {round(line_model.Length[0] + delta, 2)}")
        else:
            print(f"\n>>>>>>>>\nRetrieving out {-delta}m of line,"
                  f"\nfrom {round(line_model.Length[0], 2)} to {round(line_model.Length[0] + delta, 2)}")
            
        new_length = line_model.Length[0] + delta
        new_segment = new_length / 100  # adjust segmentation of the line
        line_model.Length[0] = round(new_length, 3)
        line_model.TargetSegmentLength[0] = round(new_segment, 3)

    else:  # payout/retrieve A&R
        if delta > 0:
            print(f"\n>>>>>>>>\nPaying out {delta}m of A/R,"
                  f"\nfrom {round(a_r.StageValue[0], 2)} to {round(a_r.StageValue[0] + delta, 2)}")
        else:
            print(f"\n>>>>>>>>\nRetrieving out {-delta}m of A/R,"
                  f"\nfrom {round(a_r.StageValue[0], 2)} to {round(a_r.StageValue[0] + delta, 2)}")
            
        a_r.StageValue[0] = round(a_r.StageValue[0] + delta, 3)

def payout_line(line_model: OrcFxAPI.OrcaFlexObject, delta: float, object_line: methods.Line, a_r: OrcFxAPI.OrcaFlexObject) -> None:
    """
    Description:
        Payout line in Contingency analysis
    Parameters:
        line_model: Orcaflex line
        delta: quantity that line/A&R's gonna change
        object_line: Line object from methods.py
        a_r: Orcaflex A&R
    Return:
        Nothing
    """
    if object_line.length == object_line.lda:  # payout line
        new_length = line_model.Length[0] + delta
        new_segment = new_length / 100  # adjust segmentation of the line
        print(f"\nNew_Length: {round(new_length, 3)}")
        line_model.Length[0] = round(new_length, 3)
        line_model.TargetSegmentLength[0] = round(new_segment, 3)

    else:  # payout A&R
        print(f"\nNew_Length: {round(a_r.StageValue[0] + delta, 3)}")
        a_r.StageValue[0] = round(a_r.StageValue[0] + delta, 3)

def flange_height_correction(winch: OrcFxAPI.OrcaFlexObject, delta: float) -> None:
    """
    Description:
        Adjust VCM height by changing winch length
    Parameters:
        winch: Orcaflex winch
        delta: Quantity that winch's gonna change
    Return:
        Nothing
    """
    if delta > 0:
        print(f"\n>>>>>>>>\nPaying out {delta}m from the winch,"
              f"\nfrom {round(winch.StageValue[0], 2)} to {round(winch.StageValue[0] + delta, 2)}")
    else:
        print(f"\n>>>>>>>>\nRetrieving out {-delta}m from the winch,"
              f"\nfrom {round(winch.StageValue[0], 2)} to {round(winch.StageValue[0] + delta, 2)}")
        
    winch.StageValue[0] = round(winch.StageValue[0] - delta, 3)

def dynamic_simulation(model: OrcFxAPI.Model, line: OrcFxAPI.OrcaFlexObject, bend_restrictor: OrcFxAPI.OrcaFlexObject, bend_restrictor_obj: methods.BendRestrictor, a_r: OrcFxAPI.OrcaFlexObject, 
                       save_simulation: str, structural_limits: dict, rt_number: str, heave: float, vcm: OrcFxAPI.OrcaFlexObject, general: OrcFxAPI.OrcaFlexObject) -> bool:
    """
    Description:
        Run simulation (dynamic) for heave up options: (2.5, 2.0, 1.8)
        When check loads and aprooves it, stop
    Parameters:
        model: Orcaflex model
        line: orcaflex line
        bend_restrictor: Orcaflex bend restrictor
        bend_restrictor_obj: bend restrictor object from methods.py
        a_r: Orcaflex A&R
        save_simulation: path to save file
        structural_limits: RL structural limits for loading in VCM's flange
        rt_number: RT identification
        heave: heave up movement
        vcm: Orcaflex VCM
        general: Orcaflex general
    Return:
        Nothing
    """
    try:
        ini_time = time.time()
        
        model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
        vcm.Connection = "Fixed"

        print(f"\nRunning dynamics for heave up in {heave}m")

        a_r.StageValue[2] = - heave

        file_name = rt_number + " - heave_" + str(heave) + "m.sim"
        simulation = os.path.join(save_simulation, file_name)

        model.RunSimulation()
        model.SaveSimulation(simulation)

        min_normal = abs(round(min(line.TimeHistory('End Ez force', total_period, OrcFxAPI.oeEndB)), 3))
        max_normal = abs(round(max(line.TimeHistory('End Ez force', total_period, OrcFxAPI.oeEndB)), 3))
        
        min_shear = abs(round(min(line.TimeHistory('End Ex force', total_period, OrcFxAPI.oeEndB)), 3))
        max_shear = abs(round(max(line.TimeHistory('End Ex force', total_period, OrcFxAPI.oeEndB)), 3))
        
        min_moment = abs(round(min(line.TimeHistory('End Ey moment', total_period, OrcFxAPI.oeEndB)), 3))
        max_moment = abs(round(max(line.TimeHistory('End Ey moment', total_period, OrcFxAPI.oeEndB)), 3))

        flange_results = [max(min_normal, max_normal), max(min_shear, max_shear), max(min_moment, max_moment)]

        flange_loads = any([verify_flange_loads(line, structural_limits, '3i', flange_results), verify_flange_loads(line, structural_limits, '3ii', flange_results)])

        nc_br = verify_normalised_curvature(bend_restrictor, "Max")
        if nc_br >= 1:
            br_results = verify_br_loads(bend_restrictor, bend_restrictor_obj, "Max")

            result = all([flange_loads, br_results])
        else:
            result = flange_loads

        if result:
            print(f"\nFor {heave}m, loads are admissible.")
        else:
            print(f"\nFor {heave}m, loads are not admissible.")

        end_time = time.time()
        print(f"Time: {end_time - ini_time}")

        return result
    
    except Exception:
        return False

def contingencies(model: OrcFxAPI.Model, line: OrcFxAPI.OrcaFlexObject, bend_restrictor: OrcFxAPI.OrcaFlexObject, bend_restrictor_obj: methods.BendRestrictor, save_simulation: str, structural_limits: dict,
                  vcm: OrcFxAPI.OrcaFlexObject, object_line: methods.Line, a_r: OrcFxAPI.OrcaFlexObject, general: OrcFxAPI.OrcaFlexObject, environment: OrcFxAPI.OrcaFlexObject) -> None:
    """
    Description:
        Check the maximum force that can be applyed in line, in a contingency condition
    Parameters:
        model: Orcaflex model
        line: Orcaflex line
        bend_restrictor: Orcaflex bend restrictor
        bend_restrictor_obj: Bend restrictor object from methods.py
        save_simulation:  Path where static runs are saved
        structural_limits: RL structural limits for loading in VCM's flange
        vcm: Orcaflex VCM
        object_line: Line object from methods.py
        a_r: Orcaflex A&R
        general: Orcaflex general
    Return:
        Nothing
    """
    global n_run_error

    vcm.Connection = "Fixed"

    positions = list(Counter(line.Attachmentz).keys())
    positions.remove(positions[0])  # buoy's position

    mass = [round(.05 + k / 10, 2) for k in range(20)]  # mass options for contingencies (if volume = 2m³ and height = 1m)

    cont = model.CreateObject(OrcFxAPI.ObjectType.ClumpType)  # create a buoy
    cont.Name = 'Cont'
    cont.Volume = 2
    cont.Height = 1

    n = line.NumberOfAttachments  # index for attachment (since we add an attachment)
    line.NumberOfAttachments = n + 1  # add attachment
    line.AttachmentType[n] = 'Cont'  # select contingency
    line.Attachmentz[n] = positions[0] + 1  # add cont 1m after the 1st buoy

    model.CalculateStatics()
    model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)

    k = 0
    k_pass = 0  # controls the number of contingencies
    while k_pass < 2:  # try untill obtain 2 contigencies

        if len(positions) == 1:  # define contingency positions
            if k == 0:
                line.Attachmentz[n] = positions[k] + k + 1
            else:
                line.Attachmentz[n] = positions[0] + k + 1
            
            if positions[0] + k + 1 > 7:
                print(f"\nWasn't possible to find a solution.")
                break  # loops give up

        elif len(positions) == 2:
            if k == 0:
                line.Attachmentz[n] = positions[k] + k + 1
            elif k == 1:
                if k_pass == 0:
                    line.Attachmentz[n] = positions[0] + k + 1
                else:
                    line.Attachmentz[n] = positions[k] + 1
            else:
                line.Attachmentz[n] = positions[1] + k - 1
            
            if positions[1] + k - 1 > 10:
                print(f"\nWasn't possible to find a solution.")
                break  # loops give up

        else:
            if k == 0:
                line.Attachmentz[n] = positions[k] + k + 1
            elif k == 1:
                if k_pass == 0:
                    line.Attachmentz[n] = positions[0] + k + 1
                else:
                    line.Attachmentz[n] = positions[k] + 1
            elif k <= 3:
                line.Attachmentz[n] = positions[1] + k - 1
            else:
                line.Attachmentz[n] = positions[2] + k - 3
            
            if positions[2] + k - 3 > 13:
                print(f"\nWasn't possible to find a solution.")
                break  # loops give up

        print("__________________________________________________________________")
        print(f"________{k + 1}st tentative for {k_pass + 1}st Contingency_______")
        print("__________________________________________________________________")

        file_name = 'Cont_' + str(k_pass + 1) + '.sim'
        path = os.path.join(save_simulation, file_name)

        work = True

        for m in mass:
            cont.Mass = m  # input contingency

            if work:
                    try:
                        model.CalculateStatics()
                    except Exception:
                        work = False
                        
            if not work:
                continue

            model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
            if not work:
                work = True
            
            model.CalculateStatics()

            line_clearance = enumerate(line.RangeGraph("Seabed clearance").Mean)
            line_tdp = [arc_length for arc_length, clearance in line_clearance if clearance < 0]  # line TDP arclength
            
            # we want, at least, 3m and, at maximum, 5m of TDP arclength (in a line region where segmentation is equal 20cm)
            while len(line_tdp) < 3/.2 or len(line_tdp) > 5/ .2 and work:

                if len(line_tdp) < 3/.2:
                    payout_line(line, payout_retrieve_pace_max, object_line, a_r)  # payout 50cm
                elif len(line_tdp) > 5/ .2:
                    payout_line(line, - payout_retrieve_pace_max, object_line, a_r)  # retrieve 50cm
                
                if work:
                    try:
                        model.CalculateStatics()
                        model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
                    except Exception:
                        work = False

                if not work:
                    work = True

                model.CalculateStatics()
                line_clearance = enumerate(line.RangeGraph("Seabed clearance").Mean)
                line_tdp = [arc_length for arc_length, clearance in line_clearance if clearance < 0]  # line TDP arclength

            if not work:
                continue

            loads = [abs(round(line.StaticResult("End Ez force", OrcFxAPI.oeEndB), 3)), abs(round(line.StaticResult("End Ex force", OrcFxAPI.oeEndB), 3)), abs(round(line.StaticResult("End Ey moment", OrcFxAPI.oeEndB), 3))]
            flange_loads = any([verify_flange_loads(line, structural_limits, '3i', loads), verify_flange_loads(line, structural_limits, '3ii', loads)])

            normalised_curvature = verify_normalised_curvature(bend_restrictor, "Mean")   
            if normalised_curvature >= 1:
                br_load = verify_br_loads(bend_restrictor, bend_restrictor_obj, "Mean")
            
                cont_limit = all([flange_loads, br_load])  # verication for bend restrictor loading + flange loading

                if cont_limit:
                    model.SaveSimulation(path)
                    print(f"\nCase {k_pass + 1}: Contingency - {round(2000 - (1000 * (m - mass[0])), 0)}kg in {line.Attachmentz[n]}m to the VCM")
                    k_pass += 1
                    break
            
            else:
                if flange_loads:
                    model.SaveSimulation(path)
                    print(f"\nCase {k_pass + 1}: Contingency - {round(2000 - (1000 * (m - mass[0])), 0)}kg in {line.Attachmentz[n]}m to the VCM")
                    k_pass += 1
                    break
            
            model.SaveSimulation(path)
            print(f"\nCase {k_pass + 1}: Contingency - {round(2000 - (1000 * (m - mass[0])), 0)}kg in {line.Attachmentz[n]}m to the VCM"
                  f"\nLoads are too high, trying to reduce 100kg buoyancy.")
        
        k += 1

        if k_pass == 2:
            break
