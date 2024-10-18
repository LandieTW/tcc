"""
Simulation methods for the automation
"""

import OrcFxAPI

n_run = 0

"""
JSON_DATA

buoy_set
[
    [1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1], 
    [1416, 1376, 1345, 1323, 1320, 871, 741, 660, 
    647, 381, 377, 155, 104, 101, 100]
    ]

buoys_configuration
[
    [5.0, 9.0], 
    [500.0, 300.0]
    ]
"""

# tendo o buoy_set, eu preciso criar todas as possíveis combinações de empuxo


def buoy_combination(b_set: list) -> dict:
    """
    Make combinations with 1 to 3 buoys, below 2 tf of buoyancy
    :param b_set: vessel's buoy set
    :return: possible combinations with up to 3 buoys
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


"""
BUOY_COMBINATION

combination_buoys
{'100': 100.0, '101': 101.0, '104': 104.0, '155': 155.0, '101+100': 201.0, 
'104+100': 204.0, '104+101': 205.0, '155+100': 255.0, '155+101': 256.0, 
'155+104': 259.0, '104+101+100': 305.0, '155+101+100': 356.0, 
'155+104+100': 359.0, '155+104+101': 360.0, '377': 377.0, '381': 381.0, 
'377+100': 477.0, '377+101': 478.0, '381+100': 481.0, '377+104': 481.0, 
'381+101': 482.0, '381+104': 485.0, '377+155': 532.0, '381+155': 536.0, 
'377+101+100': 578.0, '377+104+100': 581.0, '381+101+100': 582.0, 
'377+104+101': 582.0, '381+104+100': 585.0, '381+104+101': 586.0, 
'377+155+100': 632.0, '377+155+101': 633.0, '381+155+100': 636.0, 
'377+155+104': 636.0, '381+155+101': 637.0, '381+155+104': 640.0, '647': 647.0, 
'660': 660.0, '741': 741.0, '647+100': 747.0, '647+101': 748.0, 
'647+104': 751.0, '381+377': 758.0, '660+100': 760.0, '660+101': 761.0, 
'660+104': 764.0, '647+155': 802.0, '660+155': 815.0, '741+100': 841.0, 
'741+101': 842.0, '741+104': 845.0, '647+101+100': 848.0, '647+104+100': 851.0, 
'647+104+101': 852.0, '381+377+100': 858.0, '381+377+101': 859.0, 
'660+101+100': 861.0, '381+377+104': 862.0, '660+104+100': 864.0, 
'660+104+101': 865.0, '871': 871.0, '741+155': 896.0, '647+155+100': 902.0, 
'647+155+101': 903.0, '647+155+104': 906.0, '381+377+155': 913.0, 
'660+155+100': 915.0, '660+155+101': 916.0, '660+155+104': 919.0, 
'741+101+100': 942.0, '741+104+100': 945.0, '741+104+101': 946.0, 
'871+100': 971.0, '871+101': 972.0, '871+104': 975.0, '741+155+100': 996.0, 
'741+155+101': 997.0, '741+155+104': 1000.0, '647+377': 1024.0, 
'871+155': 1026.0, '647+381': 1028.0, '660+377': 1037.0, '660+381': 1041.0, 
'871+101+100': 1072.0, '871+104+100': 1075.0, '871+104+101': 1076.0, 
'741+377': 1118.0, '741+381': 1122.0, '647+377+100': 1124.0, 
'647+377+101': 1125.0, '871+155+100': 1126.0, '871+155+101': 1127.0, 
'647+381+100': 1128.0, '647+377+104': 1128.0, '647+381+101': 1129.0, 
'871+155+104': 1130.0, '647+381+104': 1132.0, '660+377+100': 1137.0, 
'660+377+101': 1138.0, '660+381+100': 1141.0, '660+377+104': 1141.0, 
'660+381+101': 1142.0, '660+381+104': 1145.0, '647+377+155': 1179.0, 
'647+381+155': 1183.0, '660+377+155': 1192.0, '660+381+155': 1196.0, 
'741+377+100': 1218.0, '741+377+101': 1219.0, '741+381+100': 1222.0, 
'741+377+104': 1222.0, '741+381+101': 1223.0, '741+381+104': 1226.0, 
'871+377': 1248.0, '871+381': 1252.0, '741+377+155': 1273.0, 
'741+381+155': 1277.0, '660+647': 1307.0, '1320': 1320.0, '1323': 1323.0, 
'1345': 1345.0, '871+377+100': 1348.0, '871+377+101': 1349.0, 
'871+381+100': 1352.0, '871+377+104': 1352.0, '871+381+101': 1353.0, 
'871+381+104': 1356.0, '1376': 1376.0, '741+647': 1388.0, '741+660': 1401.0, 
'871+377+155': 1403.0, '647+381+377': 1405.0, '871+381+155': 1407.0, 
'660+647+100': 1407.0, '660+647+101': 1408.0, '660+647+104': 1411.0, 
'1416': 1416.0, '660+381+377': 1418.0, '1320+100': 1420.0, '1320+101': 1421.0, 
'1323+100': 1423.0, '1323+101': 1424.0, '1320+104': 1424.0, '1323+104': 1427.0, 
'1345+100': 1445.0, '1345+101': 1446.0, '1345+104': 1449.0, 
'660+647+155': 1462.0, '1320+155': 1475.0, '1376+100': 1476.0, 
'1376+101': 1477.0, '1323+155': 1478.0, '1376+104': 1480.0, '741+741': 1482.0, 
'741+647+100': 1488.0, '741+647+101': 1489.0, '741+647+104': 1492.0, 
'741+381+377': 1499.0, '1345+155': 1500.0, '741+660+100': 1501.0, 
'741+660+101': 1502.0, '741+660+104': 1505.0, '1416+100': 1516.0, 
'1416+101': 1517.0, '871+647': 1518.0, '1416+104': 1520.0, 
'1320+101+100': 1521.0, '1323+101+100': 1524.0, '1320+104+100': 1524.0, 
'1320+104+101': 1525.0, '1323+104+100': 1527.0, '1323+104+101': 1528.0, 
'1376+155': 1531.0, '871+660': 1531.0, '741+647+155': 1543.0, 
'1345+101+100': 1546.0, '1345+104+100': 1549.0, '1345+104+101': 1550.0, 
'741+660+155': 1556.0, '1416+155': 1571.0, '1320+155+100': 1575.0, 
'1320+155+101': 1576.0, '1376+101+100': 1577.0, '1323+155+100': 1578.0, 
'1323+155+101': 1579.0, '1320+155+104': 1579.0, '1376+104+100': 1580.0, 
'1376+104+101': 1581.0, '1323+155+104': 1582.0, '741+741+100': 1582.0, 
'741+741+101': 1583.0, '741+741+104': 1586.0, '1345+155+100': 1600.0, 
'1345+155+101': 1601.0, '1345+155+104': 1604.0, '871+741': 1612.0, 
'1416+101+100': 1617.0, '871+647+100': 1618.0, '871+647+101': 1619.0, 
'1416+104+100': 1620.0, '1416+104+101': 1621.0, '871+647+104': 1622.0, 
'871+381+377': 1629.0, '1376+155+100': 1631.0, '871+660+100': 1631.0, 
'1376+155+101': 1632.0, '871+660+101': 1632.0, '1376+155+104': 1635.0, 
'871+660+104': 1635.0, '741+741+155': 1637.0, '1416+155+100': 1671.0, 
'1416+155+101': 1672.0, '871+647+155': 1673.0, '1416+155+104': 1675.0, 
'660+647+377': 1684.0, '871+660+155': 1686.0, '660+647+381': 1688.0, 
'1320+377': 1697.0, '1323+377': 1700.0, '1320+381': 1701.0, '1323+381': 1704.0, 
'871+741+100': 1712.0, '871+741+101': 1713.0, '871+741+104': 1716.0, 
'1345+377': 1722.0, '1345+381': 1726.0, '1376+377': 1753.0, '1376+381': 1757.0, 
'741+647+377': 1765.0, '871+741+155': 1767.0, '741+647+381': 1769.0, 
'741+660+377': 1778.0, '741+660+381': 1782.0, '1416+377': 1793.0, 
'1416+381': 1797.0, '1320+377+100': 1797.0, '1320+377+101': 1798.0, 
'1323+377+100': 1800.0, '1323+377+101': 1801.0, '1320+381+100': 1801.0, 
'1320+377+104': 1801.0, '1320+381+101': 1802.0, '1323+381+100': 1804.0, 
'1323+377+104': 1804.0, '1323+381+101': 1805.0, '1320+381+104': 1805.0, 
'1323+381+104': 1808.0, '1345+377+100': 1822.0, '1345+377+101': 1823.0, 
'1345+381+100': 1826.0, '1345+377+104': 1826.0, '1345+381+101': 1827.0, 
'1345+381+104': 1830.0, '1320+377+155': 1852.0, '1376+377+100': 1853.0, 
'1376+377+101': 1854.0, '1323+377+155': 1855.0, '1320+381+155': 1856.0, 
'1376+381+100': 1857.0, '1376+377+104': 1857.0, '1376+381+101': 1858.0, 
'1323+381+155': 1859.0, '741+741+377': 1859.0, '1376+381+104': 1861.0, 
'741+741+381': 1863.0, '1345+377+155': 1877.0, '1345+381+155': 1881.0, 
'1416+377+100': 1893.0, '1416+377+101': 1894.0, '871+647+377': 1895.0, 
'1416+381+100': 1897.0, '1416+377+104': 1897.0, '1416+381+101': 1898.0, 
'871+647+381': 1899.0, '1416+381+104': 1901.0, '1376+377+155': 1908.0, 
'871+660+377': 1908.0, '1376+381+155': 1912.0, '871+660+381': 1912.0, 
'1416+377+155': 1948.0, '1416+381+155': 1952.0, '1320+647': 1967.0, 
'1323+647': 1970.0, '1320+660': 1980.0, '1323+660': 1983.0, 
'871+741+377': 1989.0, '1345+647': 1992.0, '871+741+381': 1993.0}
"""


# depois, eu preciso escolher dentre todas as possibilidades de combinações a
# que melhor se assemelha a buoy_configuration

def buoyancy(buoys_config: list, combination_buoys: dict, *what: bool) -> dict:
    """
    Gives the best combination of buoys based on the initial suggestion
    :param what: control for + or - buoyancy
    :param combination_buoys: new buoy_combination
    :param buoys_config: initial buoyancy suggestion
    :return: better available combination, based on the initial suggestion
    """
    selection = {}
    for k in range(len(buoys_config[1])):
        comb_keys = list(combination_buoys.keys())
        j = 0
        while abs(combination_buoys[comb_keys[j]] - buoys_config[1][k]) > \
                abs(combination_buoys[comb_keys[j + 1]] - buoys_config[1][k]):
            j += 1
        if what:
            key = comb_keys[j + 1]
        else:
            key = comb_keys[j]
        value = combination_buoys[comb_keys[j]]
        selection[key] = value
    print(f"selection: {selection}")
    return selection


"""
BUOYANCY

