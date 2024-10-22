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


class Line:
    def __init__(self, name, revision, empty_air_weight, filled_air_weight, empty_water_weight,
                 filled_water_weight, water_depth, contact_diameter, nominal_diameter, mbr_storage,
                 mbr_installation, b_stiffness, t_stiffness, a_stiffness, relative_elongation,
                 s_curve):
        self.__name = name,
        self.__revision = revision,
        self.__eaw = empty_air_weight,
        self.__faw = filled_air_weight,
        self.__eww = empty_water_weight,
        self.__fww = filled_water_weight,
        self.__lda = water_depth,
        self.__cd = contact_diameter,
        self.__nd = nominal_diameter,
        self.__mbr_s = mbr_storage,
        self.__mbr_i = mbr_installation,
        self.__b_stiffness = b_stiffness,
        self.__t_stiffness = t_stiffness,
        self.__a_stiffness = a_stiffness,
        self.__r_elongation = relative_elongation,
        self.__od = line_d_out(empty_air_weight, empty_water_weight),
        self.__id = line_d_int(empty_water_weight, filled_water_weight),
        self.__curvature = s_curve[0],
        self.__b_moment = [b_moment / 1_000
                           for b_moment in s_curve[1]]


class BendRestrictor:
    def __init__(self, name, revision, material, length_mm, air_weight, water_weight,
                 outside_diameter, inner_diameter, contact_diameter, mbr, bend_moment, shear_force,
                 s_curve):
        self.__name = name,
        self.__revision = revision,
        self.__material = material,
        self.__length = length_mm,
        self.__aw = air_weight,
        self.__ww = water_weight,
        self.__od = outside_diameter,
        self.__id = inner_diameter,
        self.__cd = contact_diameter,
        self.__mbr = mbr,
        self.__bm = bend_moment,
        self.__sf = shear_force,
        self.__lwa = linear_weight(air_weight, length),
        self.__lww = linear_weight(water_weight, length),
        self.__out_d = accessories_d_out(air_weight, water_weight, inner_diameter, length),
        self.__b_stiffness = bending_stiffness(material, outside_diameter, inner_diameter),
        self.__t_stiffness = 10.0,
        self.__a_stiffness = 10.0,
        self.__curvature = s_curve[0],
        self.__b_moment = s_curve[1]


class Accessory:
    def __init__(self, name, revision, air_weight, water_weight, length_mm, outside_diameter,
                 inner_diameter, contact_diameter, material="Steel"):
        self.__name = name,
        self.__revision = revision,
        self.__aw = air_weight,
        self.__ww = water_weight,
        self.__length = length_mm,
        self.__od = outside_diameter,
        self.__id = inner_diameter,
        self.__cd = contact_diameter,
        self.__lwa = linear_weight(air_weight, length),
        self.__lww = linear_weight(water_weight, length),
        self.__out_d = accessories_d_out(air_weight, water_weight, inner_diameter, length),
        self.__b_stiffness = bending_stiffness(material, outside_diameter, inner_diameter),
        self.__t_stiffness = torsional_stiffness(material, outside_diameter, inner_diameter),
        self.__a_stiffness = axial_stiffness(material, outside_diameter, inner_diameter)


class Vcm:
    def __init__(self, name, revision, supplier, draw, material, weight, declination, coord):
        self.__name = name,
        self.__revision = revision,
        self.__supplier = supplier,
        self.__draw = draw,
        self.__type = material,
        self.__weight = weight,
        self.__declination = declination,
        self.__a, self.__b, self.__c, self.__d, self.__e, self.__f, self.__g, self.__h = coord
        self.__cg_az = cg_olhal_flange(coord[5], - coord[3]),
        self.__cg_bx = cg_olhal_flange(coord[6], - coord[4]),
        self.__olhal_cz = cg_olhal_flange(coord[5], coord[1]),
        self.__olhal_dx = cg_olhal_flange(coord[6], - coord[2]),
        self.__flange_ez = cg_olhal_flange(.0, coord[5])
        self.__flange_fx = cg_olhal_flange(.0, coord[6])


line = Line(
    json_data[0]["ident_line"], json_data[0]["version_line"], json_data[0]["wt_air_line"],
    json_data[0]["sw_filled_air_line"], json_data[0]["air_filled_sw_line"],
    json_data[0]["sw_filled_sw_line"], json_data[0]["water_depth"],
    json_data[0]["contact_diameter_line"], json_data[0]["nominal_diameter_line"],
    json_data[0]["mbr_storage_line [m]"], json_data[0]["mbr_installation_line"],
    json_data[0]["bending_stiffness_line"], json_data[0]["torsional_stiffness_line"],
    json_data[0]["axial_stiffness_line"], json_data[0]["rel_elong_line"], json_data[1]
)

