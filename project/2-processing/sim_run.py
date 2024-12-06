"""
Simulation methods for the automation.
"""

import OrcFxAPI
import os
import methods
from collections import Counter

# CONSTANTS
n_run = 0  # Static running counter
n_run_limit = 50  # Limit number of tentatives to converge
n_run_error = 0  # Error correction counter
prev_n_run = 0  # Previous n_run to comparison
rotation = 0  # VCM's rotation
clearance = 0  # Line's clearance
delta_flange = 0  # Error to adjustment in Flange's height to the seabed
flange_loads = True  # aproove / reprove flange loads verification
normalised_curvature = 0  # Verify if bend restrictor is locked
shear_force = 0  # Shear force in Bend_restrictor
bend_moment = 0  # Bend moment in Bend_restrictor
vcm_rotation_sup_limit = .5  # VCM's rotation superior limit criteria
vcm_rotation_inf_limit = .0  # VCM's rotation inferior limit criteria
clearance_limit_inf = .5  # Line's clearance inferior limit range criteria
clearance_limit_sup = .65  # Line's clearance superior limit range criteria
delta_flange_error_limit = 0  # Error in Flange's height criteria
buoyancy_limit = 2_000  # Buoyancy limit per position criteria
buoyancy_pace = .1  # Buoyancy changes 10% in each looping, if needed
buoy_position_pace = .5  # Buoys movement 50 cm in each looping, if needed
buoy_position_near_vcm = [3, 6, 9]  # Buoy's nearest limit position to the VCM.
buoy_position_far_vcm = [4, 8, 12]  # Buoy's far limit position to the VCM
payout_retrieve_pace_min = .2  # Line's payout/retrieve: 20 cm in each looping
payout_retrieve_pace_max = .5  # Line's payout/retrieve: 50 m in each looping
min_distance_buoys = 3  # Minimum distance between buoys is, at least, 3m.
vcm_delta_x = 20  # VCM's movement: 20m (helps convergence when adjusting flange height)
statics_max_iterations = 400  # Maximum number of iterations
statics_min_damping = 5  # Minimum damping
statics_max_damping = 15  # Maximum damping
heave_up = [2.5, 2.0, 1.8]  # heave up options
heave_up_period = OrcFxAPI.SpecifiedPeriod(0, 2.15)  # period in which 'heave up' occurs
transition_period = OrcFxAPI.SpecifiedPeriod(2.15, 32.15)  # period between heave up and tdp
tdp_period = OrcFxAPI.SpecifiedPeriod(32.15, 72.15)  # period in which tdp occurs
total_period = OrcFxAPI.SpecifiedPeriod(0, 72.15)  # all period

def insert_vert(line: OrcFxAPI.OrcaFlexObject, start_pos: float):
    """
    Inserts Bend Restrictor
    :param line: line model
    :param start_pos: stiffener start position
    :return: Nothing
    """
    n_attach = line.NumberOfAttachments
    line.NumberOfAttachments = n_attach + 1
    line.AttachmentType[n_attach] = 'Vert'
    line.Attachmentz[n_attach] = start_pos
    line.AttachmentzRelativeTo[n_attach] = "End B"
    line.AttachmentName[n_attach] = "Stiffener1"

def previous_run_static(model: OrcFxAPI.Model, general: OrcFxAPI.OrcaFlexObject, 
                        line_type: OrcFxAPI.OrcaFlexObject, vcm: OrcFxAPI.OrcaFlexObject) -> None:
    """
    Previous statics runs
    :param model: Orca model
    :param general: General configuration model
    :param line_type: Line model
    :param vcm: VCM model
    :param start_pos: stiffener start position
    :return: Nothing
    """
    try:
        global n_run_error
        model.CalculateStatics()
        n_run_error = 0
    except Exception as e:
        print(f"\nError: {e}")
        error_correction(general, line_type, vcm)
        previous_run_static(model, general, line_type, vcm)


