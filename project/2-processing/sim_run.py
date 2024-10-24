"""
Simulation methods for the automation.
"""

import OrcFxAPI

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
    n_run += 1
    model.SaveSimulation(rt_number + "\\" + str(n_run) + "-" + rt_number +
                         "_Static.sim")
    print(f"\nRunning time {n_run}")


def user_specified(model: OrcFxAPI.Model, rt_number: str) -> None:
    """
    Put the line's static position configuration in user_specified method
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
    buoys = [str(b_set[1][i])
             for i in range(len(b_set[0]))
             for _ in range(b_set[0][i])]
    one_buoy = {buoy: float(buoy) for buoy in buoys}
    two_buoys = {f"{buoy1}+{buoy2}": one_buoy[buoy1] + one_buoy[buoy2]
                 for i, buoy1 in enumerate(buoys)
                 for j, buoy2 in enumerate(buoys)
                 if i < j}
    three_buoys = {f"{buoy1}+{buoy2}+{buoy3}": one_buoy[buoy1] + one_buoy[
        buoy2] + one_buoy[buoy3]
                   for i, buoy1 in enumerate(buoys)
                   for j, buoy2 in enumerate(buoys)
                   for k, buoy3 in enumerate(buoys)
                   if i < j < k}
    combination = {**one_buoy, **two_buoys, **three_buoys}
    combination_buoys = {key: value
                         for key, value in combination.items() if value < 2000}
    combination_buoys = dict(
        sorted(combination_buoys.items(), key=lambda item: item[1],
               reverse=False))
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


def number_buoys(treated_buoys: dict) -> float:
    """
    Gives the number of attachments buoys
    :param treated_buoys: set of selected buoys
    :return: number of selected buoys
    """
    packs = [buoy[i]
             for buoy in treated_buoys.values()
             for i in range(len(buoy))]
    return len(packs)


def input_buoyancy(line_model: OrcFxAPI.OrcaFlexObject, num_buoys: float,
                   treated_buoys: dict, vessel: str) -> None:
    """
    Add the first model's buoyancy configuration
    :param vessel: operation's vessel
    :param num_buoys: attachments quantity
    :param treated_buoys: buoy selection to the Orca model
    :param line_model: line object modeled in OrcaFlex
    :return: nothing
    """
    line_model.NumberOfAttachments = num_buoys + 1
    ibs_key = tuple(treated_buoys.keys())
    ibs_val = tuple(treated_buoys.values())
    ibs_2 = []
    for i in range(len(ibs_val)):
        for j in range(len(ibs_val[i])):
            ibs_2.append(ibs_val[i][j])
    b = 1
    for m in ibs_2:
        buoy = vessel + "_" + str(m)
        line_model.AttachmentType[b] = buoy
        b += 1
    ibs_1 = []
    for z in range(len(ibs_val)):
        for _ in range(len(ibs_val[z])):
            ibs_1.append(ibs_key[z])
    p = 1
    for n in ibs_1:
        line_model.Attachmentz[p] = n
        p += 1


def loop_input_buoyancy(buoys_configuration: list,
                        line_model: OrcFxAPI.OrcaFlexObject,
                        model: OrcFxAPI.Model, k_parameter: float,
                        comb_buoys: dict, vessel: str, rt_number: str):
    """
    Creates a starting loop that grows gradually the buoyancy intensity for
    avoid the run_break that occurs when we sharply change the buoyancy.
    :param buoys_configuration: RL's buoy configuration
    :param line_model: line object modeled in OrcaFlex
    :param model: OrcaFlex model
    :param k_parameter: parameter that multiplies the buoyancy
    :param comb_buoys: actual buoy combination, in the model
    :param vessel: operation's vessel
    :param rt_number: RT indentification
    :return:
    """
    buoys_configuration_copy = [
        buoys_configuration[0],
        [round(k_parameter * x / 4, 0) for x in buoys_configuration[1]]
    ]
    selection = buoyancy(buoys_configuration_copy, comb_buoys)
    treated_buoys = buoyancy_treatment(buoys_configuration_copy, selection)
    num_buoys = number_buoys(treated_buoys)
    input_buoyancy(line_model, num_buoys, treated_buoys, vessel)

    run_static_simulation(model, rt_number)
    user_specified(model, rt_number)

    if buoys_configuration_copy != buoys_configuration:
        loop_input_buoyancy(buoys_configuration, line_model, model,
                            k_parameter + 1, comb_buoys, vessel, rt_number)


def insert_bend_restrictor(line_model: OrcFxAPI.OrcaFlexObject,
                           b_restrict: OrcFxAPI.OrcaFlexObject,
                           flange: dict, end_fitting: dict) -> None:
    """
    Inserts bend_restrictor back to the line
    :param end_fitting: end_fitting model
    :param flange: flange model
    :param b_restrict: bend_restrictor's line_type
    :param line_model: line's line_type
    :return: nothing
    """
    line_model.NumberOfAttachments = 1
    line_model.AttachmentType[0] = b_restrict.name
    if flange["ident_flange"] == "":
        line_model.Attachmentz[0] = end_fitting["length_end_fitting"] / 1000
    else:
        line_model.Attachmentz[0] = (end_fitting["length_end_fitting"] +
                                     flange["length_flange"]) / 1000
    line_model.AttachmentzRelativeTo[0] = "End B"


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


def payout_retrieve_line(line_model: OrcFxAPI.OrcaFlexObject,
                         what: bool, clearance: float) -> None:
    """
    Fine-tuning control - line's payout/retrieve
    :param clearance: line's clearance, in the model
    :param what: boolean value to select payout or retrieve
    :param line_model: model's line
    """
    delta = .25
    if clearance >= 1.2:
        delta = 1
    elif 1.2 > clearance >= .85:
        delta = .5
    elif .85 > clearance >= .6:
        delta = .25
    elif .5 >= clearance > .25:
        delta = .25
    elif .25 >= clearance:
        delta = .5

    if what:
        print(f"\nPaying out {delta}m from the line,\n"
              f"from {line_model.Length[0]} to {line_model.Length[0] + delta}")
        line_model.Length[0] += delta
    else:
        print(f"\nRetrieving {delta}m from the line,\n"
              f"from {line_model.Length[0]} to {line_model.Length[0] - delta}")
        line_model.Length[0] -= delta


def change_buoy_position(line_model: OrcFxAPI.OrcaFlexObject,
                         what: bool, rotation: float,
                         buoy_config: list) -> list:
    """
    Changes the buoys position
    :param buoy_config: RL's buoy configuration
    :param rotation: vcm's rotation, in the orcaflex
    :param what: boolean value to select + or - distance
    :param line_model: OrcaFlex's line
    :return: None
    """

    # AJUSTES --------------------------------------------------

    # 1. Possibilitar mudança de posição individual entre 2 ou mais pontos

    number = line_model.NumberOfAttachments
    positions = []
    k = 1
    for i in range(1, number):
        positions.append(line_model.Attachmentz[k])
        k += 1
    new_positions = []

    delta_x = .5
    if rotation >= 2:
        delta_x = positions[0] - 3
    elif 2 > rotation >= 1:
        delta_x = positions[0] - 4
    elif 1 > rotation >= -1:
        delta_x = .5
    elif -1 > rotation >= -2:
        delta_x = 5 - positions[0]
    elif -2 > rotation:
        delta_x = 4 - positions[0]

    if what:
        for j in positions:
            new_positions.append(j - delta_x)
    else:
        for j in positions:
            new_positions.append(j + delta_x)
    p = 1
    print(f"changing buoys position,\n"
          f"from {positions}m to {new_positions}m")
    for z in range(0, number - 1):
        line_model.Attachmentz[p] = new_positions[z]
        p += 1

    new_buoy_config = [
        list(set(new_positions)),
        buoy_config[1]
    ]
    print(new_buoy_config)
    return new_buoy_config


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


def loop_initialization(line_model: OrcFxAPI.OrcaFlexObject,
                        vcm: OrcFxAPI.OrcaFlexObject,
                        model: OrcFxAPI.Model, rotation: float,
                        clearance: float, buoy_set: list,
                        buoys_configuration: list, vessel: str,
                        rt_number: str, what: bool, selection: dict) -> str:
    """
    Function that controls the automation
    :param selection: present selection of buoys
    :param clearance: line's clearance
    :param rotation: vcm's rotation
    :param rt_number: RT's number
    :param vessel: vessel
    :param what: control for change buoys
    :param buoys_configuration: RL's buoy configuration
    :param buoy_set: vessel's buoys
    :param line_model: orcaflex's line
    :param vcm: orcaflex's vcm
    :param model: orcaflex's model
    :return: convergence sinal
    """

    global n_run
    if n_run == 100:
        return f"Sorry, was not possible to converge in {n_run} tentatives."

    if what:

        user_specified(model, rt_number)

        changing_buoys(selection, buoy_set, rotation, buoys_configuration,
                       line_model, vessel)

        run_static_simulation(model, rt_number)

        rotation = verify_vcm_rotation(vcm)
        clearance = verify_line_clearance(line_model)

        loop_initialization(line_model, vcm, model, rotation, clearance,
                            buoy_set, buoys_configuration, vessel,
                            rt_number, False, selection)

    if rotation > .5:
        if line_model.Attachmentz[1] == 3:
            loop_initialization(line_model, vcm, model, rotation,
                                clearance, buoy_set, buoys_configuration,
                                vessel, rt_number, True, selection)

        user_specified(model, rt_number)
        buoys_configuration = change_buoy_position(line_model, True, rotation,
                                                   buoys_configuration)
        run_static_simulation(model, rt_number)

        rotation = verify_vcm_rotation(vcm)
        clearance = verify_line_clearance(line_model)

        loop_initialization(line_model, vcm, model, rotation, clearance,
                            buoy_set, buoys_configuration, vessel,
                            rt_number, False, selection)

    elif rotation < -.5:
        if line_model.Attachmentz[1] == 5:
            loop_initialization(line_model, vcm, model, rotation,
                                clearance, buoy_set, buoys_configuration,
                                vessel, rt_number, True, selection)

        user_specified(model, rt_number)
        buoys_configuration = change_buoy_position(line_model, False, rotation,
                                                   buoys_configuration)
        run_static_simulation(model, rt_number)

        rotation = verify_vcm_rotation(vcm)
        clearance = verify_line_clearance(line_model)

        loop_initialization(line_model, vcm, model, rotation, clearance,
                            buoy_set, buoys_configuration, vessel,
                            rt_number, False, selection)

    if clearance > .6:

        user_specified(model, rt_number)
        payout_retrieve_line(line_model, True, clearance)
        run_static_simulation(model, rt_number)

        rotation = verify_vcm_rotation(vcm)
        clearance = verify_line_clearance(line_model)

        loop_initialization(line_model, vcm, model, rotation, clearance,
                            buoy_set, buoys_configuration, vessel,
                            rt_number, False, selection)

    elif clearance < .5:

        user_specified(model, rt_number)
        payout_retrieve_line(line_model, False, clearance)
        run_static_simulation(model, rt_number)

        rotation = verify_vcm_rotation(vcm)
        clearance = verify_line_clearance(line_model)

        loop_initialization(line_model, vcm, model, rotation, clearance,
                            buoy_set, buoys_configuration, vessel,
                            rt_number, False, selection)

    return "\nLooping's end."
