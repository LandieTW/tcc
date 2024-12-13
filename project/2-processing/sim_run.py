"""
Simulation methods for the automation.
"""

# LIBS

import OrcFxAPI
import os
import methods
from collections import Counter

# CONSTANTS

'Static running counter'
n_run = 0
'Limit number of tentatives to converge'
n_run_limit = 50
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
'Buoyancy limit in each point'
buoyancy_limit = 2_000
'Buoy movement - when position changes'
buoy_position_pace = .5
'Buoy position limits'
buoy_position_near_vcm = [3, 6, 9]
buoy_position_far_vcm = [4, 8, 12]
'Line pace - when line changes'
payout_retrieve_pace_min = .2
payout_retrieve_pace_max = .5
'line segmentation'
line_segments = [4, 2, 1, .5, .2]
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
heave_up = [2.5, 2.0, 1.8]
'Times for dynamic simulation'
heave_up_period = OrcFxAPI.SpecifiedPeriod(0, 2.15)
transition_period = OrcFxAPI.SpecifiedPeriod(2.15, 32.15)
tdp_period = OrcFxAPI.SpecifiedPeriod(32.15, 72.15)
total_period = OrcFxAPI.SpecifiedPeriod(0, 72.15)
'looping results - when trying to avoid configuration loops'
looping_results = []

# METHODS

def previous_run_static(model: OrcFxAPI.Model, general: OrcFxAPI.OrcaFlexObject, line_type: OrcFxAPI.OrcaFlexObject, vcm: OrcFxAPI.OrcaFlexObject) -> None:
    """
    Description
        Runs static simulation before its in looping
    Parameters:
        model: Orcaflex model
        general: Orcaflex general to be passed for error correction
        line_type: Orcaflex line in the model
        vcm: Orcaflex vcm in the model
    Return:
        Nothing
    """
    try:
        global n_run_error
        
        vcm.DegreesOfFreedomInStatics = 'X,Y,Z'
        model.CalculateStatics()
        model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
        vcm.DegreesOfFreedomInStatics = 'All'
        model.CalculateStatics()
        n_run_error = 0

    except Exception as e:
        print(f"\nError: {e}")
        error_correction(general, line_type, vcm, model)
        previous_run_static(model, general, line_type, vcm)

