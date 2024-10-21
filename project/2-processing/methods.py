"""
Pré-processing of the data
before using it to build the OrcaFlex model
"""

from numpy import sqrt
from numpy import pi
from math import pow
from extract import json_data


def line_d_out(w_1, w_2):
    """
    Calculates the flexible line's outside diameter
    :param w_1: wt_air_line
    :param w_2: air_filled_sw_line
    :return: flexible line's outside diameter
    """
    # weight difference (water / air) = wd
    wd = w_1 / 1_000 - w_2 / 1_000
    # seawater density = sd [T/m³]
    sd = 1.025
    return round(float(sqrt(4 / (pi * sd) * wd)), 4)


def line_d_int(w_2, w_3):
    """
    Calculates the flexible line's inner diameter
    :param w_2: air_filled_sw_line
    :param w_3: sw_filled_sw_line
    :return: flexible line's interior diameter
    """
    # filled weight difference (water / air) = fwd
    fwd = w_3 / 1_000 - w_2 / 1_000
    # seawater density = sd [T/m³]
    sd = 1.025
    return round(float(sqrt(4 / (pi * sd) * fwd)), 4)


def linear_weight(not_filled_weight, element_length):
    """
    Calculates the linear weight,
    in air and in water
    :param not_filled_weight: not filled weight, in air and in water
    :param element_length: element length
    :return: linear weight
    """
    return round(not_filled_weight / element_length, 4)


def accessories_d_out(p_air, p_water, accessory_d_int, element_length):
    """
    Calculates the accessory's outside diameter
    :param element_length: accessory length
    :param p_air: not filled linear weight in air
    :param p_water: not filled linear weight in water
    :param accessory_d_int: accessory interior diameter
    :return: outside diameter accessory
    """
    # linear weight in air = lwa
    lwa = linear_weight(p_air, element_length)
    # linear weight in water = lww
    lww = linear_weight(p_water, element_length)
    # seawater density = sd [T/m³]
    sd = 1.025
    # inner diameter square = ids
    ids = pow(accessory_d_int / 1_000, 2)
    return round(float(sqrt((4 / pi / sd) * (lwa - lww) + ids)), 4)


def bending_stiffness(material, d_out, d_int):
    """
    Calculates accessory's bending stiffness
    :param material: accessory's material
    :param d_out: accessory's outside diameter
    :param d_int: accessory's interior diameter
    :return: Bending stiffness
    """
    # thickness raised difference = trd
    trd = pow(d_out / 1_000, 4) - pow(d_int / 1_000, 4)
    # young_module = ei
    ei = young_module(material)
    return round(ei * pi / 64 * trd, 4)


def axial_stiffness(material, d_out, d_int):
    """
    Calculates accessory's axial stiffness
    :param material: accessory's material
    :param d_out: accessory's outside diameter
    :param d_int: accessory's interior diameter
    :return: Axial stiffness
    """
    # thickness raised difference = trd
    trd = pow(d_out / 1_000, 2) - pow(d_int / 1_000, 2)
    # young_module = ei
    ei = young_module(material)
    return round((ei * pi / 4) * trd, 4)


def torsional_stiffness(material, d_out, d_int, poisson=.3):
    """
    Calculates accessory's torsional stiffness
    :param material: accessory's material
    :param d_out: accessory's outside diameter
    :param d_int: accessory's interior diameter
    :param poisson: poisson ratio
    :return: Torsional Stiffness
    """
    # thickness raised difference = trd
    trd = pow(d_out / 1_000, 4) - pow(d_int / 1_000, 4)
    # torsional young module = gi
    gi = young_module(material) / (2 * (1 + poisson))
    return round((gi * pi / 32) * trd, 4)


def bend_moment_limit(material, d_out, d_int):
    """
    Calculates the stiffness curve's bend moment limit for the bend restrictor
    :param material: accessory's material
    :param d_out: accessory's outside diameter
    :param d_int: accessory's interior diameter
    :return: bend moment limit
    """
    return round(bending_stiffness(material, d_out, d_int) + .01, 4)


def young_module(material):
    """
    Defines the accessory's Young's module
    :param material: steel or polymer
    :return: young's module
    """
    if material == "Polymer":
        return round(7 * 1_000_000, 4)
    else:
        return round(207 * 1_000_000, 4)


