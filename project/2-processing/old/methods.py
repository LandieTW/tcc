#!/usr/bin/env python
# -*- coding: utf-8 -*-


from numpy import sqrt
from numpy import pi
from math import pow
from extract import dict_linha
from extract import dict_vertebra
from extract import dict_conector
from extract import dict_flange
from extract import dict_mcv
from extract import list_histerese
from extract import list_batimetria


def od_id_linha(peso_1, peso_2):
    """Calcula o od da linha."""
    od_id = sqrt(4 / (pi * 1.025) * (peso_1 / 1000 - peso_2 / 1000))
    return round(od_id, 3)


def peso_por_comprimento(peso_vazio, comprimento):
    """Calcula o peso/metro da linha."""
    peso_ar_agua_por_metro = peso_vazio / comprimento
    return round(peso_ar_agua_por_metro, 3)


def od_function(peso_no_ar_por_metro, peso_na_agua_por_metro, id_vertebra):
    """Calcula o od de alguns acessórios."""
    od = sqrt((4 / pi / 1.025) * (peso_no_ar_por_metro - peso_na_agua_por_metro) * (pow(id_vertebra / 1000, 2)))
    return round(od, 3)


def bending_stiffness(mod_young, od_vert, id_vert):
    """Calcula a rigidez flexional do elemento."""
    b_stiffness = mod_young * ((pow(od_vert / 1000, 4)) - (pow(id_vert / 1000, 4))) / 64
    return round(b_stiffness, 3)


def axial_stiffness(mod_young, od_vert, id_vert):
    """Calcula a rigidez axial do elemento."""
    a_stiffness = mod_young * ((pow(od_vert / 1000, 2)) - (pow(id_vert / 1000, 2))) / 4
    return round(a_stiffness, 3)


def torsional_stiffness(mod_young, od_vert, id_vert):
    """Calcula a rigidez torsional do elemento."""
    t_stiffness = (mod_young / (2 * 1.3)) * ((pow(od_vert / 1000, 4)) - (pow(id_vert / 1000, 4))) / 32
    return round(t_stiffness, 3)


def bend_moment_limit(b_stiffness, mbr_travamento):
    """Calcula o Momento fletor último."""
    b_moment_limit = ((1 + (1 / mbr_travamento)) - (1/mbr_travamento)) * b_stiffness + .01
    return round(b_moment_limit, 3)


def modulo_young(mat_vert):
    """Define o módulo de elasticidade do material."""
    if mat_vert[0] == "P":
        return round(7 * 1000000 * pi, 3)
    else:
        return round(207 * 1000000 * pi, 3)


def cg_olhal_flange(cota1, cota2):
    """Calcula o centro geométrico do elemento."""
    return round((cota1 / 1000) + (cota2 / 1000), 3)


dict_linha["OD [m]"] = od_id_linha(dict_linha["Peso vazio no ar [kg/m]"], dict_linha["Peso vazio na agua [kg/m]"])
dict_linha["ID [m]"] = od_id_linha(dict_linha["Peso cheio na agua [kg/m]"], dict_linha["Peso vazio na agua [kg/m]"])

print(f"\nLinha: \n{dict_linha}\n")
print(f"Curva de rigidez da linha: \n"
      f"Curvatura: {list_histerese[0]} \n"
      f"Momento Fletor: {list_histerese[1]}\n")

"""DICIONÁRIO - ZONA RÍGIDA DA VÉRTEBRA"""

