"""
Simulation methods for the automation.
"""
from typing import Tuple

import OrcFxAPI
import methods

n_run = 0


def run_static_simulation(model: OrcFxAPI.Model, rt_number: str) -> None:
    """
    Runs and save a static simulation
    :param rt_number: rt identification
    :param model: OrcaFlex model
    :return:
    """
    model.CalculateStatics()
    global n_run
    model.SaveSimulation(rt_number + "\\" + str(n_run) + "-" + rt_number +
                         "_Static.sim")

    n_run += 1
    print(f"\nRunning time {n_run}")


def user_specified(model: OrcFxAPI.Model, rt_number: str) -> None:
    """
    Put the static line's position in user_specified method
    :param rt_number: rt identification
    :param model: OrcaFlex model
    :return:
    """
    model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
    model.SaveData(rt_number + "\\" + rt_number + "_Static.dat")


def buoy_combination(b_set: list) -> dict:
    """
    Make combinations with 1 to 3 buoys, below 2 tf of buoyancy
    :param b_set: vessel's buoys dict
    :return: all possible combinations of 1 to 3 vessel's buoys
    """
    buoys = [
        str(b_set[1][i])
        for i in range(len(b_set[0]))
        for _ in range(b_set[0][i])
    ]
    one_buoy = {
        buoy: float(buoy)
        for buoy in buoys
    }
    two_buoys = {
        f"{buoy1}+{buoy2}": one_buoy[buoy1] + one_buoy[buoy2]
        for i, buoy1 in enumerate(buoys)
        for j, buoy2 in enumerate(buoys)
        if i < j
        if one_buoy[buoy1] + one_buoy[buoy2] <= 2_000
    }
    three_buoys = {
        f"{buoy1}+{buoy2}+{buoy3}": (one_buoy[buoy1] + one_buoy[buoy2] +
                                     one_buoy[buoy3])
        for i, buoy1 in enumerate(buoys)
        for j, buoy2 in enumerate(buoys)
        for k, buoy3 in enumerate(buoys)
        if i < j < k
        if (one_buoy[buoy1] + one_buoy[buoy2] + one_buoy[buoy3]) <= 2_000
    }
    combination = {
        **one_buoy, **two_buoys, **three_buoys
    }
    combination_buoys = {
        key: value
        for key, value in combination.items()
    }
    combination_buoys = dict(sorted(
        combination_buoys.items(),
        key=lambda item: item[1],
        reverse=False)
    )
    return combination_buoys


def buoyancy(buoys_config: list, combination_buoys: dict) -> dict:
    """
    Gives the best combination of buoys based on the initial suggestion
    :param combination_buoys: actual buoy combination, in the model
    :param buoys_config: buoy parameter (RL's configuration suggestion)
    :return: better available combination, based on the buoys_config
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
    :param selection: selection of buoys to OrcaFlex
    :param buoys_config: initial buoyancy suggestion
    :return: buoy combination in better format to attack it in orcaflex
    """
    position = buoys_config[0]
    treated_buoys = {position[i]: list(selection.keys())[i].split("+")
                     for i in range(len(list(selection.keys())))}
    return treated_buoys


def number_buoys(treated_buoys: dict) -> int:
    """
    Gives the number of attachments buoys
    :param treated_buoys: set of selected buoys
    :return: number of selected buoys
    """
    packs = [buoy[i]
             for buoy in treated_buoys.values()
             for i in range(len(buoy))]
    return len(packs)


def input_buoyancy(line_type: OrcFxAPI.OrcaFlexObject, num_buoys: float,
                   treated_buoys: dict, vessel: str) -> None:
    """
    Add the first model's buoyancy configuration
    :param line_type: line type
    :param vessel: operation's vessel
    :param num_buoys: attachments quantity
    :param treated_buoys: buoy selection to the Orca model
    :return: nothing
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
    :param line_model: OrcaFlex's line
    :return: clearance
    """
    line_clearance = line_model.RangeGraph("Seabed clearance")
    list_vsc = [vsc
                for index, vsc in enumerate(line_clearance.Mean)]
    vsc_min = min(list_vsc)
    print(f"\nClearance: {vsc_min}")
    return vsc_min


def verify_vcm_rotation(vcm_: OrcFxAPI.OrcaFlexObject) -> float:
    """
    Verify which is the vcm's rotation
    :param vcm_: OrcaFlex's vcm
    :return: rotation in y_axis
    """
    vcm_rotation = vcm_.StaticResult("Rotation 2")
    print(f"\nRotation: {vcm_rotation}")
    return vcm_rotation


def verify_flange_height(line_model: OrcFxAPI.OrcaFlexObject,
                         line_obj: methods.Line,
                         vcm_obj: methods.Vcm) -> float:
    """
    Verify what is the flange height, and if it's wrong,
    corrects it with the winch
    :param vcm_obj: vcm object
    :param line_obj: line object
    :param line_model: line model
    :return:
    """
    correct_depth = - line_obj.lda + (vcm_obj.a / 1_000)
    depth_verified = line_model.StaticResult("Z", OrcFxAPI.oeEndB)
    delta = round(correct_depth - depth_verified, 4)
    return delta


def get_result(rotation: float, clearance: float, delta_flange_height) -> str:
    """
    Controls the looping
    :param rotation: vcm rotation result
    :param clearance: line clearance result
    :param delta_flange_height: flange height error
    :return: red or green
    """
    if abs(rotation) > .5:
        result = "red"
    elif .5 > clearance > .7:
        result = "red"
    elif delta_flange_height != 0:
        result = "red"
    else:
        result = "green"
    return result


