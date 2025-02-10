"""
Pré-processing of the data
before using it to build the OrcaFlex model
"""

# Libs

import numpy as np
from math import pow
from extract import data

# Methods

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
    return round(float(np.sqrt(4 / (np.pi * sd) * wd)), 3)

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
    return round(float(np.sqrt(4 / (np.pi * sd) * fwd)), 3)

def linear_weight(not_filled_weight, element_length):
    """
    Calculates the linear weight,
    in air and in water
    :param not_filled_weight: not filled weight, in air and in water
    :param element_length: element length
    :return: linear weight
    """
    return round(not_filled_weight / element_length, 3)

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
    return round(float(np.sqrt((4 / np.pi / sd) * (lwa - lww) + ids)), 3)

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
    return round(ei * np.pi / 64 * trd, 3)

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
    return round((ei * np.pi / 4) * trd, 3)

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
    return round((gi * np.pi / 32) * trd, 3)

def bend_moment_limit(material, d_out, d_int):
    """
    Calculates the stiffness curve's bend moment limit for the bend restrictor
    :param material: accessory's material
    :param d_out: accessory's outside diameter
    :param d_int: accessory's interior diameter
    :return: bend moment limit
    """
    return round(bending_stiffness(material, d_out, d_int) + .01, 3)

def young_module(material):
    """
    Defines the accessory's Young's module
    :param material: steel or polymer
    :return: young's module
    """
    if material == "Polymer":
        return round(7 * 1_000_000, 3)
    else:
        return round(207 * 1_000_000, 3)

def cg_olhal_flange(cote_1, cote_2):
    """
    Calculates the VCM's points
    :param cote_1: some VCM's point
    :param cote_2: another some VCM's pont
    :return: main VCM's point
    """
    return round(cote_1 / 1_000 + cote_2 / 1_000, 3)

class Line:
    def __init__(self, name, length, empty_air_weight, filled_air_weight, empty_water_weight, filled_water_weight, 
                 water_depth, contact_diameter, nominal_diameter, mbr_storage, mbr_installation, b_stiffness, 
                 t_stiffness, a_stiffness, relative_elongation, s_curve):
        self.name = name  #
        self.length = length
        self.eaw = round(empty_air_weight / 1_000, 3)  #
        self.faw = round(filled_air_weight / 1_000, 3)
        self.eww = round(empty_water_weight / 1_000, 3)
        self.fww = round(filled_water_weight / 1_000, 3)
        self.lda = water_depth  #
        self.cd = round(contact_diameter / 1_000, 3)  #
        self.nd = nominal_diameter
        self.mbr_s = mbr_storage
        self.mbr_i = mbr_installation  #
        self.b_stiffness = b_stiffness
        self.t_stiffness = t_stiffness  #
        self.a_stiffness = a_stiffness  #
        self.r_elongation = relative_elongation
        self.od = line_d_out(empty_air_weight, empty_water_weight)  #
        self.id = line_d_int(empty_water_weight, filled_water_weight)  #
        self.curvature = s_curve[0]
        self.b_moment = [round(b_moment / 1_000, 3) for b_moment in s_curve[1]]

class BendRestrictor:
    def __init__(self, name, revision, material, length_mm, air_weight, water_weight, outside_diameter, 
                 inner_diameter, contact_diameter, mbr, bend_moment, shear_force, s_curve):
        self.name = name
        self.revision = revision
        self.material = material
        self.length = round(length_mm / 1_000, 3)  #
        self.aw = air_weight
        self.ww = water_weight
        self.out_d = outside_diameter
        self.id = round(inner_diameter / 1_000, 3)  #
        self.cd = round(contact_diameter / 1_000, 3)  #
        self.mbr = mbr  #
        if bend_moment not in (None, "None", "null"):
            self.bm = bend_moment
        else:
            self.bm = 0
        if shear_force  not in (None, "None", "null"):
            self.sf = shear_force
        else:
            self.sf = 0
        self.lwa = linear_weight(air_weight, length_mm)  #
        self.lww = linear_weight(water_weight, length_mm)
        self.od = accessories_d_out(air_weight, water_weight, inner_diameter, length_mm)  #
        self.b_stiffness = bending_stiffness(material, outside_diameter, inner_diameter)
        self.t_stiffness = 10.0  #
        self.a_stiffness = 10.0  #
        self.curvature = s_curve[0]
        self.b_moment = s_curve[1]

class Accessory:
    def __init__(self, name, revision, air_weight, water_weight, length_mm, outside_diameter, inner_diameter, contact_diameter, mbr, material="Steel"):
        self.name = name
        self.revision = revision
        self.aw = air_weight
        self.ww = water_weight
        self.length = round(length_mm / 1_000, 3)  #
        self.out_d = outside_diameter
        self.id = round(inner_diameter / 1_000, 3)  #
        self.cd = round(contact_diameter / 1_000, 3)  #
        self.mbr = mbr  #
        self.lwa = linear_weight(air_weight, length_mm)  #
        self.lww = linear_weight(water_weight, length_mm)
        self.od = accessories_d_out(air_weight, water_weight, inner_diameter, length_mm)  #
        self.b_stiffness = bending_stiffness(material, outside_diameter, inner_diameter)  #
        self.t_stiffness = torsional_stiffness(material, outside_diameter, inner_diameter)  #
        self.a_stiffness = axial_stiffness(material, outside_diameter, inner_diameter)  #