zr_vert = False
if "zr-Identificacao" in dict_vertebra:
    zr_vert = True
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
    dict_zr_vertebra["Peso no ar/comp [t/m]"] = peso_por_comprimento(dict_zr_vertebra["Peso vazio no ar [kg]"], dict_zr_vertebra["Comprimento [mm]"])
    dict_zr_vertebra["Peso na agua/comp [t/m]"] = peso_por_comprimento(dict_zr_vertebra["Peso vazio na agua [kg]"], dict_zr_vertebra["Comprimento [mm]"])
    dict_zr_vertebra["OD [m]"] = od_function(dict_zr_vertebra["Peso no ar/comp [t/m]"], dict_zr_vertebra["Peso na agua/comp [t/m]"], dict_zr_vertebra["ID [mm]"])
    dict_zr_vertebra["Modulo de Young [kN/m²]"] = modulo_young("")
    dict_zr_vertebra["Bending Stiffness [kN.m²]"] = bending_stiffness(dict_zr_vertebra["Modulo de Young [kN/m²]"], dict_zr_vertebra["OD [mm]"], dict_zr_vertebra["ID [mm]"])
    dict_zr_vertebra["Axial Stiffness [kN.m²]"] = bending_stiffness(dict_zr_vertebra["Modulo de Young [kN/m²]"], dict_zr_vertebra["OD [mm]"], dict_zr_vertebra["ID [mm]"])
    dict_zr_vertebra["Torsional Stiffness [kN.m²]"] = bending_stiffness(dict_zr_vertebra["Modulo de Young [kN/m²]"], dict_zr_vertebra["OD [mm]"], dict_zr_vertebra["ID [mm]"])

    print(f"Zona rígida da vértebra:\n{dict_zr_vertebra}\n")

"""DICIONÁRIO - VÉRTEBRA"""

dict_vertebra["Peso no ar/comp [t/m]"] = peso_por_comprimento(dict_vertebra["Peso vazio no ar [kg]"], dict_vertebra["Comprimento [mm]"])
dict_vertebra["Peso na agua/comp [t/m]"] = peso_por_comprimento(dict_vertebra["Peso vazio na agua [kg]"], dict_vertebra["Comprimento [mm]"])
dict_vertebra["OD [m]"] = od_function(dict_vertebra["Peso no ar/comp [t/m]"], dict_vertebra["Peso na agua/comp [t/m]"], dict_vertebra["ID [mm]"])
dict_vertebra["Modulo de Young [kN/m²]"] = modulo_young(dict_vertebra["Material da vertebra"])
dict_vertebra["Bending Stiffness [kN.m²]"] = bending_stiffness(dict_vertebra["Modulo de Young [kN/m²]"], dict_vertebra["OD [mm]"], dict_vertebra["ID [mm]"])
dict_vertebra["Axial Stiffness [kN]"] = 10.0
dict_vertebra["Torsional Stiffness [kN.m²]"] = 10.0

print(f"Vértebra:\n{dict_vertebra}\n")

"""CURVA DE RIGIDEZ - VERTEBRA"""

list_vertebra = [[], []]

list_vertebra[0].append(0)
list_vertebra[0].append(round(1 / dict_vertebra["MBR travamento [m]"], 2))
list_vertebra[0].append(1 + list_vertebra[0][1])
list_vertebra[1].append(0)
list_vertebra[1].append(.01)
list_vertebra[1].append(bend_moment_limit(dict_vertebra["Bending Stiffness [kN.m²]"], dict_vertebra["MBR travamento [m]"]))

print(f"Curva de rigidez da vértebra:\n"
      f"Curvatura: {list_vertebra[0]}\n"
      f"Momento Fletor: {list_vertebra[1]}\n")

"""DICIONÁRIO - CONECTOR"""

dict_conector["Peso no ar/comp [t/m]"] = peso_por_comprimento(dict_conector["Peso vazio no ar [kg]"], dict_conector["Comprimento [mm]"])
dict_conector["Peso na agua/comp [t/m]"] = peso_por_comprimento(dict_conector["Peso vazio na agua [kg]"], dict_conector["Comprimento [mm]"])
dict_conector["OD [m]"] = od_function(dict_conector["Peso no ar/comp [t/m]"], dict_conector["Peso na agua/comp [t/m]"], dict_conector["ID [mm]"])
dict_conector["Modulo de Young [kN/m²]"] = modulo_young("Aço")
dict_conector["Bending Stiffness [kN.m²]"] = bending_stiffness(dict_conector["Modulo de Young [kN/m²]"], dict_conector["OD [mm]"], dict_conector["ID [mm]"])
dict_conector["Axial Stiffness [kN.m²]"] = axial_stiffness(dict_conector["Modulo de Young [kN/m²]"], dict_conector["OD [mm]"], dict_conector["ID [mm]"])
dict_conector["Torsional Stiffness [kN.m²]"] = torsional_stiffness(dict_conector["Modulo de Young [kN/m²]"], dict_conector["OD [mm]"], dict_conector["ID [mm]"])

