#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comentários - Reunião 03/05/24

Utilizar POO

Modularizar - um arquivo para cada coisa

Proposta de cronograma até o final do semestre
"""


from json import load
from os import path
from os import remove
from shutil import copy
from numpy import sqrt
from numpy import pi
from math import pow

"""LENDO O ARQUIVO json.data GERADO PELA INTERFACE"""

json_file = path.join(path.expanduser('~'), 'Downloads', 'data.json')

if path.exists(json_file):
    diretorio_destino = path.dirname(path.abspath(__file__))

    copy(json_file, diretorio_destino)  # copia o .json na pasta de destino

    remove(json_file)  # remove o .json da pasta Downloads

with open("data.json") as file:
    data = load(file)

dict_linha = data["dict_linha"]
dict_vertebra = data["dict_vertebra"]
dict_conector = data["dict_conector"]
dict_flange = data["dict_flange"]
dict_mcv = data["dict_mcv"]
list_histerese = data["list_histerese"]
list_batimetria = data["list_batimetria"]

"""CONSTRUINDO OS DADOS CALCULADOS DOS ELEMENTOS"""

"""FUNÇÕES"""


def od_id_linha(peso_1, peso_2):
    a = 4 / (pi * 1.025)
    b = float(peso_1) / 1000
    c = float(peso_2) / 1000
    od_id = sqrt(a * (b - c))

    return round(od_id, 3)


def peso_por_comprimento(peso_vazio, comprimento):
    peso = float(peso_vazio) / 1000
    comp = float(comprimento) / 1000
    peso_ar_agua_por_metro = peso / comp

    return round(peso_ar_agua_por_metro, 3)


def od_function(peso_no_ar_por_metro, peso_na_agua_por_metro, id_vertebra):
    a = 4 / pi / 1.025  # tirar dúvida sobre este cálculo
    b = float(peso_no_ar_por_metro) - float(peso_na_agua_por_metro)
    c = pow(float(id_vertebra) / 1000, 2)
    od = sqrt(a * b * c)

    return round(od, 3)


def bending_stiffness(mod_young, od_vert, id_vert):
    a = pow(float(od_vert) / 1000, 4)
    b = pow(float(id_vert) / 1000, 4)
    b_stiffness = float(mod_young) * (a - b) / 64

    return round(b_stiffness, 3)


def axial_stiffness(mod_young, od_vert, id_vert):
    a = pow(float(od_vert) / 1000, 2)
    b = pow(float(id_vert) / 1000, 2)
    a_stiffness = float(mod_young) * (a - b) / 4

    return round(a_stiffness, 3)


def torsional_stiffness(mod_young, od_vert, id_vert):
    a = float(mod_young) / (2 * 1.3)
    b = pow(float(od_vert) / 1000, 4)
    c = pow(float(id_vert) / 1000, 4)
    t_stiffness = a * (b - c) / 32

    return round(t_stiffness, 3)


def bend_moment_limit(b_stiffness, mbr_travamento):
    a = 1 / float(mbr_travamento)
    b = 1 + a
    b_moment_limit = (b - 1) * float(b_stiffness) + .01

    return round(b_moment_limit, 3)


def material_vertebra(mat_vert):
    if str(mat_vert) == "P":
        return "PU"
    else:
        return "Aco"


def modulo_young(mat_vert):
    if str(mat_vert) == "PU":
        return round(7 * 1000000 * pi, 3)
    else:
        return round(207 * 1000000 * pi, 3)


def cg_olhal_flange(cota1, cota2):
    a = float(cota1) / 1000
    b = float(cota2) / 1000

    return round(a + b, 3)


def gerar_modelo():

    if dict_flange["Comprimento [mm]"] != "":
        length_1 = float(dict_linha["LDA [m]"]) - float(dict_vertebra["Comprimento [mm]"])/1000 - float(dict_conector["Comprimento [mm]"])/1000 - float(dict_flange["Comprimento [mm]"])/1000 - 310
    else:
        length_1 = float(dict_linha["LDA [m]"]) - float(dict_vertebra["Comprimento [mm]"]) / 1000 - float(dict_conector["Comprimento [mm]"]) / 1000 - 310   # perguntar pro IAS sobre o 310

    # line commands

    loading = """LoadData 'ModeloRTCVD1a.dat'"""
    line_od = f"Select Line Select Linha OD = {float(dict_linha["OD [m]"])}"
    line_id = f"Select Line Select Linha ID = {float(dict_linha["ID [m]"])}"
    line_mass_per_unit_length = f"Select Line Select Linha MassPerUnitLength = {float(dict_linha["Peso vazio no ar [kg/m]"])/1000}"
    line_contact_diameter = f"Select Line Select Linha ContactDiameter = {float(dict_linha["Diametro de contato [mm]"])/1000}"
    line_normal_drag_lift_diameter = f"Select Line Select Linha NormalDragLiftDiameter = {float(dict_linha["Diametro de contato [mm]"])/1000}"
    line_axial_drag_lift_diameter = f"Select Line Select Linha AxialDragLiftDiameter = {float(dict_linha["Diametro de contato [mm]"])/1000}"
    line_length = f"Select Line Length[1] = {length_1}"
    line_axial_stiffness = f"Select Line Select Linha EA = {float(dict_linha["Axial Stiffness [kN]"])}"
    line_mbr = f"Select Line Select Linha xMinRadius = {float(dict_linha["MBR installation [m]"])}"
    line_gj = f"Select Line Select Linha GJ = {float(dict_linha["Torsional Stiffness [kN.m²]"])}"
    line_endb_x = f"Select Line EndBX = {float(dict_mcv["Flange F [m] (X)"])}"
    line_endb_z = f"Select Line EndBZ = {float(dict_mcv["Flange E [m] (Z)"])}"
    line_endb_declination = f"Select Lina EndBDeclination = {float(dict_mcv["Angulo de inclinacao [°]"])}"
    line_name = f"Select Linha Name = {str(dict_linha["ID da Linha"]).replace(" ", "_")}"

    # bend_restrictor commands

    bend_restrictor_length_6 = f"Select Line Length[6] = {float(dict_vertebra["Comprimento [mm]"])/1000}"
    bend_restrictor_od = f"Select Line Select Vértebra OD = {float(dict_vertebra["OD [m]"])}"
    bend_restrictor_id = f"Select Line Select Vértebra ID = {float(dict_vertebra["ID [mm]"])/1000}"
    bend_restrictor_mass_per_unit_length = f"Select Line Select Vértebra MassPerUnitLength = {float(dict_vertebra["Peso no ar/comp [t/m]"])}"
    bend_restrictor_axial_stiffness = f"Select Line Select Vértebra EA = {float(dict_vertebra["Axial Stiffness [kN]"])}"
    bend_restrictor_mbr = f"Select Line Select Vértebra xMinRadius = {float(dict_vertebra["MBR travamento [m]"])}"
    bend_restrictor_normal_drag_lift_diameter = f"Select Line Select Vértebra NormalDragLiftDiameter = {float(dict_vertebra["Diametro de contato [mm]"])/1000}"
    bend_restrictor_axial_drag_lift_diameter = f"Select Line Select Vértebra AxialDragLiftDiameter = {float(dict_vertebra["Diametro de contato [mm]"])/1000}"
    bend_restrictor_contact_diameter = f"Select Line Select Vértebra ContactDiameter = {float(dict_vertebra["Diametro de contato [mm]"])/1000}"
    bend_restrictor_gj = f"Select Line Select Vértebra GJ = {float(dict_vertebra["Torsional Stiffness [kN.m²]"])}"
    bend_restrictor_length = f"Select Vert Length = {float(dict_vertebra["Comprimento [mm]"])/1000}"
    bend_restrictor_name = f"Select Vértebra Name = {str(dict_vertebra["Id da Vertebra"]).replace(" ", "_")}"

    # stiffener commands

    stiffener_length = f"Select Line Length[7] = {float(dict_conector["Comprimento [mm]"])/1000}"
    stiffener_od = f"Select Line Select Conector OD = {float(dict_conector["OD [m]"])}"
    stiffener_id = f"Select Line Select Conector ID = {float(dict_conector["ID [mm]"])/1000}"
    stiffener_mass_per_unit_length = f"Select Line Select Conector MassPerUnitLength = {float(dict_conector["Peso no ar/comp [t/m]"])}"
    stiffener_bend_stiffness = f"Select Line Select Conector EIx = {float(dict_conector["Bending Stiffness [kN.m²]"])}"
    stiffener_axial_stiffness = f"Select Line Select Conector EA = {float(dict_conector["Axial Stiffness [kN]"])}"
    stiffener_mbr = f"Select line Select Conector xMinRadius = {float(dict_vertebra["MBR travamento [m]"])}"
    stiffener_normal_drag_lift_diameter = f"Select Line Select Conector NormalDragLiftDiameter = {float(dict_conector["Diametro de contato [mm]"])/1000}"
    stiffener_axial_drag_lift_diameter = f"Select Line Select Conector AxialDragLiftDiameter = {float(dict_conector["Diametro de contato [mm]"])/1000}"
    stiffener_contact_diameter = f"Select Line Select Conector ContactDiameter = {float(dict_conector["Diametro de contato [mm]"])/1000}"
    stiffener_gj = f"Select Line Select Conector GJ = {float(dict_conector["Torsional Stiffness [kN.m²]"])}"
    stiffener_name = f"Select Conector Name = {str(dict_conector["ID do Conector"]).replace(" ", "_")}"

    flange_length = 0
    if dict_flange["Peso no ar/comp [t/m]"] in dict_flange:
        flange_od = f"Select Line Select Adaptador OD = {float(dict_flange["OD [m]"])}"
        flange_id = f"Select Line Select Adaptador ID = {float(dict_flange["ID [mm]"])/1000}"
        flange_mass_per_unit_length = f"Select Line Select Adaptador MassPerUnitLength = {float(dict_flange["Peso no ar/comp [t/m]"])}"
        flange_bend_stiffness = f"Select Line Select Adaptador EIx = {float(dict_flange["Bending Stiffness [kN.m²]"])}"
        flange_axial_stiffness = f"Select Line Select Adaptador EA = {float(dict_flange["Axial Stiffness [kN]"])}"
        flange_mbr = f"Select Line Select Adaptador xMinRadius = {float(dict_vertebra["MBR travamento [m]"])}"
        flange_normal_drag_lift_diameter = f"Select Line Select Adaptador NormalDragLiftDiameter = {float(dict_flange["Diametro de contato [mm]"])/1000}"
        flange_axial_drag_lift_diameter = f"Select Line Select Adaptador AxialDragLiftDiameter = {float(dict_flange["Diametro de contato [mm]"])/1000}"
        flange_contact_diameter = f"Select Line Select Adaptador ContactDiameter = {float(dict_flange["Diametro de contato [mm]"])/1000}"
        flange_gj = f"Select Line Select Adaptador GJ = {float(dict_flange["Torsional Stiffness [kN.m²]"])}"
        flange_name = f"Select Adaptador Name = {str(dict_flange["ID do Adaptador"]).replace(" ", "_")}"
        flange_length = f"Select Line Length[8] = {float(dict_flange["Comprimento [mm]"])/1000}"
    else:
        line_number_of_sections = f"Select Line NumberOfSections = {float(7)}"

    attachmentz1 = f"Select Line Attachmentz[1] = {flange_length + stiffener_length}"

    # mcv Commands

    mcv_mass = f"Select MCV Mass = {dict_mcv["Peso submerso [kgf]"]}"
    mcv_height = f"Select MCV Height = {(float(dict_mcv["F [mm]"]) + float(dict_mcv["B [mm]"]))/1000}"
    mcv_initial_z = f"Select MCV InitialZ = {-1 * h_ao_solo}"
    mcv_centre_of_mass_x = f"Select MCV CentreOfMassX = {dict_mcv["CG B[m] (X)"]}"
    mcv_centre_of_mass_z = f"Select MCV CentreOfMassZ = {dict_mcv["CG A[m] (Z)"]}"
    mcv_centre_of_volume_x = f"Select MCV CentreOfVolumeX = {dict_mcv["CG B[m] (X)"]}"
    mcv_centre_of_volume_z = f"Select MCV CentreOfVolumeZ = {dict_mcv["CG A[m] (Z)"]}"
    mcv_name = f"Select MCV Name = {str(dict_mcv["ID do Projeto"]).replace(" ", "_")}"

    # Winch Commands

    winch_connection_x_2 = f"Select Guindaste ConnectionX[2] = {float(dict_mcv["Olhal D [m] (X)"])}"
    winch_connection_z_2 = f"Select Guindaste ConnectionZ[2] = {float(dict_mcv["Olhal C [m] (Z)"])}"
    winch_stage = f"Select Guindaste StageValue[1] = {comprimento_ar_guindaste}"

    # Seabed Commands

    seabed_type = f"Select Environment SeabedType = {"Profile"}"
    seabed_profile_depth_1 = f"Select Environment SeabedProfileDepth[1] = {list_batimetria[2][0]}"
    seabed_number_of_points = f"Select Environment SeabedProfileNumberOfPoints = {len(list_batimetria[0])}"


"""DICIONÁRIO - LINHA"""

dict_linha["OD [m]"] = od_id_linha(
    dict_linha["Peso vazio no ar [kg/m]"],
    dict_linha["Peso vazio na agua [kg/m]"]
)
dict_linha["ID [m]"] = od_id_linha(
    dict_linha["Peso cheio na agua [kg/m]"],
    dict_linha["Peso vazio na agua [kg/m]"]
)

print(f"\nLinha: \n{dict_linha}\n")
print(f"Curva de rigidez da linha: \n"
      f"Curvatura: {list_histerese[0]} \n"
      f"Momento Fletor: {list_histerese[1]}\n")

"""DICIONÁRIO - ZONA RÍGIDA DA VÉRTEBRA"""

if "zr-Identificacao" in dict_vertebra:

    dict_zr_vertebra = {"Identificacao": dict_vertebra["zr-Identificacao"]}

    del dict_vertebra["zr-Identificacao"]

    dict_zr_vertebra["Revisao"] = dict_vertebra["zr-Revisao"]
    del dict_vertebra["zr-Revisao"]

    dict_zr_vertebra["Comprimento [mm]"] = dict_vertebra["zr-Comprimento [mm]"]
    del dict_vertebra["zr-Comprimento [mm]"]

    dict_zr_vertebra["Peso vazio no ar [kg]"] = dict_vertebra["zr-Peso vazio no ar [kg]"]
    del dict_vertebra["zr-Peso vazio no ar [kg]"]

    dict_zr_vertebra["Peso vazio na agua [kg]"] = dict_vertebra["zr-Peso vazio na agua [kg]"]
    del dict_vertebra["zr-Peso vazio na agua [kg]"]

    dict_zr_vertebra["OD [mm]"] = dict_vertebra["zr-OD [mm]"]
    del dict_vertebra["zr-OD [mm]"]

    dict_zr_vertebra["ID [mm]"] = dict_vertebra["zr-ID [mm]"]
    del dict_vertebra["zr_ID [mm]"]

    dict_zr_vertebra["Contact diameter [mm]"] = dict_vertebra["zr-Contact diameter [mm]"]
    del dict_vertebra["zr-Contact diameter [mm]"]

    dict_zr_vertebra["Peso no ar/comp [t/m]"] = peso_por_comprimento(
        dict_zr_vertebra["Peso vazio no ar [kg]"],
        dict_zr_vertebra["Comprimento [mm]"]
    )
    dict_zr_vertebra["Peso na agua/comp [t/m]"] = peso_por_comprimento(
        dict_zr_vertebra["Peso vazio na agua [kg]"],
        dict_zr_vertebra["Comprimento [mm]"]
    )
    dict_zr_vertebra["OD [m]"] = od_function(
        dict_zr_vertebra["Peso no ar/comp [t/m]"],
        dict_zr_vertebra["Peso na agua/comp [t/m]"],
        dict_zr_vertebra["ID [mm]"]
    )
    dict_zr_vertebra["Modulo de Young [kN/m²]"] = modulo_young(
        ""
    )
    dict_zr_vertebra["Bending Stiffness [kN.m²]"] = bending_stiffness(
        dict_zr_vertebra["Modulo de Young [kN/m²]"],
        dict_zr_vertebra["OD [mm]"],
        dict_zr_vertebra["ID [mm]"]
    )
    dict_zr_vertebra["Axial Stiffness [kN.m²]"] = bending_stiffness(
        dict_zr_vertebra["Modulo de Young [kN/m²]"],
        dict_zr_vertebra["OD [mm]"],
        dict_zr_vertebra["ID [mm]"]
    )
    dict_zr_vertebra["Torsional Stiffness [kN.m²]"] = bending_stiffness(
        dict_zr_vertebra["Modulo de Young [kN/m²]"],
        dict_zr_vertebra["OD [mm]"],
        dict_zr_vertebra["ID [mm]"]
    )

    print(f"Zona rígida da vértebra:\n{dict_zr_vertebra}\n")

"""DICIONÁRIO - VÉRTEBRA"""

dict_vertebra["Peso no ar/comp [t/m]"] = peso_por_comprimento(
    dict_vertebra["Peso vazio no ar [kg]"],
    dict_vertebra["Comprimento [mm]"]
)
dict_vertebra["Peso na agua/comp [t/m]"] = peso_por_comprimento(
    dict_vertebra["Peso vazio na agua [kg]"],
    dict_vertebra["Comprimento [mm]"]
)
dict_vertebra["OD [m]"] = od_function(
    dict_vertebra["Peso no ar/comp [t/m]"],
    dict_vertebra["Peso na agua/comp [t/m]"],
    dict_vertebra["ID [mm]"]
)
dict_vertebra["Material da vertebra"] = material_vertebra(
    dict_vertebra["Material da vertebra"][0]
)
dict_vertebra["Modulo de Young [kN/m²]"] = modulo_young(
    dict_vertebra["Material da vertebra"]
)
dict_vertebra["Bending Stiffness [kN.m²]"] = bending_stiffness(
    dict_vertebra["Modulo de Young [kN/m²]"],
    dict_vertebra["OD [mm]"],
    dict_vertebra["ID [mm]"]
)
dict_vertebra["Axial Stiffness [kN]"] = 10.0
dict_vertebra["Torsional Stiffness [kN.m²]"] = 10.0

print(f"Vértebra:\n{dict_vertebra}\n")

"""CURVA DE RIGIDEZ - VERTEBRA"""

list_vertebra = [[], []]

list_vertebra[0].append(
    0
)
list_vertebra[0].append(
    round(1 / float(dict_vertebra["MBR travamento [m]"]), 2)
)
list_vertebra[0].append(
    1 + list_vertebra[0][1]
)
list_vertebra[1].append(
    0
)
list_vertebra[1].append(
    .01
)
list_vertebra[1].append(
    bend_moment_limit(
        dict_vertebra["Bending Stiffness [kN.m²]"],
        dict_vertebra["MBR travamento [m]"]
    )
)

print(f"Curva de rigidez da vértebra:\n"
      f"Curvatura: {list_vertebra[0]}\n"
      f"Momento Fletor: {list_vertebra[1]}\n")

"""DICIONÁRIO - CONECTOR"""

dict_conector["Peso no ar/comp [t/m]"] = peso_por_comprimento(
    dict_conector["Peso vazio no ar [kg]"],
    dict_conector["Comprimento [mm]"]
)
dict_conector["Peso na agua/comp [t/m]"] = peso_por_comprimento(
    dict_conector["Peso vazio na agua [kg]"],
    dict_conector["Comprimento [mm]"]
)
dict_conector["OD [m]"] = od_function(
    dict_conector["Peso no ar/comp [t/m]"],
    dict_conector["Peso na agua/comp [t/m]"],
    dict_conector["ID [mm]"]
)
dict_conector["Modulo de Young [kN/m²]"] = modulo_young(
    ""
)
dict_conector["Bending Stiffness [kN.m²]"] = bending_stiffness(
    dict_conector["Modulo de Young [kN/m²]"],
    dict_conector["OD [mm]"],
    dict_conector["ID [mm]"]
)
dict_conector["Axial Stiffness [kN.m²]"] = bending_stiffness(
    dict_conector["Modulo de Young [kN/m²]"],
    dict_conector["OD [mm]"],
    dict_conector["ID [mm]"]
)
dict_conector["Torsional Stiffness [kN.m²]"] = bending_stiffness(
    dict_conector["Modulo de Young [kN/m²]"],
    dict_conector["OD [mm]"],
    dict_conector["ID [mm]"]
)

print(f"Conector:\n{dict_conector}\n")

"""DICIONÁRIO - ADAPTADOR DE FLANGE"""

if dict_flange["Comprimento [mm]"] != "":
    dict_flange["Peso no ar/comp [t/m]"] = peso_por_comprimento(
        dict_flange["Peso vazio no ar [kg]"],
        dict_flange["Comprimento [mm]"]
    )
    dict_flange["Peso na agua/comp [t/m]"] = peso_por_comprimento(
        dict_flange["Peso vazio na agua [kg]"],
        dict_flange["Comprimento [mm]"]
    )
    dict_flange["OD [m]"] = od_function(
        dict_flange["Peso no ar/comp [t/m]"],
        dict_flange["Peso na agua/comp [t/m]"],
        dict_flange["ID [mm]"]
    )
    dict_flange["Modulo de Young [kN/m²]"] = modulo_young(
        ""
    )
    dict_flange["Bending Stiffness [kN.m²]"] = bending_stiffness(
        dict_flange["Modulo de Young [kN/m²]"],
        dict_flange["OD [mm]"],
        dict_flange["ID [mm]"]
    )
    dict_flange["Axial Stiffness [kN.m²]"] = bending_stiffness(
        dict_flange["Modulo de Young [kN/m²]"],
        dict_flange["OD [mm]"],
        dict_flange["ID [mm]"]
    )
    dict_flange["Torsional Stiffness [kN.m²]"] = bending_stiffness(
        dict_flange["Modulo de Young [kN/m²]"],
        dict_flange["OD [mm]"],
        dict_flange["ID [mm]"]
    )

    print(f"Adaptador de flange:\n{dict_flange}\n")

"""DICIONÁRIO - MCV"""

dict_mcv["Angulo de inclinacao [°]"] = dict_mcv["Ã‚ngulo de inclinaÃ§ao [Â°]"]
del dict_mcv["Ã‚ngulo de inclinaÃ§ao [Â°]"]

dict_mcv["Volume"] = 1 * pow(10, -6)
dict_mcv["CG A [m] (Z)"] = cg_olhal_flange(
    dict_mcv["F [mm]"],
    -float(dict_mcv["D [mm]"])
)
dict_mcv["CG B[m] (X)"] = cg_olhal_flange(
    dict_mcv["G [mm]"],
    -float(dict_mcv["E [mm]"])
)
dict_mcv["Olhal C [m] (Z)"] = cg_olhal_flange(
    dict_mcv["F [mm]"],
    dict_mcv["B [mm]"]
)
dict_mcv["Olhal D [m] (X)"] = cg_olhal_flange(
    dict_mcv["G [mm]"],
    -float(dict_mcv["C [mm]"])
)
dict_mcv["Flange E [m] (Z)"] = cg_olhal_flange(
    0,
    dict_mcv["F [mm]"]
)
dict_mcv["Flange F [m] (X)"] = cg_olhal_flange(
    0,
    dict_mcv["G [mm]"]
)

print(f"MCV:\n{dict_mcv}\n")

"""COMPRIMENTO - GUINDASTE"""

comprimento_ar_guindaste = (float(dict_linha["LDA [m]"]) -
                            float(dict_mcv["B [mm]"])/1000 - float(dict_mcv["A [mm]"])/1000)

print(f"Comprimento dos Cabos [m]:\n{comprimento_ar_guindaste}\n")

"""DESENHO -MCV"""

desenho_mcv = (
    (.25, .25, 1.2),
    (-.25, .25, 1.2),
    (-.25, -.25, 1.2),
    (.25, -.25, 1.2),
    (.5, .5, 0),
    (-.5, .5, 0),
    (-.5, -.5, 0),
    (.5, -.5, 0)
)

"""BATIMETRIA - PROFUNDIDADE"""

profundidade = []

for i in range(len(list_batimetria[0])):
    profundidade.append(float(dict_linha["LDA [m]"]) +
                        float(list_batimetria[1][i])/1000 - float(dict_mcv["A [mm]"])/1000)

list_batimetria.append(profundidade)

print(f"Batimetria:\n"
      f"Distância a partir do flange [m]: {list_batimetria[0]}\n"
      f"Altura em relação ao solo [m]: {list_batimetria[1]}\n"
      f"Profundidade [m]: {list_batimetria[2]}")


h_ao_solo = (float(dict_linha["LDA [m]"]) -
             (float(dict_mcv["A [mm]"]) - float(dict_mcv["F [mm]"]))/1000)

"""Comandos p/ OrcaFlex"""