def run_static(model: OrcFxAPI.Model, rt_number: str, vcm: OrcFxAPI.OrcaFlexObject,
               line_type: OrcFxAPI.OrcaFlexObject, bend_restrictor_model: OrcFxAPI.OrcaFlexObject,
               line_obj: methods.Line, bend_restrictor_object: methods.BendRestrictor,
               vcm_obj: methods.Vcm, general: OrcFxAPI.OrcaFlexObject, file_path: str,
               structural_limits: dict) -> None:
    """
    Static runs, then gets and show the results
    If fails, changes the StaticStep Policy and try again
    :param bend_restrictor_object: Bend restrictor object
    :param bend_restrictor_model: Bend restrictor model
    :param general: General configuration model
    :param vcm_obj: VCM object class
    :param line_obj: Line object class
    :param vcm: VCM model
    :param line_type: Line model
    :param model: Orca model
    :param rt_number: Analysis identification
    :param file_path: Path to save files
    :return: Nothing
    """
    try:
        global n_run, rotation, clearance, delta_flange, shear_force, bend_moment, n_run_error, \
            prev_n_run, normalised_curvature, flange_loads
        
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
            print(f"\nRunning {n_run}th time.")
            prev_n_run = n_run
        print(
            f"\n    Results"
            f"\n        VCM Rotation: {rotation}°."
            f"\n        Line Clearance: {clearance}m."
            f"\n        Flange Height error: {delta_flange}m."
        )
        flange_loads = verify_flange_loads(line_type, structural_limits, '2')
        normalised_curvature = verify_normalised_curvature(bend_restrictor_model, "Mean")   
        if normalised_curvature >= 1:
            verify_br_loads(bend_restrictor_model, bend_restrictor_object, "Mean")
    except Exception as e:
        print(f"\nError: {e}")
        error_correction(general, line_type, vcm)
        run_static(model, rt_number, vcm, line_type, bend_restrictor_model, line_obj,
                   bend_restrictor_object, vcm_obj, general, file_path, structural_limits)


def error_correction(general: OrcFxAPI.OrcaFlexObject, line_type: OrcFxAPI.OrcaFlexObject,
                     vcm: OrcFxAPI.OrcaFlexObject):
    """
    What to do if occurs some exception while trying to run static calculations
    :param general: General configuration model
    :param line_type: Line model
    :param vcm: VCM model
    :return: Nothing
    """
    global n_run_error, n_run
    
    if n_run_error == 0:
        print(f"\nChanging Line's Static policy to Catenary.")
        line_type.StaticsStep1 = "Catenary"
    
    elif n_run_error == 1:
        print(f"\nDisplacing VCM")
        vcm.InitialX -= vcm_delta_x
    
    elif n_run_error == 2:
        print(f"\nChanging Static damping range and Increasing iterations.")
        general.StaticsMinDamping = 5 * statics_min_damping
        general.StaticsMaxDamping = 5 * statics_max_damping
        general.StaticsMaxIterations = 5 * statics_max_iterations
    
    if n_run_error == 3:
        n_run = n_run_limit + 1

    n_run_error += 1


def user_specified(model: OrcFxAPI.Model, rt_number: str, file_path: str) -> None:
    """
    Set calculated positions in Line's StaticStep Policy
    :param rt_number: Analysis identification
    :param model: Orca model
    :return: Nothing
    """
    model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
    file_name = rt_number + ".dat"
    save_data = os.path.join(file_path, file_name)
    model.SaveData(save_data)