print(f"Conector:\n{dict_conector}\n")

"""DICIONÁRIO - ADAPTADOR DE FLANGE"""

if dict_flange["Comprimento [mm]"] != "":
    dict_flange["Peso no ar/comp [t/m]"] = peso_por_comprimento(dict_flange["Peso vazio no ar [kg]"], dict_flange["Comprimento [mm]"])
    dict_flange["Peso na agua/comp [t/m]"] = peso_por_comprimento(dict_flange["Peso vazio na agua [kg]"], dict_flange["Comprimento [mm]"])
    dict_flange["OD [m]"] = od_function(dict_flange["Peso no ar/comp [t/m]"], dict_flange["Peso na agua/comp [t/m]"], dict_flange["ID [mm]"])
    dict_flange["Modulo de Young [kN/m²]"] = modulo_young("")
    dict_flange["Bending Stiffness [kN.m²]"] = bending_stiffness(dict_flange["Modulo de Young [kN/m²]"], dict_flange["OD [mm]"], dict_flange["ID [mm]"])
    dict_flange["Axial Stiffness [kN.m²]"] = axial_stiffness(dict_flange["Modulo de Young [kN/m²]"], dict_flange["OD [mm]"], dict_flange["ID [mm]"])
    dict_flange["Torsional Stiffness [kN.m²]"] = torsional_stiffness(dict_flange["Modulo de Young [kN/m²]"], dict_flange["OD [mm]"], dict_flange["ID [mm]"])

    print(f"Adaptador de flange:\n{dict_flange}\n")

"""DICIONÁRIO - MCV"""

dict_mcv["Volume"] = 1 * pow(10, -6)
dict_mcv["CG A [m] (Z)"] = cg_olhal_flange(dict_mcv["F [mm]"], -dict_mcv["D [mm]"])
dict_mcv["CG B[m] (X)"] = cg_olhal_flange(dict_mcv["G [mm]"], - dict_mcv["E [mm]"])
dict_mcv["Olhal C [m] (Z)"] = cg_olhal_flange(dict_mcv["F [mm]"], dict_mcv["B [mm]"])
dict_mcv["Olhal D [m] (X)"] = cg_olhal_flange(dict_mcv["G [mm]"], -dict_mcv["C [mm]"])
dict_mcv["Flange E [m] (Z)"] = cg_olhal_flange(0, dict_mcv["F [mm]"])
dict_mcv["Flange F [m] (X)"] = cg_olhal_flange(0, dict_mcv["G [mm]"])

print(f"MCV:\n{dict_mcv}\n")

"""COMPRIMENTO - GUINDASTE"""

comprimento_ar_guindaste = (dict_linha["LDA [m]"] - dict_mcv["B [mm]"] / 1000 - dict_mcv["A [mm]"] / 1000)

print(f"Comprimento dos Cabos [m]:\n{comprimento_ar_guindaste}\n")

"""DESENHO -MCV"""

desenho_mcv = ((.25, .25, 1.2), (-.25, .25, 1.2), (-.25, -.25, 1.2), (.25, -.25, 1.2), (.5, .5, 0), (-.5, .5, 0), (-.5, -.5, 0), (.5, -.5, 0))

"""BATIMETRIA - PROFUNDIDADE"""

profundidade = []

for i in range(len(list_batimetria[0])):
    profundidade.append(dict_linha["LDA [m]"] + list_batimetria[1][i] / 1000 - dict_mcv["A [mm]"] / 1000)

list_batimetria.append(profundidade)

print(f"Batimetria:\n"
      f"Distância a partir do flange [m]: {list_batimetria[0]}\n"
      f"Altura em relação ao solo [m]: {list_batimetria[1]}\n"
      f"Profundidade [m]: {list_batimetria[2]}")

h_ao_solo = dict_linha["LDA [m]"] - dict_mcv["A [mm]"] - dict_mcv["F [mm]"] / 1000
