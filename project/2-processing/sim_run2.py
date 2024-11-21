"""
Simulation methods for the automation.
"""

import OrcFxAPI
import methods
from collections import Counter

# CONSTANTS
n_run = 0  # Static running counter
n_run_limit = 50  # Limit number of tentatives to converge
n_run_error = 0  # Error correction counter
rotation = 0  # VCM's rotation
clearance = 0  # Line's clearance
delta_flange = 0  # Error to adjustment in Flange's height to the seabed
vcm_rotation_limit = .5  # VCM's rotation limit criteria
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


def run_static(model: OrcFxAPI.Model, rt_number: str, vcm: OrcFxAPI.OrcaFlexObject,
               line_type: OrcFxAPI.OrcaFlexObject, line_obj: methods.Line,
               vcm_obj: methods.Vcm, general: OrcFxAPI.OrcaFlexObject) -> None:
    """
    Static runs, then gets and show the results
    If fails, changes the StaticStep Policy and try again
    :param general: General configuration model
    :param vcm_obj: VCM object class
    :param line_obj: Line object class
    :param vcm: VCM model
    :param line_type: Line model
    :param model: Orca model
    :param rt_number: Analysis identification
    :return: Nothing
    """
    try:
        global n_run, rotation, clearance, delta_flange, n_run_error
        model.CalculateStatics()
        n_run_error = 0
        rotation = verify_vcm_rotation(vcm)
        clearance = verify_line_clearance(line_type)
        delta_flange = verify_flange_height(line_type, line_obj, vcm_obj)
        model.SaveSimulation(rt_number + "\\" + str(n_run) + "-" + rt_number + "_Static.sim")
        print(
            f"\nRunning {n_run}th time."
            f"\n\nVCM Rotation: {rotation}°."
            f"\nLine Clearance: {clearance}m."
            f"\nFlange Height error: {delta_flange}m."
        )
        n_run += 1

    except Exception as e:
        print(f"\nError: {e}"
              f"\nChanging Line's StaticStep to 'Catenary'"
              f"\nMoving VCM, in X axis.")
        error_correction(general, line_type, vcm)
        run_static(model, rt_number, vcm, line_type, line_obj, vcm_obj, general)


def error_correction(general: OrcFxAPI.OrcaFlexObject, line_type: OrcFxAPI.OrcaFlexObject,
                     vcm: OrcFxAPI.OrcaFlexObject):
    """
    What to do if occurs some exception while trying to run static calculations
    :param general: General configuration model
    :param line_type: Line model
    :param vcm: VCM model
    :return: Nothing
    """
    global n_run_error

    if n_run_error == 0:
        general.StaticsMinDamping = 2 * statics_min_damping
        general.StaticsMaxDamping = 2 * statics_max_damping
        general.StaticsMaxIterations = 3 * statics_max_iterations
    elif n_run_error == 1:
        line_type.StaticsStep1 = "Catenary"
    elif n_run_error == 2:
        vcm.InitialX -= vcm_delta_x

    n_run_error += 1


def user_specified(model: OrcFxAPI.Model, rt_number: str) -> None:
    """
    Set calculated positions in Line's StaticStep Policy
    :param rt_number: Analysis identification
    :param model: Orca model
    :return: Nothing
    """
    model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
    model.SaveData(rt_number + "\\" + rt_number + "_Static.dat")


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
    combination_buoys = {key: value
                         for key, value in combination.items()}
    combination_buoys = dict(
        sorted(combination_buoys.items(), key=lambda item: item[1], reverse=False))
    return combination_buoys


def buoyancy(buoys_config: list, combination_buoys: dict) -> dict:
    """
    Gives the best combination of buoys based on the initial suggestion
    :param combination_buoys: All possible combinations of 1 to 3 vessel's buoys
    :param buoys_config: RL's configuration suggestion
    :return: Better available combination, that fits with RL's configuration suggestion
    """
    selection = {}
    for k in range(len(buoys_config[1])):
        comb_keys = list(combination_buoys.keys())
        j = 0
        while (combination_buoys[comb_keys[j]] < buoys_config[1][k] and
               combination_buoys[comb_keys[j + 1]] < buoys_config[1][k]):
            j += 1
        key = comb_keys[j]
        value = combination_buoys[key]
        selection[key] = value
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
                for index, vsc in enumerate(line_clearance.Mean)]
    vsc_min = round(min(list_vsc), 4)
    if vsc_min < 0:
        print(f"\nLine's in contact with seabed")
    return vsc_min