class Vcm:
    def __init__(self, name, revision, supplier, draw, material, weight, declination, coord, lda):
        self.name = name
        self.revision = revision
        self.supplier = supplier
        self.draw = draw
        self.type = material
        self.weight = round(weight / 1_000, 3)
        self.declination = declination
        self.a, self.b, self.c, self.d, self.e, self.f, self.g, self.h = coord
        self.cg_az = cg_olhal_flange(self.f, - self.d)
        self.cg_bx = cg_olhal_flange(self.g, - self.e)
        self.olhal_cz = cg_olhal_flange(self.f, self.b)
        self.olhal_dx = cg_olhal_flange(self.g, - self.c)
        self.flange_ez = cg_olhal_flange(.0, self.f)
        self.flange_fx = cg_olhal_flange(.0, self.g)
        self.hts = - round((lda - ((self.a - self.f) / 1_000)), 3)

line = Line(data[0]["ident_line"], data[0]["line_length"], data[0]["wt_air_line"], data[0]["sw_filled_air_line"], data[0]["air_filled_sw_line"], data[0]["sw_filled_sw_line"], data[0]["water_depth"], 
            data[0]["contact_diameter_line"], data[0]["nominal_diameter_line"], data[0]["mbr_storage_line [m]"], data[0]["mbr_installation_line"], data[0]["bending_stiffness_line"], 
            data[0]["torsional_stiffness_line"], data[0]["axial_stiffness_line"], data[0]["rel_elong_line"], data[1])

stiffness_curve_bend_restrictor = [[.0, round(1 / data[2]["locking_mbr_bend_restrictor"], 4), round(1 + 1 / data[2]["locking_mbr_bend_restrictor"], 4)],
                                   [.0, .01, bend_moment_limit(data[2]["type_bend_restrictor"], data[2]["od_bend_restrictor"], data[2]["id_bend_restrictor"])]]

bend_restrictor = BendRestrictor(data[2]["ident_bend_restrictor"], data[2]["version_bend_restrictor"], data[2]["type_bend_restrictor"], data[2]["length_bend_restrictor"], data[2]["wt_air_bend_restrictor"], 
                                 data[2]["wt_sw_bend_restrictor"], data[2]["od_bend_restrictor"], data[2]["id_bend_restrictor"], data[2]["contact_diameter_bend_restrictor"], data[2]["locking_mbr_bend_restrictor"], 
                                 data[2]["bend_moment_bend_restrictor"], data[2]["shear_stress_bend_restrictor"], stiffness_curve_bend_restrictor)

end_fitting = Accessory(data[3]["ident_end_fitting"], data[3]["version_end_fitting"], data[3]["wt_air_end_fitting"], data[3]["wt_sw_end_fitting"], data[3]["length_end_fitting"], data[3]["od_end_fitting"], 
                        data[3]["id_end_fitting"], data[3]["contact_diameter_end_fitting"], data[2]["locking_mbr_bend_restrictor"])

vcm_geometry = [data[5]["a_vcm"], data[5]["b_vcm"], data[5]["c_vcm"], data[5]["d_vcm"], data[5]["e_vcm"], data[5]["f_vcm"], data[5]["g_vcm"], data[5]["h_vcm"]]

vcm = Vcm(data[5]["subsea_equipment"], data[5]["version_vcm"], data[5]["supplier_vcm"], data[5]["drawing_vcm"], data[5]["subsea_equipment_type"], data[5]["wt_sw_vcm"], data[5]["declination"], 
          vcm_geometry, data[0]["water_depth"])

olhal_height = (data[5]["b_vcm"] + data[5]["a_vcm"]) / 1_000

winch_length = data[0]["water_depth"] - olhal_height

list_bathymetric = data[6]
depth = [(data[0]["water_depth"] + (list_bathymetric[1][i] - data[5]["a_vcm"]) / 1_000) for i in range(len(list_bathymetric[0]))]
list_bathymetric.append(depth)

# length discounted of seawater depth to be set as line_type.length[0]
br_ef_length = (data[2]["length_bend_restrictor"] + data[3]["length_end_fitting"])
length = 160 + 100 + 40 + 20 + br_ef_length / 1_000
if data[0]["line_length"] != data[0]["water_depth"]:
    difference_lda = data[0]['water_depth'] - data[0]['line_length']
    length += difference_lda

# json_data[7] = rt_number
# json_data[8] = vessel_name
# json_data[9] = vessel's buoy_set
# json_data[10] = RL's buoy_configuration
# json_data[11] = structural_limits

info = (data[7], data[8], data[9], data[10], data[11])

comb_data = [ line, bend_restrictor, end_fitting, vcm, winch_length, list_bathymetric, data[7], length]

if bend_restrictor.material == "Polymer":
    rigid_zone = Accessory(data[2]["rz_ident_bend_restrictor"], data[2]["rz_version_bend_restrictor"], data[2]["rz_wt_air_bend_restrictor"], data[2]["rz_wt_sw_bend_restrictor"],
                           data[2]["rz_length_bend_restrictor"], data[2]["rz_od_bend_restrictor"], data[2]["rz_id_bend_restrictor"], data[2]["rz_contact_diameter_bend_restrictor"],
                           data[2]["locking_mbr_bend_restrictor"])
    comb_data.append(rigid_zone)

if data[4]["ident_flange"] != "":
    flange = Accessory(data[4]["ident_flange"], data[4]["version_flange"], data[4]["wt_air_flange"], data[4]["wt_sw_flange"], data[4]["length_flange"], data[4]["od_flange"],
                       data[4]["id_flange"], data[4]["contact_diameter_flange"], data[2]["locking_mbr_bend_restrictor"])
    
    if bend_restrictor.material == "Polymer":
        comb_data[-2] += data[4]["length_flange"] / 1_000
    
    else:
        comb_data[-1] += data[4]["length_flange"] / 1_000
    
    comb_data.append(flange)

new_combined_data = comb_data