def l_c_b_p(new_positions: list, model_line_type: OrcFxAPI.OrcaFlexObject, number: int,
            model_buoys_position: list, pointer: int, model: OrcFxAPI.Model, rt_number: str,
            model_vcm: OrcFxAPI.OrcaFlexObject, object_line: methods.Line, object_vcm: methods.Vcm):
    """
    l_c_b_p = looping changing buoy position
    :param new_positions:
    :param model_line_type:
    :param number:
    :param model_buoys_position:
    :param pointer:
    :param model:
    :param rt_number:
    :param model_vcm:
    :param object_line:
    :param object_vcm:
    :return: looping results
    """
    change_buoy_position(new_positions, model_line_type, number, model_buoys_position, pointer)

    run_static_simulation(model, rt_number)

    rotation = verify_vcm_rotation(model_vcm)
    clearance = verify_line_clearance(model_line_type)
    delta_flange_height = verify_flange_height(model_line_type, object_line, object_vcm)

    return rotation, clearance, delta_flange_height


def make_pointer(case: float, p_parameter: int) -> tuple[int, int]:
    """
    Creates a pointer that selects which of
    the buoys positions is going to be changed
    :param case: this is used as a counter parameter to the pointer
    :param p_parameter: this makes the pointer changes
    :return: pointer and the p_parameter
    """
    if case == 1:
        pointer = p_parameter
    else:
        if p_parameter != case - 1:
            pointer = p_parameter
            p_parameter += 1
        else:
            p_parameter = 0
            pointer = p_parameter
    return pointer, p_parameter


def change_buoy_position(new_positions: list, line_model: OrcFxAPI.OrcaFlexObject,
                         number_attachments: int, model_buoys_position: list, pointer: int) -> None:
    """

    :param pointer:
    :param new_positions:
    :param line_model:
    :param number_attachments:
    :param model_buoys_position:
    :return:
    """
    print(f"changing buoys position,\n"
          f"from {model_buoys_position[pointer]}m to {new_positions[pointer]}m")

    p = 1
    for z in range(0, number_attachments - 1):
        if new_positions[z] == new_positions[pointer]:
            line_model.Attachmentz[p] = new_positions[z]
        p += 1


def changing_buoys(selection: dict, buoy_set: list, rotation: float,
                   buoys_configuration: list,
                   line_model: OrcFxAPI.OrcaFlexObject, vessel: str) -> None:
    """
    With this method we can change the buoy_set
    :param selection: actual selection of buoys
    :param buoy_set: vessel's available buoys
    :param rotation: actual vcm's rotation
    :param buoys_configuration: RL's buoy configuration
    :param line_model: orcaflex's line
    :param vessel: vessel for operation
    :return:
    """

    # AJUSTES --------------------------------------------------

    # 1. Possibilitar aumento de empuxo individual entre 2 ou mais pontos
    # 2. Limitar aumento de empuxo a 2 Tf

    print(f"\nChanging buoys,\n"
          f"from {list(selection.keys())}: {list(selection.values())}")
    teta = 100
    combination_buoys = buoy_combination(buoy_set)
    buoyancy_config = []
    if rotation > 0:
        for buoy in range(len(buoys_configuration[1])):
            buoyancy_config.append(buoys_configuration[1][buoy] + teta)
    else:
        for buoy in range(len(buoys_configuration[1])):
            buoyancy_config.append(buoys_configuration[1][buoy] - teta)
    buoys_configuration = [buoys_configuration[0], buoyancy_config]
    selection = buoyancy(buoys_configuration, combination_buoys)
    print(f"to {list(selection.keys())}: {list(selection.values())}")

    treated_buoys = buoyancy_treatment(buoys_configuration, selection)
    num_buoys = number_buoys(treated_buoys)
    input_buoyancy(line_model, num_buoys, treated_buoys, vessel)


def define_delta_line(clearance: float) -> float:
    """
    Define how much to pay or to retrieve of the line
    :param clearance: line's clearance to the seabed
    :return: delta length
    """
    delta = abs(clearance - .5)
    return delta


def payout_line(line_model: OrcFxAPI.OrcaFlexObject, delta: float) -> None:
    """
    Fine-tuning control - line's payout/retrieve
    :param delta: line's clearance, in the model
    :param line_model: model's line
    """
    print(f"\nPaying out {delta}m from the line,\n"
          f"from {line_model.Length[0]} to {line_model.Length[0] + delta}")
    line_model.Length[0] += delta


def retrieve_line(line_model: OrcFxAPI.OrcaFlexObject, delta: float) -> None:
    """
    Fine-tuning control - line's payout/retrieve
    :param delta: line's clearance, in the model
    :param line_model: model's line
    """
    print(f"\nRetrieving {delta}m from the line,\n"
          f"from {line_model.Length[0]} to {line_model.Length[0] - delta}")
    line_model.Length[0] -= delta


def flange_height_correction(winch: OrcFxAPI.OrcaFlexObject,
                             delta: float) -> None:
    """
    Correct the flange height
    :param winch: winch model
    :param delta: pay_out / retrieve winch
    :return:
    """
    winch_length = winch.StageValue[0]
    winch.StageValue[0] = winch_length + delta