def verify_vcm_rotation(vcm_: OrcFxAPI.OrcaFlexObject) -> float:
    """
    Verify which is the VCM's rotation
    :param vcm_: VCM model
    :return: VCM's rotation (in transversal axis)
    """
    vcm_rotation = round(vcm_.StaticResult("Rotation 2"), 4)
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
    delta = round(correct_depth - depth_verified, 4)
    return delta


def looping(model_line_type: OrcFxAPI.OrcaFlexObject, selection: dict, model: OrcFxAPI.Model,
            rt_number: str, vessel: str, rl_config: list, buoy_set: list,
            model_vcm: OrcFxAPI.OrcaFlexObject, object_line: methods.Line,
            object_vcm: methods.Vcm, winch: OrcFxAPI.OrcaFlexObject,
            general: OrcFxAPI.OrcaFlexObject, environment: OrcFxAPI.OrcaFlexObject) -> None:
    """
    In looping, controls the model's changing.
    If VCM's rotation's the problem: changes buoy position
    If can't, changes the buoys
    If Line's clearance's the problema: payout or retrieves line
    If there's need some adjustment in flange's height: payout or retrieves winch
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
    :param object_line: Line object class
    :param object_vcm: VCM object class
    :return:
    """

    global rotation, clearance, delta_flange

    general.LineStaticsStep2Policy = "None"
    environment.SeabedOriginX = model_vcm.InitialX
    general.StaticsMinDamping = statics_min_damping
    general.StaticsMaxDamping = statics_max_damping
    general.StaticsMaxIterations = statics_max_iterations

    if n_run > n_run_limit:
        rotation = 0
        clearance = .55
        delta_flange = 0
        print("\nSorry, it was not possible to converge.")

    if clearance < clearance_limit_inf or clearance > clearance_limit_sup:
        if clearance < payout_retrieve_pace_min:
            payout_retrieve_line(model_line_type, -payout_retrieve_pace_max)
        else:
            if clearance < clearance_limit_inf:
                payout_retrieve_line(model_line_type, -payout_retrieve_pace_min)
            else:
                payout_retrieve_line(model_line_type, payout_retrieve_pace_min)
        run_static(model, rt_number, model_vcm, model_line_type, object_line, object_vcm, general)
        user_specified(model, rt_number)
        looping(model_line_type, selection, model, rt_number, vessel, rl_config, buoy_set,
                model_vcm, object_line, object_vcm, winch, general, environment)

    if rotation > vcm_rotation_limit or rotation < -vcm_rotation_limit:

        number = model_line_type.NumberOfAttachments

        position = []
        k = 1
        for _ in range(1, number):
            position.append(model_line_type.Attachmentz[k])
            k += 1
        buoys = list(selection.values())
        buoy_model = [position, buoys]

        num_positions = len(Counter(buoy_model[0]))
        unique_positions = list(set(buoy_model[0]))
        pointer = make_pointer(num_positions, unique_positions)
        limits = [list(set(buoy_position_near_vcm[i]
                           for i in range(num_positions)))
                  if rotation > vcm_rotation_limit
                  else
                  list(set(buoy_position_far_vcm[i]
                           for i in range(num_positions)))][0]
        if unique_positions[pointer] != limits[pointer]:
            new_positions = [list(set(buoy_position - buoy_position_pace
                                      for buoy_position in unique_positions))
                             if rotation > vcm_rotation_limit
                             else
                             list(set(buoy_position + buoy_position_pace
                                      for buoy_position in unique_positions))][0]
            change_position(model_line_type, new_positions, pointer, num_positions, position)
            run_static(model, rt_number, model_vcm, model_line_type, object_line, object_vcm,
                       general)
            user_specified(model, rt_number)
            looping(model_line_type, selection, model, rt_number, vessel, rl_config, buoy_set,
                    model_vcm, object_line, object_vcm, winch, general, environment)
        else:
            new_rl_config = changing_buoyancy(rl_config, pointer)
            changing_buoys(selection, buoy_set, new_rl_config, model_line_type, vessel)
            run_static(model, rt_number, model_vcm, model_line_type, object_line, object_vcm,
                       general)
            user_specified(model, rt_number)
            looping(model_line_type, selection, model, rt_number, vessel, rl_config, buoy_set,
                    model_vcm, object_line, object_vcm, winch, general, environment)

    if delta_flange != delta_flange_error_limit:
        flange_height_correction(winch, delta_flange)
        general.StaticsMinDamping = 2 * statics_min_damping
        general.StaticsMaxDamping = 2 * statics_max_damping
        general.StaticsMaxIterations = 3 * statics_max_iterations
        run_static(model, rt_number, model_vcm, model_line_type, object_line, object_vcm, general)
        user_specified(model, rt_number)
        looping(model_line_type, selection, model, rt_number, vessel, rl_config, buoy_set,
                model_vcm, object_line, object_vcm, winch, general, environment)


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
    for z in range(0, num_positions - 1):
        if (positions[z] + buoy_position_pace == new_positions[pointer]
                or positions[z] - buoy_position_pace == new_positions[pointer]):
            line_model.Attachmentz[p] = new_positions[pointer]
        p += 1
    if rotation < 0:
        print(f"\nChanging buoys position"
              f"\nfrom {new_positions[pointer] + buoy_position_pace}m to {new_positions[pointer]}m")
    else:
        print(f"\nChanging buoys position"
              f"\nfrom {new_positions[pointer] - buoy_position_pace}m to {new_positions[pointer]}m")