def run_static(model: OrcFxAPI.Model, rt_number: str, vcm: OrcFxAPI.OrcaFlexObject, line_type: OrcFxAPI.OrcaFlexObject, bend_restrictor_model: OrcFxAPI.OrcaFlexObject, line_obj: methods.Line, 
               bend_restrictor_object: methods.BendRestrictor, vcm_obj: methods.Vcm, general: OrcFxAPI.OrcaFlexObject, file_path: str, structural_limits: dict) -> None:
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
        line_obj: Line object in the orca.py
        bend_restrictor_object: Bend_restrictor in the orca.py
        vcm_obj: VCM object in the orca.py
        general: Orcaflex general to be passed for error correction
        file_path: Path where static runs are saved
        structural_limits: structural limits informed in RL
    Return:
        Nothing
    """
    try:
        print("__________________________________________________________________")
        print("_________________________RUNNING..._______________________________")
        print("__________________________________________________________________")
        global n_run, rotation, clearance, delta_flange, shear_force, bend_moment, n_run_error, prev_n_run, normalised_curvature, flange_loads
        
        vcm.DegreesOfFreedomInStatics = 'X,Y,Z'
        model.CalculateStatics()
        model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
        vcm.DegreesOfFreedomInStatics = 'All'
        model.CalculateStatics()

        n_run_error = 0

        rotation = verify_vcm_rotation(vcm)
        clearance = verify_line_clearance(line_type)
        delta_flange = verify_flange_height(line_type, line_obj, vcm_obj)

        static_dir = os.path.join(file_path, "Static")
        os.makedirs(static_dir, exist_ok=True)
        file_name = str(n_run) + "-" + rt_number + ".sim"
        save_simulation = os.path.join(static_dir, file_name)
        model.SaveSimulation(save_simulation)

        n_run += 1

        if n_run != prev_n_run:
            print(f"\n Running {n_run}th time.")
            prev_n_run = n_run
        print(f"\n Results"
              f"\n    VCM Rotation: {rotation}°."
              f"\n    Line Clearance: {clearance}m."
              f"\n    Flange Height error: {delta_flange}m.")
        
        flange_loads = verify_flange_loads(line_type, structural_limits, '2')
        normalised_curvature = verify_normalised_curvature(bend_restrictor_model, "Mean")   
        if normalised_curvature >= 1:
            verify_br_loads(bend_restrictor_model, bend_restrictor_object, "Mean")

    except Exception as e:
        print(f"\nError: {e}")
        error_correction(general, line_type, vcm, model)
        run_static(model, rt_number, vcm, line_type, bend_restrictor_model, line_obj, bend_restrictor_object, vcm_obj, general, file_path, structural_limits)

def error_correction(general: OrcFxAPI.OrcaFlexObject, line_type: OrcFxAPI.OrcaFlexObject, vcm: OrcFxAPI.OrcaFlexObject, model: OrcFxAPI.Model) -> None:
    """
    Description:
        Sequence of tentatives to improove convergence when Static Simulations fails
        1st - Reduce line's descriptization
        2st - Increase 3 times the Static damping range and Maximum number of iterations
        3st - Remove interation between line and seabed (just if they're touching)
        4st - Change line's static policy to Catenary
        5st - Increase even more the Static damping range and Maximum number of iterations
    Parameters:
        general: Orcaflex general
        line_type: Orcaflex line
        vcm: Orcaflex VCM
        model: Orcaflex model
    Return:
        Nothing
    """
    global n_run_error, n_run

    if n_run_error == 0:
        print(f"\nReducing line descriptization")
        n_sections = len(line_type.TargetSegmentLength)
        n = len(line_segments)
        i = 0
        while i < n_sections:
            if line_type.TargetSegmentLength[i] != '~':
                if i <= n - 1:
                    line_type.TargetSegmentLength[i] = 5 * line_segments[i]
                else:
                    line_type.TargetSegmentLength[i] = 5 * line_segments[-1]
            i += 1

    if n_run_error == 1:
        print(f"\nIncreasing 3 times the Static Damping Range and the Number of iterations")
        general.StaticsMinDamping = 3 * statics_min_damping
        general.StaticsMaxDamping = 3 * statics_max_damping
        general.StaticsMaxIterations = 3 * statics_max_iterations

    if n_run_error == 2:
        if clearance <= 0:
            print(f"\nRemoving interation between line and seabed")
            model_environment = model["Environment"]
            model_environment.SeabedNormalStiffness = 0
        else:
            n_run_error += 1

    if n_run_error == 3:
        print(f"\nChanging Line's Static policy to Catenary.")
        line_type.StaticsStep1 = "Catenary"

    if n_run_error == 4:
        print(f"\nDisplacing VCM")
        vcm.InitialX -= vcm_delta_x

    if n_run_error == 5:
        print(f"\nIncreasing 5 times the Static Damping Range and the Number of iterations")
        general.StaticsMinDamping = 5 * statics_min_damping
        general.StaticsMaxDamping = 5 * statics_max_damping
        general.StaticsMaxIterations = 5 * statics_max_iterations

    if n_run_error == 6:
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

    one_buoy = {buoy: float(buoy) for buoy in buoys}
    two_buoys = {f"{buoy1}+{buoy2}": one_buoy[buoy1] + one_buoy[buoy2] for i, buoy1 in enumerate(buoys) for j, buoy2 in enumerate(buoys) if i < j if one_buoy[buoy1] + one_buoy[buoy2] <= buoyancy_limit}
    three_buoys = {f"{buoy1}+{buoy2}+{buoy3}": (one_buoy[buoy1] + one_buoy[buoy2] + one_buoy[buoy3]) for i, buoy1 in enumerate(buoys) for j, buoy2 in enumerate(buoys) for k, buoy3 in enumerate(buoys) if i < j < k 
                   if (one_buoy[buoy1] + one_buoy[buoy2] + one_buoy[buoy3]) <= buoyancy_limit}
    
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
    """
    try:
        selection = {}
        comb_keys = list(combination_buoys.keys())
        for k in range(len(buoys_config[1])):
            j = 0
            while (combination_buoys[comb_keys[j]] < buoys_config[1][k] and combination_buoys[comb_keys[j + 1]] < buoys_config[1][k]):
                j += 1
            selection[comb_keys[j]] = combination_buoys[comb_keys[j]]
            comb_keys.remove(comb_keys[j])
        return selection
    
    except IndexError:
        buoys_config[1][k] = .9 * buoys_config[1][k]

        selection = {}
        comb_keys = list(combination_buoys.keys())
        for k in range(len(buoys_config[1])):
            j = 0
            while (combination_buoys[comb_keys[j]] < buoys_config[1][k] and combination_buoys[comb_keys[j + 1]] < buoys_config[1][k]):
                j += 1
            selection[comb_keys[j]] = combination_buoys[comb_keys[j]]
            comb_keys.remove(comb_keys[j])
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

    ibs_2 = [ibs_val[i][j] for i in range(len(ibs_val)) for j in range(len(ibs_val[i]))]
    b = 1
    for m in ibs_2:
        buoy = vessel + "_" + str(m)
        line_type.AttachmentType[b] = buoy
        b += 1

    ibs_1 = [ibs_key[z] for z in range(len(ibs_val)) for _ in range(len(ibs_val[z]))]
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
        print(f"\nLine's in contact with seabed")
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


def verify_flange_height(line_model: OrcFxAPI.OrcaFlexObject, line_obj: methods.Line, vcm_obj: methods.Vcm) -> float:
    """
    Description:
        Verify flange's height error
    Parameters:
        line_model: Orcaflex model
        line_obj: Line object in orca.py
        vcm_obj: VCM object in orca.py
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
    load_case = structural_limits[case]

    if case == "2":
        normal = abs(round(line_model.StaticResult("End Ez force", OrcFxAPI.oeEndB), 3))
        shear = abs(round(line_model.StaticResult("End Ex force", OrcFxAPI.oeEndB), 3))
        moment = abs(round(line_model.StaticResult("End Ey moment", OrcFxAPI.oeEndB), 3))
        print(f"\n        Normal force in flange's gooseneck: {normal}kN (Limit: {load_case[0]}kN)"
              f"\n        Shear force in flange's gooseneck: {shear}kN  (Limit: {load_case[1]}kN)"
              f"\n        Bend moment in flange's gooseneck: {moment}kN.m (Limit: {load_case[2]}kN)")
        flange_loads = (normal, shear, moment)

    else:
        if case == "3":
            print(f"\nFor heave period...")
        elif case == "3i":
            print(f"\nFor transition period...")
        elif case == "3ii":
            print(f"\nFor TDP period...")
        flange_loads = f_loads[0]
        print(f"\n        Normal force in flange's gooseneck: {flange_loads[0]}kN (Limit: {load_case[0]}kN)"
              f"\n        Shear force in flange's gooseneck: {flange_loads[1]}kN (Limit: {load_case[1]}kN)"
              f"\n        Bend moment in flange's gooseneck: {flange_loads[2]}kN.m (Limit: {load_case[2]}kN.m)")
        
    load_check = [flange_loads[i] < abs(round(load_case[i], 3)) for i in range(len(load_case))]
    if (loads := all(load_check)) == False:
        print("\nFlange loads aprooved!")
    else:
        print("\nFlange loads reprooved!")
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

def verify_br_loads(bend_restrictor_model: OrcFxAPI.OrcaFlexObject, bend_restrictor_object: methods.BendRestrictor, magnitude: str) -> list:
    """
    Description:
        Verify if bend restrictor's loads are admissible
    Parameters:
        bend_restrictor_model: Orcaflex bend restrictor
        bend_restrictor_object: Bend restrictor object in orca.py
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

def looping(model_line_type: OrcFxAPI.OrcaFlexObject, selection: dict, model: OrcFxAPI.Model, bend_restrictor_model: OrcFxAPI.OrcaFlexObject, rt_number: str, vessel: str, rl_config: list, buoy_set: list, 
            model_vcm: OrcFxAPI.OrcaFlexObject, object_line: methods.Line, object_bend_restrictor: methods.BendRestrictor, object_vcm: methods.Vcm, winch: OrcFxAPI.OrcaFlexObject, general: OrcFxAPI.OrcaFlexObject, 
            environment: OrcFxAPI.OrcaFlexObject, file_path: str, structural: dict, a_r: OrcFxAPI.OrcaFlexObject) -> None:
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
        object_line: Line object from orca.py
        object_bend_restrictor: Bend restrictor object from orca.py
        object_vcm: VCM object from orca.py
        winch: Orcaflex winch
        general: Orcaflex general
        environment: Orcaflex environment
        file_path: Path where static runs are saved
        structural: RL structural limits for loading in VCM's flange
        a_r: Orcaflex A&R cable
    Return:
        Nothing
    """
    global rotation, clearance, delta_flange, n_run, flange_loads, clearance_limit_sup, payout_retrieve_pace_min, vcm_rotation_inf_limit, looping_results, br_loads
    
    environment.SeabedOriginX = model_vcm.InitialX
    if general.StaticsMinDamping != statics_min_damping:
        general.StaticsMinDamping = statics_min_damping
        general.StaticsMaxDamping = statics_max_damping
        general.StaticsMaxIterations = statics_max_iterations
    if general.LineStaticsStep2Policy != "None":
        general.LineStaticsStep2Policy = "None"
    if environment.SeabedNormalStiffness != 100:
        environment.SeabedNormalStiffness = 100
    if model_line_type.TargetSegmentLength[0] != line_segments[0]:
        n_sections = len(model_line_type.TargetSegmentLength)
        n = len(line_segments)
        i = 0
        while i < n_sections:
            if model_line_type.TargetSegmentLength[i] != '~':
                if i <= n - 1:
                    model_line_type.TargetSegmentLength[i] = line_segments[i]
                else:
                    model_line_type.TargetSegmentLength[i] = line_segments[-1]
            i += 1
    
    if n_run > n_run_limit:
        rotation = .45
        clearance = .52
        delta_flange = 0
        flange_loads = True
        print("\nSorry, it was not possible to converge.")
    
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

        call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, environment, file_path, structural, a_r)
    
    if rotation > vcm_rotation_sup_limit:  # VCM inclined in line's direction

        limits = [buoy_position_far_vcm[i] for i in range(len(unique_positions))]  # limits for 'change position' of buoys

        if unique_positions[pointer] > limits[pointer]:  # condition that allows change buoy position
            new_positions = [buoy_position - buoy_position_pace for buoy_position in unique_positions]  # define the new positions for the buoys
            change_position(model_line_type, new_positions, pointer, num_positions, position)
            
            call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, environment, file_path, 
                        structural, a_r)
                
        else:  # change set of buoys
            call_change_buoys(unique_positions, rl_config, pointer, buoy_set, model_line_type, vessel, model_vcm, object_line, model, bend_restrictor_model, rt_number, object_bend_restrictor, object_vcm, winch, general, 
                                environment, file_path, structural, a_r, selection, buoy_model)
    
    elif rotation < vcm_rotation_inf_limit:  # VCM inclined away of line's direction

        limits = [buoy_position_near_vcm[i] for i in range(len(unique_positions))]  # limits for 'change position' of buoys

        if unique_positions[pointer] < limits[pointer]:  # condition that allows change buoy position
            new_positions = [buoy_position + buoy_position_pace for buoy_position in unique_positions]  # define the new positions for the buoys
            change_position(model_line_type, new_positions, pointer, num_positions, position)
            
            call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, winch, general, environment, file_path, 
                        structural, a_r)
                
        else:  # change set of buoys
            call_change_buoys(unique_positions, rl_config, pointer, buoy_set, model_line_type, vessel, model_vcm, object_line, model, bend_restrictor_model, rt_number, object_bend_restrictor, object_vcm, winch, general, 
                                environment, file_path, structural, a_r, selection, buoy_model)

    # if not br_loads:
    
    if delta_flange != delta_flange_error_limit:

        flange_height_correction(winch, delta_flange)

        general.StaticsMinDamping = 2 * statics_min_damping
        general.StaticsMaxDamping = 2 * statics_max_damping
        general.StaticsMaxIterations = 3 * statics_max_iterations

        call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel,
                    rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
                    winch, general, environment, file_path, structural, a_r)

def more_buoys(rl_config):
    """
    Add one place more to apply buoyance in the line
    """
    print(f"""\nProbably the suggestion of buoys was not that good.
          Gonna change it a little to see if it works...""")
    position = rl_config[0]
    buoys = rl_config[1]
    if rotation > vcm_rotation_sup_limit:
        new_position = position[-1] + 3
        position.append(new_position)
        new_buoy = 100
        buoys.append(new_buoy)
    new_rl_config = [position, buoys]
    return new_rl_config

def less_buoys(rl_config):
    """
    take out a place position of buoycy in the line
    """
    print(f"""\nProbably the suggestion of buoys was not that good.
          Gonna change it a little to see if it works...""")
    position = rl_config[0]
    buoys = rl_config[1]
    pos_off = position[-1]
    buoy_off = buoys[-1]
    position.remove(pos_off)
    buoys.remove(buoy_off)
    new_rl_config = [position, buoys]
    return new_rl_config
    
def call_loop(model_line_type: OrcFxAPI.OrcaFlexObject, selection: dict, model: OrcFxAPI.Model, bend_restrictor_model: OrcFxAPI.OrcaFlexObject, rt_number: str, vessel: str,
              rl_config: list, buoy_set: list, model_vcm: OrcFxAPI.OrcaFlexObject, object_line: methods.Line, object_bend_restrictor: methods.BendRestrictor, object_vcm: methods.Vcm, 
              winch: OrcFxAPI.OrcaFlexObject, general: OrcFxAPI.OrcaFlexObject, environment: OrcFxAPI.OrcaFlexObject, file_path: str, structural: dict, a_r: OrcFxAPI.OrcaFlexObject):
    """"""
    run_static(model, rt_number, model_vcm, model_line_type, bend_restrictor_model, object_line, 
               object_bend_restrictor, object_vcm, general, file_path, structural)
    user_specified(model, rt_number, file_path)
    looping(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel,
            rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
            winch, general, environment, file_path, structural, a_r)

def call_change_buoys(unique_positions, rl_config, pointer, buoy_set, model_line_type, vessel, model_vcm, object_line, model, bend_restrictor_model, rt_number, object_bend_restrictor, 
                      object_vcm, winch, general, environment, file_path, structural, a_r, selection, buoy_model):
    """"""
    try:
        if buoy_model != looping_results[-1]:
            if buoy_model not in looping_results:
                new_rl_config = changing_buoyancy(unique_positions, rl_config, pointer)
                selection = changing_buoys(selection, buoy_set, new_rl_config, model_line_type, vessel)
                call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel,
                            rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
                            winch, general, environment, file_path, structural,a_r)
            else:
                new_rl_config = more_buoys(rl_config)
                selection = changing_buoys(selection, buoy_set, new_rl_config, model_line_type, vessel)
                call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel,
                            rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
                            winch, general, environment, file_path, structural,a_r)
        else:
            new_rl_config = changing_buoyancy(unique_positions, rl_config, pointer)
            selection = changing_buoys(selection, buoy_set, new_rl_config, model_line_type, vessel)
            call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel,
                        rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
                        winch, general, environment, file_path, structural,a_r)
    except Exception:
        new_rl_config = more_buoys(rl_config)
        selection = changing_buoys(selection, buoy_set, new_rl_config, model_line_type, vessel)
        call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel,
                    rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
                    winch, general, environment, file_path, structural,a_r)

def change_position(line_model: OrcFxAPI.OrcaFlexObject, new_positions: list, pointer: int, num_positions: int, positions: list) -> None:
    """
    Changes buoy position with the index = pointer
    :param line_model: Line model
    :param new_positions: Next buoy position
    :param pointer: Position's index that will be changed
    :param num_positions: Number of buoys positions in the line
    :param positions: Buoys positions distance to the vcm
    :return: Nothing
    """
    p = 1
    for z in range(0, num_positions):
        if (positions[z] + buoy_position_pace == new_positions[pointer]
                or positions[z] - buoy_position_pace == new_positions[pointer]):
            print(f"\nChanging buoys position"
                  f"from {line_model.Attachmentz[p]} to {new_positions[pointer]}")
            line_model.Attachmentz[p] = new_positions[pointer]
        p += 1

def make_pointer(num_positions: float, positions: list) -> int:
    """
    Creates a pointer that selects which of the buoys positions is going to be changed
    :param positions: Buoys model positions
    :param num_positions: number of attachments (buoys) in all the line
    :return: pointer
    """
    if rotation > 0:
        pointer = 0
        if num_positions == 2:
            first_buoy_position = positions[0]
            second_buoy_position = positions[1]
            if second_buoy_position - first_buoy_position == min_distance_buoys:
                pointer = 1
        elif num_positions == 3:
            first_buoy_position = positions[0]
            second_buoy_position = positions[1]
            third_buoy_position = positions[2]
            if third_buoy_position - second_buoy_position == min_distance_buoys:
                pointer = 2
            elif second_buoy_position - first_buoy_position == min_distance_buoys:
                pointer = 1
        return pointer
    elif rotation < 0:
        pointer = num_positions - 1
        if num_positions == 2:
            first_buoy_position = positions[0]
            second_buoy_position = positions[1]
            if second_buoy_position - first_buoy_position == min_distance_buoys:
                pointer = 0
        elif num_positions == 3:
            first_buoy_position = positions[0]
            second_buoy_position = positions[1]
            third_buoy_position = positions[2]
            if third_buoy_position - second_buoy_position == min_distance_buoys:
                pointer = 1
            elif second_buoy_position - first_buoy_position == min_distance_buoys:
                pointer = 0
        return pointer


def changing_buoyancy(position: list, rl_config: list, pointer: int) -> list:
    """
    Determines a "new RL's configuration" to be sought
    :param position: buoy unique_positions in model
    :param rl_config: RL's configuration
    :param pointer: which buoy position change
    :return: New RL's Configuration
    """
    total_buoyancy = rl_config[1]
    if rotation > 0:
        if len(total_buoyancy) == 1:
            if (total := 50 + total_buoyancy[pointer]) < buoyancy_limit:
                total_buoyancy[pointer] = total
        elif len(total_buoyancy) == 2:
            if total_buoyancy[pointer - 1] >= 2 * total_buoyancy[pointer]:
                if (total := 50 + total_buoyancy[pointer]) < buoyancy_limit:
                    total_buoyancy[pointer] = total
            else:
                if (total := 50 + total_buoyancy[pointer-1]) < buoyancy_limit:
                    total_buoyancy[pointer-1] = total
        elif len(total_buoyancy) == 3:
            if total_buoyancy[pointer - 2] >= 2 * total_buoyancy[pointer - 1]:
                if total_buoyancy[pointer - 1] >= 2 * total_buoyancy[pointer]:
                    if (total := 50 + total_buoyancy[pointer]) < buoyancy_limit:
                        total_buoyancy[pointer] = total
                else:
                    if (total := 50 + total_buoyancy[pointer-1]) < buoyancy_limit:
                        total_buoyancy[pointer-1] = total
            else:
                if (total := 50 + total_buoyancy[pointer-2]) < buoyancy_limit:
                    total_buoyancy[pointer-2] = total

    elif rotation < 0:
        if len(total_buoyancy) == 1:
            if (total := total_buoyancy[pointer] - 50) > 0:
                total_buoyancy[pointer] = total
        elif len(total_buoyancy) == 2:
            if total_buoyancy[pointer + 1] <= 2 * total_buoyancy[pointer]:
                if (total := total_buoyancy[pointer] - 50) > 0:
                    total_buoyancy[pointer] = total
            else:
                if (total := total_buoyancy[pointer+1] - 50) > 0:
                    total_buoyancy[pointer+1] = total
        elif len(total_buoyancy) == 3:
            if total_buoyancy[pointer + 2] <= 2 * total_buoyancy[pointer+1]:
                if total_buoyancy[pointer + 1] <= 2 * total_buoyancy[pointer]:
                    if (total := total_buoyancy[pointer] - 50) > 0:
                        total_buoyancy[pointer] = total
                else:
                    if (total := total_buoyancy[pointer+1] - 50) > 0:
                        total_buoyancy[pointer+1] = total
            else:
                if (total := 50 + total_buoyancy[pointer+2]) < buoyancy_limit:
                    total_buoyancy[pointer+2] = total
    rl_config = [position, total_buoyancy]
    return rl_config


'''
2/1 -> se estiver aumentando o empuxo


1/2 -> se estiver reduzindo o empuxo

'''


def changing_buoys(selection: dict, buoy_set: list, new_rl_config: list, line_model: OrcFxAPI.OrcaFlexObject, vessel: str) -> dict:
    """
    Get the "New RL's Configuration" and inserts it in the model
    :param selection: Better available combination, that fits with RL's configuration suggestion
    :param buoy_set: Vessel's buoys
    :param new_rl_config: "New RL's Configuration" to be sought
    :param line_model: Line model
    :param vessel: Vessel's name (to identify the vessel's buoys)
    :return: the new 'selection'
    """
    print(f"\nChanging buoys"
          f"\nfrom {selection.keys()}: {selection.values()}")
    combination_buoys = buoy_combination(buoy_set)
    selection = buoyancy(new_rl_config, combination_buoys)
    print(f"to {selection.keys()}: {selection.values()}")
    treated_buoys = buoyancy_treatment(new_rl_config, selection)
    num_buoys = number_buoys(treated_buoys)
    input_buoyancy(line_model, num_buoys, treated_buoys, vessel)
    return selection


def payout_retrieve_line(line_model: OrcFxAPI.OrcaFlexObject, delta: float, object_line: methods.Line, a_r: OrcFxAPI.OrcaFlexObject) -> None:
    """
    Line's payout/retrieve
    :param delta: Line range to be retrieved or payed out
    :param line_model: Line model
    :return: Nothing
    """
    if clearance > .4 and clearance < .75:
        delta = delta / 2
    if object_line.length == object_line.lda:
        if delta > 0:
            print(f"\nPaying out {delta}m of line,\n"
                f"from {round(line_model.Length[0], 2)} to {round(line_model.Length[0] + delta, 2)}")
        else:
            print(f"\nRetrieving out {-delta}m of line,\n"
                f"from {round(line_model.Length[0], 2)} to {round(line_model.Length[0] + delta, 2)}")
        new_length = line_model.Length[0] + delta
        new_segment = new_length / 100
        line_model.Length[0] = round(new_length, 3)
        line_model.TargetSegmentLength[0] = round(new_segment, 3)
    else:
        if delta > 0:
            print(f"\nPaying out {delta}m of A/R,\n"
                  f"from {round(a_r.StageValue[0], 2)} to {round(a_r.StageValue[0] + delta, 2)}")
        else:
            print(f"\nRetrieving out {-delta}m of A/R, \n"
                  f"from {round(a_r.StageValue[0], 2)} to {round(a_r.StageValue[0] + delta, 2)}")
        a_r.StageValue[0] = round(a_r.StageValue[0] + delta, 3)


def flange_height_correction(winch: OrcFxAPI.OrcaFlexObject, delta: float) -> None:
    """
    Correct the flange height, with paying out / retrieving winch
    :param winch: Winch model
    :param delta: Flange height error
    :return: Nothing
    """
    if delta > 0:
        print(f"\nPaying out {delta}m from the winch,\n"
              f"from {round(winch.StageValue[0], 2)} to {round(winch.StageValue[0] + delta, 2)}")
    else:
        print(f"\nRetrieving out {-delta}m from the winch,\n"
              f"from {round(winch.StageValue[0], 2)} to {round(winch.StageValue[0] + delta, 2)}")
    winch.StageValue[0] = round(winch.StageValue[0] - delta, 3)

def dynamic_simulation(model: OrcFxAPI.Model, line: OrcFxAPI.OrcaFlexObject, vcm: OrcFxAPI.OrcaFlexObject, bend_restrictor: OrcFxAPI.OrcaFlexObject, bend_restrictor_obj: methods.BendRestrictor,
                       a_r: OrcFxAPI.OrcaFlexObject, save_simulation: str, structural_limits: dict, rt_number: str):
    """
    Runs dynamic simulation for 3 'heave up' options: [1.8, 2.0, 2.5].
    :param model: model in orcaflex
    :param line: line model
    :param vcm: vcm model
    :param bend_restrictor: stiffener model
    :param a_r: A/R cable model
    :param save_simulation: path to save dyn_file
    :param structural_limits: load limits cases in RL
    :return: nothing
    """
    global heave_up
    i = 0
    vcm.Connection == "Fixed"
    while i < len(heave_up):
        print(f"\nRunning dynamics for heave up in {heave_up[i]}m")
        a_r.StageValue[2] = -heave_up[i]
        file_name = rt_number + " - heave_" + str(heave_up[i]) + "m.sim"
        simulation = os.path.join(save_simulation, file_name)
        result = run_dynamic(model, line, bend_restrictor, bend_restrictor_obj, structural_limits, simulation)
        if result:
            print(f"\nPara {heave_up[i]}m de heave up, os esforços verificados no gooseneck são admissíveis.")
            i = len(heave_up)
        else:
            print(f"\nPara {heave_up[i]}m de heave up, os esforços verificados no gooseneck não são admissíveis.")
        i += 1

def run_dynamic(model: OrcFxAPI.Model, line: OrcFxAPI.OrcaFlexObject, bend_restrictor: OrcFxAPI.OrcaFlexObject, bend_restrictor_obj: methods.BendRestrictor, structural_limits: dict,
                simulation: str) -> bool:
    """
    Run simulation and work their results
    :param model: orcaflex model
    :param line: line model
    :param bend_restrictor: stiffener model
    :param bend_restrictor_obj: stiffener object
    :param structural_limits: load limits cases in RL
    :param simulation: path to save file after it runs
    :return: True / False
    """
    model.RunSimulation()
    model.SaveSimulation(simulation)
    dyn_result = dyn_results(line, bend_restrictor, bend_restrictor_obj)
    heave_up_loads = dyn_result[0]
    transition_loads = dyn_result[1]
    tdp_loads = dyn_result[2]
    dynamic_load = [verify_flange_loads(line, structural_limits, '3', heave_up_loads), verify_flange_loads(line, structural_limits, '3i', heave_up_loads), 
                    verify_flange_loads(line, structural_limits, '3ii', heave_up_loads), verify_flange_loads(line, structural_limits, '3', transition_loads),
                    verify_flange_loads(line, structural_limits, '3i', transition_loads), verify_flange_loads(line, structural_limits, '3ii', transition_loads),
                    verify_flange_loads(line, structural_limits, '3', tdp_loads), verify_flange_loads(line, structural_limits, '3i', tdp_loads),
                    verify_flange_loads(line, structural_limits, '3ii', tdp_loads)]
    return any(dynamic_load)
    

def dyn_results(line: OrcFxAPI.OrcaFlexObject, bend_restrictor: OrcFxAPI.OrcaFlexObject, bend_restrictor_obj: methods.BendRestrictor) -> list:
    """
    Extract the dynamic results
    :param line: line model
    :param bend_restrictor: stiffener model
    :param bend_restrictor_obj: stiffener object
    :return: Dynamic results
    """
    results = []
    max_absolut_load(line, heave_up_period, results)
    max_absolut_load(line, transition_period, results)
    max_absolut_load(line, tdp_period, results)
    nc_br = verify_normalised_curvature(bend_restrictor, "Max")
    if nc_br > 1:
        verify_br_loads(bend_restrictor, bend_restrictor_obj, "Max")
    return results


def max_absolut_load(line: OrcFxAPI.OrcaFlexObject, period: OrcFxAPI.SpecifiedPeriod, safe_list: list) -> None:
    """
    Get the max absolut loads of each period
    :param line: lone model
    :param period: period of the result
    :param safe_list: list where the results will be appended
    :return: nothing
    """
    min_normal = abs(round(min(line.TimeHistory('End Ez force', period, OrcFxAPI.oeEndB)), 3))
    max_normal = abs(round(max(line.TimeHistory('End Ez force', period, OrcFxAPI.oeEndB)), 3))
    normal = max(min_normal, max_normal)
    
    min_shear = abs(round(min(line.TimeHistory('End Ex force', period, OrcFxAPI.oeEndB)), 3))
    max_shear = abs(round(max(line.TimeHistory('End Ex force', period, OrcFxAPI.oeEndB)), 3))
    shear = max(min_shear, max_shear)
    
    min_moment = abs(round(min(line.TimeHistory('End Ey moment', period, OrcFxAPI.oeEndB)), 3))
    max_moment = abs(round(max(line.TimeHistory('End Ey moment', period, OrcFxAPI.oeEndB)), 3))
    moment = max(min_moment, max_moment)

    loads = [normal, shear, moment]
    safe_list.append(loads)