def cg_olhal_flange(cote_1, cote_2):
    """
    Calculates the VCM's points
    :param cote_1: some VCM's point
    :param cote_2: another some VCM's pont
    :return: main VCM's point
    """
    return round(cote_1 / 1_000 + cote_2 / 1_000, 4)


dict_line = json_data[0]
dict_line["outside_diameter_line"] = line_d_out(dict_line["wt_air_line"], dict_line["air_filled_sw_line"])
dict_line["interior_diameter_line"] = line_d_int(dict_line["air_filled_sw_line"], dict_line["sw_filled_sw_line"])

list_curvature_bend_moment_line = json_data[1]

dict_bend_restrictor = json_data[2]
if len(dict_bend_restrictor) > 15:  # zona rígida (vertebra polimérica)
    dict_bend_restrictor["rz_linear_weight_in_air"] = linear_weight(dict_bend_restrictor["rz_wt_air_bend_restrictor"], dict_bend_restrictor["rz_length_bend_restrictor"])
    dict_bend_restrictor["rz_linear_weight_in_water"] = linear_weight(dict_bend_restrictor["rz_wt_sw_bend_restrictor"], dict_bend_restrictor["rz_length_bend_restrictor"])
    dict_bend_restrictor["rz_outside_diameter"] = accessories_d_out(dict_bend_restrictor["rz_wt_air_bend_restrictor"], dict_bend_restrictor["rz_wt_sw_bend_restrictor"], dict_bend_restrictor["rz_id_bend_restrictor"], dict_bend_restrictor["rz_length_bend_restrictor"])
    dict_bend_restrictor["rz_bending_stiffness_bend_restrictor"] = (bending_stiffness("Steel", dict_bend_restrictor["rz_od_bend_restrictor"], dict_bend_restrictor["rz_id_bend_restrictor"]))
    dict_bend_restrictor["rz_axial_stiffness_bend_restrictor"] = (axial_stiffness("Steel", dict_bend_restrictor["rz_od_bend_restrictor"], dict_bend_restrictor["rz_id_bend_restrictor"]))
    dict_bend_restrictor["rz_torsional_stiffness_bend_restrictor"] = (torsional_stiffness("Steel", dict_bend_restrictor["rz_od_bend_restrictor"], dict_bend_restrictor["rz_id_bend_restrictor"]))

dict_bend_restrictor["linear_weight_in_air_bend_restrictor"] = linear_weight(dict_bend_restrictor["wt_air_bend_restrictor"], dict_bend_restrictor["length_bend_restrictor"])
dict_bend_restrictor["linear_weight_in_water_bend_restrictor"] = linear_weight(dict_bend_restrictor["wt_sw_bend_restrictor"], dict_bend_restrictor["length_bend_restrictor"])
dict_bend_restrictor["outside_diameter_bend_restrictor"] = accessories_d_out(dict_bend_restrictor["wt_air_bend_restrictor"], dict_bend_restrictor["wt_sw_bend_restrictor"], dict_bend_restrictor["id_bend_restrictor"], dict_bend_restrictor["length_bend_restrictor"])
dict_bend_restrictor["bending_stiffness_bend_restrictor"] = (bending_stiffness(dict_bend_restrictor["type_bend_restrictor"], dict_bend_restrictor["od_bend_restrictor"], dict_bend_restrictor["id_bend_restrictor"]))  # erro
dict_bend_restrictor["axial_stiffness_bend_restrictor"] = 10.0
dict_bend_restrictor["torsional_stiffness_bend_restrictor"] = 10.0

list_curvature_bend_moment_bend_restrictor = [
    [
        .0,
        round(1 / dict_bend_restrictor["locking_mbr_bend_restrictor"], 4),
        round(1 + 1 / dict_bend_restrictor["locking_mbr_bend_restrictor"], 4)
    ],
    [
        .0,
        .01,
        bend_moment_limit(dict_bend_restrictor["type_bend_restrictor"], dict_bend_restrictor["od_bend_restrictor"], dict_bend_restrictor["id_bend_restrictor"])
    ]
]