def make_pointer(num_positions: float, positions: list) -> int:
    """
    Creates a pointer that selects which of the buoys positions is going to be changed
    :param positions: Buoys model positions
    :param num_positions: number of attachments (buoys) in all the line
    :return: pointer
    """
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
        if third_buoy_position - second_buoy_position == min_distance_buoys:
            pointer = 2
    return pointer


def changing_buoyancy(rl_config: list, pointer: int) -> list:
    """
    Determines a "new RL's configuration" to be sought
    :param rl_config: RL's configuration
    :param pointer: which buoy position change
    :return: New RL's Configuration
    """
    total_buoyancy = rl_config[1]
    if rotation > 0:
        if (total := (1 + buoyancy_pace) * total_buoyancy[pointer]) < buoyancy_limit:
            total_buoyancy[pointer] = max(total, total_buoyancy[pointer] + 100)
    elif rotation < 0:
        if (total := (1 - buoyancy_pace) * total_buoyancy[pointer]) > 0:
            total_buoyancy[pointer] = min(total, total_buoyancy[pointer] - 100)
    rl_config = [rl_config[0], total_buoyancy]
    return rl_config


def changing_buoys(selection: dict, buoy_set: list, new_rl_config: list,
                   line_model: OrcFxAPI.OrcaFlexObject, vessel: str) -> None:
    """
    Get the "New RL's Configuration" and inserts it in the model
    :param selection: Better available combination, that fits with RL's configuration suggestion
    :param buoy_set: Vessel's buoys
    :param new_rl_config: "New RL's Configuration" to be sought
    :param line_model: Line model
    :param vessel: Vessel's name (to identify the vessel's buoys)
    :return: Nothing
    """
    print(f"\nChanging buoys"
          f"\nfrom {tuple(selection.keys())}: {tuple(selection.values())}")

    combination_buoys = buoy_combination(buoy_set)
    selection = buoyancy(new_rl_config, combination_buoys)

    print(f"to {tuple(selection.keys())}: {tuple(selection.values())}")

    treated_buoys = buoyancy_treatment(new_rl_config, selection)
    num_buoys = number_buoys(treated_buoys)
    input_buoyancy(line_model, num_buoys, treated_buoys, vessel)


def payout_retrieve_line(line_model: OrcFxAPI.OrcaFlexObject, delta: float) -> None:
    """
    Line's payout/retrieve
    :param delta: Line range to be retrieved or payed out
    :param line_model: Line model
    :return: Nothing
    """
    if delta > 0:
        print(f"\nPaying out {delta}m from the line,\n"
              f"from {round(line_model.Length[0], 2)} to {round(line_model.Length[0] + delta, 2)}")
    else:
        print(f"\nRetrieving out {-delta}m from the line,\n"
              f"from {round(line_model.Length[0], 2)} to {round(line_model.Length[0] + delta, 2)}")

    line_model.Length[0] = round(line_model.Length[0] + delta, 4)


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

    winch.StageValue[0] = round(winch.StageValue[0] - delta, 4)