def buoy_combination(b_set: list) -> dict:
    """
    Make combinations with 1 to 3 buoys, below 2 tf of buoyancy
    :param b_set: Vessel's buoys
    :return: All possible combinations of 1 to 3 vessel's buoys
    """
    buoys = [str(b_set[1][i])
             for i in range(len(b_set[0]))
             for _ in range(b_set[0][i])]
    one_buoy = {buoy: float(buoy)
                for buoy in buoys}
    two_buoys = {f"{buoy1}+{buoy2}": one_buoy[buoy1] + one_buoy[buoy2]
                 for i, buoy1 in enumerate(buoys)
                 for j, buoy2 in enumerate(buoys)
                 if i < j
                 if one_buoy[buoy1] + one_buoy[buoy2] <= buoyancy_limit}
    three_buoys = {f"{buoy1}+{buoy2}+{buoy3}": (one_buoy[buoy1] + one_buoy[buoy2] + one_buoy[buoy3])
                   for i, buoy1 in enumerate(buoys)
                   for j, buoy2 in enumerate(buoys)
                   for k, buoy3 in enumerate(buoys)
                   if i < j < k
                   if (one_buoy[buoy1] + one_buoy[buoy2] + one_buoy[buoy3]) <= buoyancy_limit}
    combination = {**one_buoy, **two_buoys, **three_buoys}
    combination_buoys = {key: value for key, value in combination.items()}
    combination_buoys = dict( sorted(combination_buoys.items(), key=lambda item: item[1], reverse=False))
    return combination_buoys


def buoyancy(buoys_config: list, combination_buoys: dict) -> dict:
    """
    Gives the best combination of buoys based on the initial suggestion
    :param combination_buoys: All possible combinations of 1 to 3 vessel's buoys
    :param buoys_config: RL's configuration suggestion
    :return: Better available combination, that fits with RL's configuration suggestion
    """
    try:
        selection = {}
        comb_keys = list(combination_buoys.keys())
        for k in range(len(buoys_config[1])):
            j = 0
            while (combination_buoys[comb_keys[j]] < buoys_config[1][k] and
                combination_buoys[comb_keys[j + 1]] < buoys_config[1][k]):
                j += 1
            key = comb_keys[j]
            value = combination_buoys[key]
            selection[key] = value
            comb_keys.remove(key)
        return selection
    except IndexError:
        buoys_config[1][k] = .9 * buoys_config[1][k]
        selection = {}
        comb_keys = list(combination_buoys.keys())
        for k in range(len(buoys_config[1])):
            j = 0
            while (combination_buoys[comb_keys[j]] < buoys_config[1][k] and
                combination_buoys[comb_keys[j + 1]] < buoys_config[1][k]):
                j += 1
            key = comb_keys[j]
            value = combination_buoys[key]
            selection[key] = value
            comb_keys.remove(key)
        return selection


def buoyancy_treatment(buoys_config: list, selection: dict) -> dict:
    """
    It uses initial buoyancy and treats it to return the entry data for
    OrcaFlex, referring the initial buoyancy
    :param selection: Better available combination, that fits with RL's configuration suggestion
    :param buoys_config: RL's configuration suggestion
    :return: Orca buoys attachments
    """
    position = buoys_config[0]
    treated_buoys = {position[i]: list(selection.keys())[i].split("+")
                     for i in range(len(list(selection.keys())))}
    return treated_buoys


def number_buoys(treated_buoys: dict) -> int:
    """
    Gives the number of attachments buoys
    :param treated_buoys: Orca buoys attachments
    :return: Number of attachments
    """
    packs = [buoy[i]
             for buoy in treated_buoys.values()
             for i in range(len(buoy))]
    return len(packs)


def input_buoyancy(line_type: OrcFxAPI.OrcaFlexObject, num_buoys: float,
                   treated_buoys: dict, vessel: str) -> None:
    """
    Input the attachments (buoys)
    :param line_type: Line model
    :param vessel: Vessel's name (to identify the vessel's buoys)
    :param num_buoys: Number of attachments
    :param treated_buoys: Orca buoys attachments
    :return: Nothing
    """
    line_type.NumberOfAttachments = int(num_buoys + 1)
    ibs_key = tuple(treated_buoys.keys())
    ibs_val = tuple(treated_buoys.values())
    ibs_2 = []
    for i in range(len(ibs_val)):
        for j in range(len(ibs_val[i])):
            ibs_2.append(ibs_val[i][j])
    b = 1
    for m in ibs_2:
        buoy = vessel + "_" + str(m)
        line_type.AttachmentType[b] = buoy
        b += 1
    ibs_1 = []
    for z in range(len(ibs_val)):
        for _ in range(len(ibs_val[z])):
            ibs_1.append(ibs_key[z])
    p = 1
    for n in ibs_1:
        line_type.Attachmentz[p] = n
        p += 1