selection
{'381+100': 481.0, '104+101+100': 305.0}
"""

# Agora que eu tenho as boias que vão para o modelo, preciso ajustar os dados
# para lançar no OrcaFlex


def buoyancy_treatment(buoys_config: list, selection: dict) -> dict:
    """
    It uses initial buoyancy and treats it to return the entry data for
    OrcaFlex, referring the initial buoyancy
    :param selection: selection of buoys to OrcaFlex
    :param buoys_config: initial buoyancy suggestion
    :return: attachments to OrcaFlex
    """
    position = buoys_config[0]
    treated_buoys = {position[i]: list(selection.keys())[i].split("+")
                     for i in range(len(list(selection.keys())))}
    return treated_buoys


"""
BUOYANCY_TREATMENT

treated_buoys
{
    5.0: ['381', '100'], 
    9.0: ['104', '101', '100']
    }
"""

# Agora vou determinar a quantidade de attachments, considerando vértebra e
# boias


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


"""
NUMBER_BUOYS

len_pack
5
"""

# Agora, posso adicionar os attachments no modelo


def input_buoyancy(line_model: OrcFxAPI.OrcaFlexObject, num_buoys: float,
                   treated_buoys: dict, vessel: str) -> None:
    """
    Add the first model's buoyancy configuration
    :param vessel:
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