dict_end_fitting = json_data[3]
dict_end_fitting["linear_weight_in_air_end_fitting"] = linear_weight(dict_end_fitting["wt_air_end_fitting"], dict_end_fitting["length_end_fitting"])
dict_end_fitting["linear_weight_in_water_end_fitting"] = linear_weight(dict_end_fitting["wt_sw_end_fitting"], dict_end_fitting["length_end_fitting"])
dict_end_fitting["outside_diameter_end_fitting"] = accessories_d_out(dict_end_fitting["wt_air_end_fitting"], dict_end_fitting["wt_sw_end_fitting"], dict_end_fitting["id_end_fitting"], dict_end_fitting["length_end_fitting"])
dict_end_fitting["bending_stiffness_end_fitting"] = bending_stiffness("Steel", dict_end_fitting["od_end_fitting"], dict_end_fitting["id_end_fitting"])
dict_end_fitting["axial_stiffness_end_fitting"] = axial_stiffness("Steel", dict_end_fitting["od_end_fitting"], dict_end_fitting["id_end_fitting"])
dict_end_fitting["torsional_stiffness_end_fitting"] = torsional_stiffness("Steel", dict_end_fitting["od_end_fitting"], dict_end_fitting["id_end_fitting"])

dict_vcm = json_data[5]
dict_vcm["cg_az"] = cg_olhal_flange(dict_vcm["f_vcm"], - dict_vcm["d_vcm"])
dict_vcm["cg_bx"] = cg_olhal_flange(dict_vcm["g_vcm"], - dict_vcm["e_vcm"])
dict_vcm["olhal_cz"] = cg_olhal_flange(dict_vcm["f_vcm"], dict_vcm["b_vcm"])
dict_vcm["olhal_dx"] = cg_olhal_flange(dict_vcm["g_vcm"], - dict_vcm["c_vcm"])
dict_vcm["flange_ez"] = cg_olhal_flange(.0, dict_vcm["f_vcm"])
dict_vcm["flange_fx"] = cg_olhal_flange(.0, dict_vcm["g_vcm"])

winch_length = dict_line["water_depth"] - ((dict_vcm["b_vcm"] + dict_vcm["a_vcm"]) / 1_000)

list_bathymetric = json_data[6]
depth = [(dict_line["water_depth"] + (list_bathymetric[1][i] - dict_vcm["a_vcm"]) / 1_000)
         for i in range(len(list_bathymetric[0]))]
list_bathymetric.append(depth)

flange_height = (dict_vcm["a_vcm"] - dict_vcm["f_vcm"]) / 1_000
height_to_seabed = dict_line["water_depth"] - flange_height

# (bend restrictor + end fitting) length = bel
bel = (dict_bend_restrictor["length_bend_restrictor"] + dict_end_fitting["length_end_fitting"])
length = 160 + 100 + 40 + 10 + bel / 1_000

dict_flange = json_data[4]

if dict_flange["ident_flange"] != "":
    dict_flange["linear_weight_in_air_flange"] = linear_weight(dict_flange["wt_air_flange"], dict_flange["length_flange"])
    dict_flange["linear_weight_in_water_flange"] = linear_weight(dict_flange["wt_sw_flange"], dict_flange["length_flange"])
    dict_flange["outside_diameter_flange"] = accessories_d_out(dict_flange["wt_air_flange"], dict_flange["wt_sw_flange"], dict_flange["id_flange"], dict_flange["length_flange"])
    dict_flange["bending_stiffness_flange"] = bending_stiffness("Steel", dict_flange["od_flange"], dict_flange["id_flange"])
    dict_flange["axial_stiffness_flange"] = axial_stiffness("Steel", dict_flange["od_flange"], dict_flange["id_flange"])
    dict_flange["torsional_stiffness_flange"] = torsional_stiffness("Steel", dict_flange["od_flange"], dict_flange["id_flange"])

    length += dict_flange["length_flange"] / 1_000

    new_combined_data = (
        dict_line, list_curvature_bend_moment_line, dict_bend_restrictor,
        list_curvature_bend_moment_bend_restrictor, dict_end_fitting,
        dict_flange, length, dict_vcm, winch_length, list_bathymetric,
        height_to_seabed, json_data[7], json_data[8], json_data[9],
        json_data[10], json_data[11]
    )
else:
    new_combined_data = (
        dict_line, list_curvature_bend_moment_line, dict_bend_restrictor,
        list_curvature_bend_moment_bend_restrictor, dict_end_fitting, length,
        dict_vcm, winch_length, list_bathymetric, height_to_seabed, json_data[7],
        json_data[8], json_data[9], json_data[10], json_data[11]
    )