def verify_line_clearance(line_model: OrcFxAPI.OrcaFlexObject) -> float:
    """
    Verify which is the minimum line's clearance
    :param line_model: Line model
    :return: Line's clearance
    """
    line_clearance = line_model.RangeGraph("Seabed clearance")
    list_vsc = [vsc
                for _, vsc in enumerate(line_clearance.Mean)]
    vsc_min = round(min(list_vsc), 3)
    if vsc_min < 0:
        print(f"\nLine's in contact with seabed")
    return vsc_min


def verify_vcm_rotation(vcm_: OrcFxAPI.OrcaFlexObject) -> float:
    """
    Verify which is the VCM's rotation
    :param vcm_: VCM model
    :return: VCM's rotation (in transversal axis)
    """
    vcm_rotation = round(vcm_.StaticResult("Rotation 2"), 3)
    return vcm_rotation


def verify_flange_height(line_model: OrcFxAPI.OrcaFlexObject, line_obj: methods.Line,
                         vcm_obj: methods.Vcm) -> float:
    """
    Verify what is the flange height error/variation
    :param vcm_obj: VCM object
    :param line_obj: Line object
    :param line_model: Line model
    :return: Flange height error/variation
    """
    correct_depth = - line_obj.lda + (vcm_obj.a / 1_000)
    depth_verified = line_model.StaticResult("Z", OrcFxAPI.oeEndB)
    delta = round(correct_depth - depth_verified, 3)
    return delta


def verify_flange_loads(line_model: OrcFxAPI.OrcaFlexObject, structural_limits: dict,
                        case: str, *f_loads: list) -> bool:
    """
    Verify the loads in gooseneck of the flange
    :param line_model: line in model
    :param structural_limts: structural limits informed in RL
    :param case: case of load [2, 3, 3i, 3ii]
    :return: True if the loads are above the limits, false if not
    """
    load_case = structural_limits[case]
    if case == "2":
        normal = abs(round(line_model.StaticResult("End Ez force", OrcFxAPI.oeEndB), 3))
        shear = abs(round(line_model.StaticResult("End Ex force", OrcFxAPI.oeEndB), 3))
        moment = abs(round(line_model.StaticResult("End Ey moment", OrcFxAPI.oeEndB), 3))
        print(
            f"\n        Normal force in flange's gooseneck: {normal}kN (Limit: {load_case[0]}kN)"
            f"\n        Shear force in flange's gooseneck: {shear}kN  (Limit: {load_case[1]}kN)"
            f"\n        Bend moment in flange's gooseneck: {moment}kN.m (Limit: {load_case[2]}kN)"
        )
        flange_loads = (normal, shear, moment)
    else:
        if case == "3":
            print(f"\nFor heave period...")
        elif case == "3i":
            print(f"\nFor transition period...")
        elif case == "3ii":
            print(f"\nFor TDP period...")
        flange_loads = f_loads[0]
        print(
            f"\n        Normal force in flange's gooseneck: {flange_loads[0]}kN (Limit: {load_case[0]}kN)"
            f"\n        Shear force in flange's gooseneck: {flange_loads[1]}kN (Limit: {load_case[1]}kN)"
            f"\n        Bend moment in flange's gooseneck: {flange_loads[2]}kN.m (Limit: {load_case[2]}kN.m)"
        )
    load_check = []
    for i in range(len(load_case)):
        if flange_loads[i] < abs(round(load_case[i], 3)):
            load_check.append(True)
        else:
            load_check.append(False)
    if (loads := all(load_check)) == False:
        print("\nOs esforços verificados no gooseneck não são admissíveis")
    else:
        print("\nOs esforços verificados no gooseneck são admissíveis.")
    return loads


