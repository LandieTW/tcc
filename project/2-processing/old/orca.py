#!/usr/bin/env python
# -*- coding: utf-8 -*-


from methods import dict_linha
from methods import dict_vertebra
from methods import zr_vert
if zr_vert:
    from methods import dict_zr_vertebra
from methods import dict_zr_vertebra
from methods import dict_conector
from methods import dict_flange
from methods import dict_mcv
from methods import list_histerese
from methods import list_vertebra
from methods import list_batimetria
from methods import comprimento_ar_guindaste
from methods import desenho_mcv
from methods import h_ao_solo


def gerar_modelo():
    if dict_flange["Comprimento [mm]"] != "":
        length_1 = dict_linha["LDA [m]"] - dict_vertebra["Comprimento [mm]"] / 1000 - dict_conector["Comprimento [mm]"] / 1000 - dict_flange["Comprimento [mm]"] / 1000 - 310
    else:
        length_1 = dict_linha["LDA [m]"] - dict_vertebra["Comprimento [mm]"] / 1000 - dict_conector["Comprimento [mm]"] / 1000 - 310  # perguntar pro IAS sobre o 310

    # line commands

    loading = """LoadData 'ModeloRTCVD1a.dat'"""
    line_od = f"Select Line Select Linha OD = {dict_linha["OD [m]"]}"
    line_id = f"Select Line Select Linha ID = {dict_linha["ID [m]"]}"
    line_mass_per_unit_length = f"Select Line Select Linha MassPerUnitLength = {dict_linha["Peso vazio no ar [kg/m]"] / 1000}"
    line_contact_diameter = f"Select Line Select Linha ContactDiameter = {dict_linha["Diametro de contato [mm]"] / 1000}"
    line_normal_drag_lift_diameter = f"Select Line Select Linha NormalDragLiftDiameter = {dict_linha["Diametro de contato [mm]"] / 1000}"
    line_axial_drag_lift_diameter = f"Select Line Select Linha AxialDragLiftDiameter = {dict_linha["Diametro de contato [mm]"] / 1000}"
    line_length = f"Select Line Length[1] = {length_1}"
    line_axial_stiffness = f"Select Line Select Linha EA = {dict_linha["Axial Stiffness [kN]"]}"
    line_mbr = f"Select Line Select Linha xMinRadius = {dict_linha["MBR installation [m]"]}"
    line_gj = f"Select Line Select Linha GJ = {dict_linha["Torsional Stiffness [kN.m²]"]}"
    line_endb_x = f"Select Line EndBX = {dict_mcv["Flange F [m] (X)"]}"
    line_endb_z = f"Select Line EndBZ = {dict_mcv["Flange E [m] (Z)"]}"
    line_endb_declination = f"Select Lina EndBDeclination = {dict_mcv["Angulo de inclinacao [°]"]}"
    line_name = f"Select Linha Name = {dict_linha["ID da Linha"].replace(" ", "_")}"

    # bend_restrictor commands

    bend_restrictor_length_6 = f"Select Line Length[6] = {dict_vertebra["Comprimento [mm]"] / 1000}"
    bend_restrictor_od = f"Select Line Select Vértebra OD = {dict_vertebra["OD [m]"]}"
    bend_restrictor_id = f"Select Line Select Vértebra ID = {dict_vertebra["ID [mm]"] / 1000}"
    bend_restrictor_mass_per_unit_length = f"Select Line Select Vértebra MassPerUnitLength = {dict_vertebra["Peso no ar/comp [t/m]"]}"
    bend_restrictor_axial_stiffness = f"Select Line Select Vértebra EA = {dict_vertebra["Axial Stiffness [kN]"]}"
    bend_restrictor_mbr = f"Select Line Select Vértebra xMinRadius = {dict_vertebra["MBR travamento [m]"]}"
    bend_restrictor_normal_drag_lift_diameter = f"Select Line Select Vértebra NormalDragLiftDiameter = {dict_vertebra["Diametro de contato [mm]"] / 1000}"
    bend_restrictor_axial_drag_lift_diameter = f"Select Line Select Vértebra AxialDragLiftDiameter = {dict_vertebra["Diametro de contato [mm]"] / 1000}"
    bend_restrictor_contact_diameter = f"Select Line Select Vértebra ContactDiameter = {dict_vertebra["Diametro de contato [mm]"] / 1000}"
    bend_restrictor_gj = f"Select Line Select Vértebra GJ = {dict_vertebra["Torsional Stiffness [kN.m²]"]}"
    bend_restrictor_length = f"Select Vert Length = {dict_vertebra["Comprimento [mm]"] / 1000}"
    bend_restrictor_name = f"Select Vértebra Name = {dict_vertebra["Id da Vertebra"].replace(" ", "_")}"

    # stiffener commands

    stiffener_length = f"Select Line Length[7] = {dict_conector["Comprimento [mm]"] / 1000}"
    stiffener_od = f"Select Line Select Conector OD = {dict_conector["OD [m]"]}"
    stiffener_id = f"Select Line Select Conector ID = {dict_conector["ID [mm]"] / 1000}"
    stiffener_mass_per_unit_length = f"Select Line Select Conector MassPerUnitLength = {dict_conector["Peso no ar/comp [t/m]"]}"
    stiffener_bend_stiffness = f"Select Line Select Conector EIx = {dict_conector["Bending Stiffness [kN.m²]"]}"
    stiffener_axial_stiffness = f"Select Line Select Conector EA = {dict_conector["Axial Stiffness [kN]"]}"
    stiffener_mbr = f"Select line Select Conector xMinRadius = {dict_vertebra["MBR travamento [m]"]}"
    stiffener_normal_drag_lift_diameter = f"Select Line Select Conector NormalDragLiftDiameter = {dict_conector["Diametro de contato [mm]"] / 1000}"
    stiffener_axial_drag_lift_diameter = f"Select Line Select Conector AxialDragLiftDiameter = {dict_conector["Diametro de contato [mm]"] / 1000}"
    stiffener_contact_diameter = f"Select Line Select Conector ContactDiameter = {dict_conector["Diametro de contato [mm]"] / 1000}"
    stiffener_gj = f"Select Line Select Conector GJ = {dict_conector["Torsional Stiffness [kN.m²]"]}"
    stiffener_name = f"Select Conector Name = {dict_conector["ID do Conector"].replace(" ", "_")}"

    flange_length = 0
    if dict_flange["Peso no ar/comp [t/m]"] in dict_flange:
        flange_od = f"Select Line Select Adaptador OD = {dict_flange["OD [m]"]}"
        flange_id = f"Select Line Select Adaptador ID = {dict_flange["ID [mm]"] / 1000}"
        flange_mass_per_unit_length = f"Select Line Select Adaptador MassPerUnitLength = {dict_flange["Peso no ar/comp [t/m]"]}"
        flange_bend_stiffness = f"Select Line Select Adaptador EIx = {dict_flange["Bending Stiffness [kN.m²]"]}"
        flange_axial_stiffness = f"Select Line Select Adaptador EA = {dict_flange["Axial Stiffness [kN]"]}"
        flange_mbr = f"Select Line Select Adaptador xMinRadius = {dict_vertebra["MBR travamento [m]"]}"
        flange_normal_drag_lift_diameter = f"Select Line Select Adaptador NormalDragLiftDiameter = {dict_flange["Diametro de contato [mm]"] / 1000}"
        flange_axial_drag_lift_diameter = f"Select Line Select Adaptador AxialDragLiftDiameter = {dict_flange["Diametro de contato [mm]"] / 1000}"
        flange_contact_diameter = f"Select Line Select Adaptador ContactDiameter = {dict_flange["Diametro de contato [mm]"] / 1000}"
        flange_gj = f"Select Line Select Adaptador GJ = {dict_flange["Torsional Stiffness [kN.m²]"]}"
        flange_name = f"Select Adaptador Name = {dict_flange["ID do Adaptador"].replace(" ", "_")}"
        flange_length = f"Select Line Length[8] = {dict_flange["Comprimento [mm]"] / 1000}"
    else:
        line_number_of_sections = f"Select Line NumberOfSections = {7.0}"

    attachmentz1 = f"Select Line Attachmentz[1] = {flange_length + stiffener_length}"

    # mcv Commands

    mcv_mass = f"Select MCV Mass = {dict_mcv["Peso submerso [kgf]"]}"
    mcv_height = f"Select MCV Height = {(dict_mcv["F [mm]"] + dict_mcv["B [mm]"]) / 1000}"
    mcv_initial_z = f"Select MCV InitialZ = {-1 * h_ao_solo}"
    mcv_centre_of_mass_x = f"Select MCV CentreOfMassX = {dict_mcv["CG B[m] (X)"]}"
    mcv_centre_of_mass_z = f"Select MCV CentreOfMassZ = {dict_mcv["CG A[m] (Z)"]}"
    mcv_centre_of_volume_x = f"Select MCV CentreOfVolumeX = {dict_mcv["CG B[m] (X)"]}"
    mcv_centre_of_volume_z = f"Select MCV CentreOfVolumeZ = {dict_mcv["CG A[m] (Z)"]}"
    mcv_name = f"Select MCV Name = {dict_mcv["ID do Projeto"].replace(" ", "_")}"

    # Winch Commands

    winch_connection_x_2 = f"Select Guindaste ConnectionX[2] = {dict_mcv["Olhal D [m] (X)"]}"
    winch_connection_z_2 = f"Select Guindaste ConnectionZ[2] = {dict_mcv["Olhal C [m] (Z)"]}"
    winch_stage = f"Select Guindaste StageValue[1] = {comprimento_ar_guindaste}"

    # Seabed Commands

    seabed_type = f"Select Environment SeabedType = {"Profile"}"
    seabed_profile_depth_1 = f"Select Environment SeabedProfileDepth[1] = {list_batimetria[2][0]}"
    seabed_number_of_points = f"Select Environment SeabedProfileNumberOfPoints = {len(list_batimetria[0])}"