# ---------------------------------------------------------
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# ---------------------------------------------------------

# função para adicionar a vértebra


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


# função para rodar a simulação estática


def run_static_simulation(model: OrcFxAPI.Model, rt_number: str) -> None:
    """
    Runs and save a static simulation
    :param rt_number:
    :param model: OrcaFlex model
    :return: nothing
    """
    model.CalculateStatics()
    global n_run
    n_run += 1
    model.SaveSimulation(rt_number + "\\" + str(n_run) + "-" + rt_number +
                         "_Static.sim")
    print(f"\nRunning time {n_run}")


# função para setar regra de pesquisa de convergência


def user_specified(model: OrcFxAPI.Model, rt_number: str) -> None:
    """
    Put the line's static position configuration in user_specified method
    :param rt_number:
    :param model: OrcaFlex model
    :return: nothing
    """
    model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)
    model.SaveData(rt_number + "\\" + rt_number + "_Static.dat")


# ---------------------------------------------------------
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# ---------------------------------------------------------

# função para pegar os dados de resultados que balizarão a automação


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
    :return: rotation in y axis
    """
    vcm_rotation = vcm_.StaticResult("Rotation 2")
    print(f"\nRotation: {vcm_rotation}")
    return vcm_rotation


# ---------------------------------------------------------
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# ---------------------------------------------------------

# fazer a função que paga/recolhe a linha


def payout_retrieve_line(line_model: OrcFxAPI.OrcaFlexObject,
                         what: bool) -> None:
    """
    Fine-tuning control - line's payout/retrieve
    :param what: boolean value to select payout or retrieve
    :param line_model: model's line
    """
    delta = .2
    if what:
        print(f"\nPayout line from {line_model.Length[0]} "
              f"to {line_model.Length[0] + delta}")
        line_model.Length[0] += delta
    else:
        print(f"\nRetrieve line from {line_model.Length[0]} "
              f"to {line_model.Length[0] - delta}")
        line_model.Length[0] -= delta


# fazer a função que troca a posição das boias


def change_buoy_position(line_model: OrcFxAPI.OrcaFlexObject,
                         what: bool) -> None:
    """
    Changes the buoys position
    :param what: boolean value to select + or - distance
    :param line_model: OrcaFlex's line
    :return: None
    """
    number = line_model.NumberOfAttachments
    positions = []
    for i in range(1, number):
        positions.append(line_model.Attachmentz[i])

    new_positions = []
    if what:
        for j in positions:
            new_positions.append(j + .5)
    else:
        for j in positions:
            new_positions.append(j - .5)

    for z in range(1, number):
        print(f"changing position from {positions[z]} to {new_positions[z]}")
        line_model.Attachmentz[z] = new_positions[z]


# fazer a função que troca boias


# ---------------------------------------------------------
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# ---------------------------------------------------------

# fazer a função que fica em loop

old_buoys = {}


def loop_initialization(line_model: OrcFxAPI.OrcaFlexObject,
                        vcm: OrcFxAPI.OrcaFlexObject,
                        model: OrcFxAPI.Model, rotation: float,
                        clearance: float, buoy_set: list,
                        buoys_configuration: list, vessel: str,
                        rt_number: str, what: bool, selection: dict) -> str:
    """
    Function control of the automation
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
        return "Sorry, was not possible to converge"

    if what:

        print(f"\nchanging buoys {selection}")
        user_specified(model, rt_number)

        global old_buoys
        old_buoys.update(selection)
        combination_buoys = buoy_combination(buoy_set)
        for key in old_buoys:
            combination_buoys.pop(key, None)

        if rotation > 0:
            print("aumenta o empuxo")
            selection = buoyancy(buoys_configuration, combination_buoys, True)
        else:
            print("reduz o empuxo")
            selection = buoyancy(buoys_configuration, combination_buoys, False)
        print(f"new buoys {selection}")

        treated_buoys = buoyancy_treatment(buoys_configuration, selection)
        num_buoys = number_buoys(treated_buoys)

        input_buoyancy(line_model, num_buoys, treated_buoys, vessel)

        run_static_simulation(model, rt_number)

        rotation = verify_vcm_rotation(vcm)
        clearance = verify_line_clearance(line_model)

        loop_initialization(line_model, vcm, model, rotation, clearance,
                            buoy_set, buoys_configuration, vessel,
                            rt_number, False, selection)

    if rotation > .5 and line_model.Attachmentz[1] == 5:

        loop_initialization(line_model, vcm, model, rotation, clearance,
                            buoy_set, buoys_configuration, vessel,
                            rt_number, True, selection)

    elif rotation < -.5 and line_model.Attachmentz[1] == 3:

        loop_initialization(line_model, vcm, model, rotation, clearance,
                            buoy_set, buoys_configuration, vessel,
                            rt_number, True, selection)

    if .5 > clearance > .6:

        if clearance > .6:

            user_specified(model, rt_number)

            payout_retrieve_line(line_model, True)

            run_static_simulation(model, rt_number)

            rotation = verify_vcm_rotation(vcm)
            clearance = verify_line_clearance(line_model)

            loop_initialization(line_model, vcm, model, rotation, clearance,
                                buoy_set, buoys_configuration, vessel,
                                rt_number, what, selection)

        elif clearance < .5:

            user_specified(model, rt_number)

            payout_retrieve_line(line_model, False)

            run_static_simulation(model, rt_number)

            rotation = verify_vcm_rotation(vcm)
            clearance = verify_line_clearance(line_model)

            loop_initialization(line_model, vcm, model, rotation, clearance,
                                buoy_set, buoys_configuration, vessel,
                                rt_number, what, selection)

    elif -.5 > rotation > .5:
        
        if rotation > 0:

            user_specified(model, rt_number)

            change_buoy_position(line_model, True)

            run_static_simulation(model, rt_number)

            rotation = verify_vcm_rotation(vcm)
            clearance = verify_line_clearance(line_model)

            loop_initialization(line_model, vcm, model, rotation, clearance,
                                buoy_set, buoys_configuration, vessel,
                                rt_number, what, selection)

        else:

            user_specified(model, rt_number)

            change_buoy_position(line_model, False)

            run_static_simulation(model, rt_number)

            rotation = verify_vcm_rotation(vcm)
            clearance = verify_line_clearance(line_model)

            loop_initialization(line_model, vcm, model, rotation, clearance,
                                buoy_set, buoys_configuration, vessel,
                                rt_number, what, selection)

    return "\nLooping's end."