def verify_normalised_curvature(bend_restrictor_model: OrcFxAPI.OrcaFlexObject, magnitude: str) -> float:
    """
    Verify if the bend_restrictor is locked
    :param bend_restrictor_model: stiffener1 in model
    :return: normalised_curvature result
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


def verify_br_loads(bend_restrictor_model: OrcFxAPI.OrcaFlexObject,
                    bend_restrictor_object: methods.BendRestrictor,
                    magnitude: str) -> float:
    """
    Verify the bend moment in bend restrictor
    :param bend_restrictor_model: bend restrictor in model
    :param bend_restrictor_object: bend restrictor object
    :return: bend moment in bend restrictor
    """
    limit_sf, limit_bf = bend_restrictor_object.sf, bend_restrictor_object.bm
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
    print(
        f"\n        Shear force in bend_restrictor: {max_shear}kN (Limit: {limit_sf}kN)"
        f"\n        Bend moment in bend_restrictor: {max_moment}kN.m (Limit: {limit_bf}kN.m)"
        )
    load_check = []
    br_loads = [max_shear, max_moment]
    load_case = [limit_sf, limit_bf]
    for i in range(len(load_case)):
        if br_loads[i] < abs(round(load_case[i], 3)):
            load_check.append(True)
        else:
            load_check.append(False)
    if all(load_check):
        print("\nOs esforços verificados na vértebra são admissíveis.")
    else:
        print("\nOs esforços verificados na vértebra não são admissíveis")

def looping(model_line_type: OrcFxAPI.OrcaFlexObject, selection: dict, model: OrcFxAPI.Model,
            bend_restrictor_model: OrcFxAPI.OrcaFlexObject, rt_number: str, vessel: str,
            rl_config: list, buoy_set: list, model_vcm: OrcFxAPI.OrcaFlexObject,
            object_line: methods.Line, object_bend_restrictor: methods.BendRestrictor,
            object_vcm: methods.Vcm, winch: OrcFxAPI.OrcaFlexObject,
            general: OrcFxAPI.OrcaFlexObject, environment: OrcFxAPI.OrcaFlexObject,
            file_path: str, structural: dict, a_r: OrcFxAPI.OrcaFlexObject) -> None:
    """
    In looping, controls the model's changing.
    If VCM's rotation's the problem: changes buoy position
    If can't, changes the buoys
    If Line's clearance's the problema: payout or retrieves line
    If there's need some adjustment in flange's height: payout or retrieves winch
    :param structural: structural limits in the flange
    :param file_path: path to save files
    :param bend_restrictor_model: Bend restrictor model
    :param object_bend_restrictor: Bend restrictor object
    :param environment: Environment model
    :param general: General configuration model
    :param winch: Winch model
    :param model_line_type: Line model
    :param selection: Better available combination, that fits with RL's configuration suggestion
    :param model: Orca model
    :param rt_number: Analysis identification
    :param vessel: Vessel's name (to identify the vessel's buoys)
    :param rl_config: RL's configuration suggestion
    :param buoy_set: Vessel's buoys
    :param model_vcm: VCM model
    :param a_r: A/R cable model
    :param object_line: Line object class
    :param object_vcm: VCM object class
    :return:
    """
    global rotation, clearance, delta_flange, n_run, flange_loads, clearance_limit_sup, \
        payout_retrieve_pace_min, vcm_rotation_inf_limit

    environment.SeabedOriginX = model_vcm.InitialX
    if general.StaticsMinDamping != statics_min_damping:
        general.StaticsMinDamping = statics_min_damping
        general.StaticsMaxDamping = statics_max_damping
        general.StaticsMaxIterations = statics_max_iterations
    if general.LineStaticsStep2Policy != "None":
        general.LineStaticsStep2Policy = "None"
    
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
    num_positions = len(buoy_model[0])
    unique_positions = list(Counter(position).keys())
    pointer = make_pointer(len(unique_positions), unique_positions, model_line_type)
    if clearance < clearance_limit_inf or clearance > clearance_limit_sup:
        if clearance < 0:
            payout_retrieve_line(model_line_type, -payout_retrieve_pace_max, object_line, a_r)
        elif clearance < clearance_limit_inf:
            payout_retrieve_line(model_line_type, - payout_retrieve_pace_min, object_line, a_r)
        elif clearance > clearance_limit_sup:
            payout_retrieve_line(model_line_type, payout_retrieve_pace_min, object_line, a_r)
        n_run = max(n_run - 1, 0)  # não contabiliza ajustes no comprimento da linha como iteração
        call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel,
                rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
                winch, general, environment, file_path, structural, a_r)
    if vcm_rotation_inf_limit > abs(rotation) or abs(rotation) > vcm_rotation_sup_limit:
        limits = [buoy_position_near_vcm[i] for i in range(len(unique_positions))] if rotation > vcm_rotation_sup_limit \
            else [buoy_position_far_vcm[i] for i in range(len(unique_positions))]
        if unique_positions[pointer] != limits[pointer]:
            new_positions = [list(set(buoy_position - buoy_position_pace for buoy_position in unique_positions)) if rotation > vcm_rotation_sup_limit \
                else list(set(buoy_position + buoy_position_pace for buoy_position in unique_positions))][0]
            change_position(model_line_type, new_positions, pointer, num_positions, position)
            call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel,
                        rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
                        winch, general, environment, file_path, structural,a_r)
        else:
            try:
                new_rl_config = changing_buoyancy(unique_positions, rl_config, pointer)
                selection = changing_buoys(selection, buoy_set, new_rl_config, model_line_type, vessel)
                call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel,
                            rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
                            winch, general, environment, file_path, structural,a_r)
            except Exception as error:
                print(f"\n Error: {error}")
                pass
    if delta_flange != delta_flange_error_limit:
        flange_height_correction(winch, delta_flange)
        general.StaticsMinDamping = 2 * statics_min_damping
        general.StaticsMaxDamping = 2 * statics_max_damping
        general.StaticsMaxIterations = 3 * statics_max_iterations
        call_loop(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel,
                    rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
                    winch, general, environment, file_path, structural, a_r)


def call_loop(model_line_type: OrcFxAPI.OrcaFlexObject, selection: dict, model: OrcFxAPI.Model,
            bend_restrictor_model: OrcFxAPI.OrcaFlexObject, rt_number: str, vessel: str,
            rl_config: list, buoy_set: list, model_vcm: OrcFxAPI.OrcaFlexObject,
            object_line: methods.Line, object_bend_restrictor: methods.BendRestrictor,
            object_vcm: methods.Vcm, winch: OrcFxAPI.OrcaFlexObject,
            general: OrcFxAPI.OrcaFlexObject, environment: OrcFxAPI.OrcaFlexObject,
            file_path: str, structural: dict, a_r: OrcFxAPI.OrcaFlexObject):
    """"""
    run_static(model, rt_number, model_vcm, model_line_type, bend_restrictor_model, object_line, 
               object_bend_restrictor, object_vcm, general, file_path, structural)
    user_specified(model, rt_number, file_path)
    looping(model_line_type, selection, model, bend_restrictor_model, rt_number, vessel,
            rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
            winch, general, environment, file_path, structural, a_r)


def change_position(line_model: OrcFxAPI.OrcaFlexObject, new_positions: list, pointer: int,
                    num_positions: int, positions: list) -> None:
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


def make_pointer(num_positions: float, positions: list, line: OrcFxAPI.OrcaFlexObject) -> int:
    """
    Creates a pointer that selects which of the buoys positions is going to be changed
    :param positions: Buoys model positions
    :param num_positions: number of attachments (buoys) in all the line
    :return: pointer
    """
    try:
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
            if second_buoy_position - first_buoy_position == min_distance_buoys:
                pointer = 1
            elif third_buoy_position - second_buoy_position == min_distance_buoys:
                pointer = 2

        """attach = list(line.AttachmentType)
        attach_pos = list(line.Attachmentz)
        vert_index = attach.index('Vert')
        attach_pos.remove(attach_pos[vert_index])
        if rotation > vcm_rotation_sup_limit:
            if attach_pos[pointer + 1] - attach_pos[pointer] == 3:
                pointer += 1"""
        return pointer
    except IndexError:
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
        if (total := (1 + buoyancy_pace) * total_buoyancy[pointer]) < buoyancy_limit:
            total_buoyancy[pointer] = total
    elif rotation < 0:
        if (total := (1 - buoyancy_pace) * total_buoyancy[pointer]) > 0:
            total_buoyancy[pointer] = total
    rl_config = [position, total_buoyancy]
    return rl_config


def changing_buoys(selection: dict, buoy_set: list, new_rl_config: list,
                   line_model: OrcFxAPI.OrcaFlexObject, vessel: str) -> dict:
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


def payout_retrieve_line(line_model: OrcFxAPI.OrcaFlexObject, delta: float,
                         object_line: methods.Line, a_r: OrcFxAPI.OrcaFlexObject) -> None:
    """
    Line's payout/retrieve
    :param delta: Line range to be retrieved or payed out
    :param line_model: Line model
    :return: Nothing
    """
    delta = round(delta, 2)
    if object_line.length == object_line.lda:
        if delta > 0:
            print(f"\nPaying out {delta}m of line,\n"
                f"from {round(line_model.Length[0], 2)} to {round(line_model.Length[0] + delta, 2)}")
        else:
            print(f"\nRetrieving out {-delta}m of line,\n"
                f"from {round(line_model.Length[0], 2)} to {round(line_model.Length[0] + delta, 2)}")
        line_model.Length[0] = round(line_model.Length[0] + delta, 3)
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

def dynamic_simulation(model: OrcFxAPI.Model, line: OrcFxAPI.OrcaFlexObject,
                       vcm: OrcFxAPI.OrcaFlexObject, bend_restrictor: OrcFxAPI.OrcaFlexObject,
                       bend_restrictor_obj: methods.BendRestrictor,
                       a_r: OrcFxAPI.OrcaFlexObject, save_simulation: str,
                       structural_limits: dict, rt_number: str):
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

def run_dynamic(model: OrcFxAPI.Model, line: OrcFxAPI.OrcaFlexObject,
                bend_restrictor: OrcFxAPI.OrcaFlexObject, 
                bend_restrictor_obj: methods.BendRestrictor, structural_limits: dict,
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
    dynamic_load = [
        verify_flange_loads(line, structural_limits, '3', heave_up_loads),
        verify_flange_loads(line, structural_limits, '3i', heave_up_loads),
        verify_flange_loads(line, structural_limits, '3ii', heave_up_loads),
        verify_flange_loads(line, structural_limits, '3', transition_loads),
        verify_flange_loads(line, structural_limits, '3i', transition_loads),
        verify_flange_loads(line, structural_limits, '3ii', transition_loads),
        verify_flange_loads(line, structural_limits, '3', tdp_loads),
        verify_flange_loads(line, structural_limits, '3i', tdp_loads),
        verify_flange_loads(line, structural_limits, '3ii', tdp_loads),
    ]
    return any(dynamic_load)
    

def dyn_results(line: OrcFxAPI.OrcaFlexObject, bend_restrictor: OrcFxAPI.OrcaFlexObject, 
                bend_restrictor_obj: methods.BendRestrictor) -> list:
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