stiffness_curve_bend_restrictor = [
    [
        .0,
        round(1 / json_data[2]["locking_mbr_bend_restrictor"], 4),
        round(1 + 1 / json_data[2]["locking_mbr_bend_restrictor"], 4)
    ],
    [
        .0,
        .01,
        bend_moment_limit(json_data[2]["type_bend_restrictor"],
                          json_data[2]["od_bend_restrictor"],
                          json_data[2]["id_bend_restrictor"])
    ]
]
bend_restrictor = BendRestrictor(
    json_data[2]["ident_bend_restrictor"], json_data[2]["version_bend_restrictor"],
    json_data[2]["type_bend_restrictor"], json_data[2]["length_bend_restrictor"],
    json_data[2]["wt_air_bend_restrictor"], json_data[2]["wt_sw_bend_restrictor"],
    json_data[2]["od_bend_restrictor"], json_data[2]["id_bend_restrictor"],
    json_data[2]["contact_diameter_bend_restrictor"], json_data[2]["locking_mbr_bend_restrictor"],
    json_data[2]["bend_moment_bend_restrictor"], json_data[2]["shear_stress_bend_restrictor"],
    stiffness_curve_bend_restrictor
)

end_fitting = Accessory(
    json_data[3]["ident_end_fitting"], json_data[3]["version_end_fitting"],
    json_data[3]["wt_air_end_fitting"], json_data[3]["wt_sw_end_fitting"],
    json_data[3]["length_end_fitting"], json_data[3]["od_end_fitting"],
    json_data[3]["id_end_fitting"], json_data[3]["contact_diameter_end_fitting"]
)

vcm_geometry = [
    json_data[5]["a_vcm"], json_data[5]["b_vcm"], json_data[5]["c_vcm"], json_data[5]["d_vcm"],
    json_data[5]["e_vcm"], json_data[5]["f_vcm"], json_data[5]["g_vcm"], json_data[5]["h_vcm"]
]
vcm = Vcm(
    json_data[5]["subsea_equipment"], json_data[5]["version_vcm"], json_data[5]["supplier_vcm"],
    json_data[5]["drawing_vcm"], json_data[5]["subsea_equipment_type"], json_data[5]["wt_sw_vcm"],
    json_data[5]["declination"], vcm_geometry
)

olhal_height = (json_data[5]["b_vcm"] + json_data[5]["a_vcm"]) / 1_000
winch_length = json_data[0]["water_depth"] - olhal_height

list_bathymetric = json_data[6]
depth = [(json_data[0]["water_depth"] + (list_bathymetric[1][i] - json_data[5]["a_vcm"]) / 1_000)
         for i in range(len(list_bathymetric[0]))]
list_bathymetric.append(depth)

flange_height = (json_data[5]["a_vcm"] - json_data[5]["f_vcm"]) / 1_000
height_to_seabed = json_data[0]["water_depth"] - flange_height

# (bend restrictor + end fitting) length = br_ef_l
br_ef_l = (json_data[2]["length_bend_restrictor"] + json_data[3]["length_end_fitting"])
length = 160 + 100 + 40 + 10 + br_ef_l / 1_000

comb_data = [
    line, bend_restrictor, end_fitting, vcm, winch_length, list_bathymetric,
    height_to_seabed, json_data[7], json_data[8], json_data[9], json_data[10],
    json_data[11], length
]

if json_data[4]["ident_flange"] != "":
    flange = Accessory(
        json_data[4]["ident_flange"], json_data[4]["version_flange"], json_data[4]["wt_air_flange"],
        json_data[4]["wt_sw_flange"], json_data[4]["length_flange"], json_data[4]["od_flange"],
        json_data[4]["id_flange"], json_data[4]["contact_diameter_flange"]
    )

    comb_data[-1] += json_data[4]["length_flange"] / 1_000
    comb_data.append(flange)

    if json_data[2]["type_bend_restrictor"] == "Polymer":
        rigid_zone = Accessory(
            json_data[2]["rz_ident_bend_restrictor"], json_data[2]["rz_version_bend_restrictor"],
            json_data[2]["rz_wt_air_bend_restrictor"], json_data[2]["rz_wt_sw_bend_restrictor"],
            json_data[2]["rz_length_bend_restrictor"], json_data[2]["rz_od_bend_restrictor"],
            json_data[2]["rz_id_bend_restrictor"],
            json_data[2]["rz_contact_diameter_bend_restrictor"]
        )

        comb_data.append(rigid_zone)

new_combined_data = comb_data
