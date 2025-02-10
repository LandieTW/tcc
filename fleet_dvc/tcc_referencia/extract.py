"""
Realizes the moving of the json's file
Then, extracts file's data and passes it ot the next script
"""

# Libs

import json
import os
from collections import Counter
from shutil import copy
from glob import glob
from openpyxl import load_workbook

# Constants
    # Vessel buoys
cda_buoys = [1252, 1252, 1252, 973, 828, 573, 573, 573, 283, 283, 283, 205, 205, 205, 205, 118, 118, 118, 118, 118, 118, 100]
ska_buoys = [1416, 1376, 1345, 1323, 1320, 871, 741, 741, 660, 647, 381, 377, 155, 104, 101, 100]
skb_buoys = [1508, 1451, 1428, 1425, 1416, 1320, 760, 726, 708, 385]
skn_buoys = [1000, 1000, 1000, 1000, 1000, 500, 500, 500, 343, 100, 100, 100, 100, 100]
sko_buoys = [1213, 1213, 1213, 1213, 1213, 576, 576, 576, 576, 576, 381, 381, 381,381,381, 100, 100, 100, 100, 100]
skr_buoys = [1000, 1000, 1000, 1000, 1000, 500, 500, 500, 250, 250, 100, 100, 100, 100, 100]
skv_buoys = [1000, 1000, 1000, 1000, 1000, 500, 500, 500, 300, 100, 100, 100, 100, 100]
vessel_buoys = {'SKN': [Counter(skn_buoys).keys, Counter(skn_buoys).values], 'SKB': [Counter(skb_buoys).keys, Counter(skb_buoys).values], 
                'SKA': [Counter(ska_buoys).keys, Counter(ska_buoys).values], 'SKV': [Counter(skv_buoys).keys, Counter(skv_buoys).values], 
                'SKR': [Counter(skr_buoys).keys, Counter(skr_buoys).values], 'SKO': [Counter(sko_buoys).keys, Counter(sko_buoys).values], 
                'CDA': [Counter(cda_buoys).keys, Counter(cda_buoys).values]}
    # vessel names
vessel_names = {'Skandi Niterói': 'SKN', 'Skandi Búzios': 'SKB', 'Skandi Açu': 'SKA', 'Skandi Vitória': 'SKV', 'Skandi Recife': 'SKR', 'Skandi Olinda': 'SKO', 'Coral do Atlântico': 'CDA'}
    # rl_config
rl_config = [[3, 6], [800, 400]]

# Methods

def moving(origin_file_path: str, destiny_file_path: str) -> str:
    """
    Verify if the file is in directory /downloads
    Then, move it the directory /json
    If not, verify if the file already is in the directory /json
    Then, returns its path
    If not, returns a "File not found" message
    :param origin_file_path: origin json file's path
    :param destiny_file_path: destiny json's directory
    :return: path of the json file in the json's directory
    """
    if os.path.exists(origin_file_path):
        os.makedirs(destiny_file_path, exist_ok=True)
        destiny_path = os.path.join(destiny_file_path, json_name)
        if not os.path.exists(destiny_path):
            copy(origin_file_path, destiny_path)
            os.remove(origin_file_path)
    else:
        destiny_path = os.path.join(destiny_file_path, json_name)
        if not os.path.exists(destiny_path):
            raise FileNotFoundError(f"Arquivo {origin_file_path} não encontrado.")
    return destiny_path

def read_json(file_path: str) -> dict:
    """
    Reads a json file
    :param file_path: file's path
    :return: file's data
    """
    if os.path and os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        raise FileNotFoundError(f"Arquivo {file_path} não encontrado.")

def read_excel(file_path: str) -> dict:
    """
    Reads an excel file
    :param file_path: file's path
    :return: file's data
    """
    excel_data = []

    if os.path and os.path.exists(file_path):

        workbook = load_workbook(filename=file_path)

        sheet = workbook['Values']
        line = {
            "ident_line": sheet["A5"].value,
            "line_length": sheet["C3"].value,  # necessidade de ajuste p/ contemplar casos de CVD com jumper
            "wt_air_line": sheet["C4"].value,
            "sw_filled_air_line": sheet["C5"].value,
            "air_filled_sw_line": sheet["C6"].value,
            "sw_filled_sw_line": sheet["C7"].value,
            "water_depth": sheet["C3"].value,
            "contact_diameter_line": sheet["C10"].value,
            "nominal_diameter_line": sheet["C11"].value,
            "mbr_storage_line [m]":sheet["C12"].value,
            "mbr_installation_line": sheet["C13"].value,
            "bending_stiffness_line": sheet["C14"].value,
            "torsional_stiffness_line": sheet["C15"].value,
            "axial_stiffness_line": sheet["C17"].value,
            "rel_elong_line": sheet["C16"].value
            }
        excel_data.append(line)

        sheet = workbook['Bending Stiffness']
        line_stiffness = [
            [cell.value for cell in sheet["A5:A44"]],
            [cell.value for cell in sheet["B5:B44"]]
        ]
        excel_data.append(line_stiffness)

        sheet = workbook['Values']
        bend_restrictor = {
            "ident_bend_restrictor": sheet["A20"].value,
            "version_bend_restrictor": sheet["A22"].value,
            "type_bend_restrictor": sheet["A24"].value,
            "length_bend_restrictor": sheet["C18"].value,
            "wt_air_bend_restrictor": sheet["C19"].value,
            "wt_sw_bend_restrictor": sheet["C20"].value,
            "od_bend_restrictor": sheet["C24"].value,
            "id_bend_restrictor": sheet["C25"].value,
            "contact_diameter_bend_restrictor": sheet["C26"].value,
            "locking_mbr_bend_restrictor": sheet["C27"].value,
            "bend_moment_bend_restrictor": sheet["C28"].value,
            "shear_stress_bend_restrictor": sheet["C29"].value
            }
        if bend_restrictor['type_bend_restrictor'] == "PU":
            bend_restrictor["rz_ident_bend_restrictor"] = sheet["A66"].value
            bend_restrictor["rz_version_bend_restrictor"] = sheet["A68"].value
            bend_restrictor["rz_length_bend_restrictor"] = sheet["A64"].value
            bend_restrictor["rz_wt_air_bend_restrictor"] = sheet["A65"].value
            bend_restrictor["rz_wt_sw_bend_restrictor"] = sheet["A66"].value
            bend_restrictor["rz_od_bend_restrictor"] = sheet["A70"].value
            bend_restrictor["rz_id_bend_restrictor"] = sheet["A71"].value
            bend_restrictor["rz_contact_diameter_bend_restrictor"] = sheet["A72"].value
        excel_data.append(bend_restrictor)

        end_fitting = {
            "ident_end_fitting": sheet["A40"].value,
            "version_end_fitting": sheet["A42"].value,
            "wt_air_end_fitting": sheet["C39"].value,
            "wt_sw_end_fitting": sheet["C40"].value,
            "length_end_fitting": sheet["C38"].value,
            "od_end_fitting": sheet["C44"].value,
            "id_end_fitting": sheet["C45"].value,
            "contact_diameter_end_fitting": sheet["C46"].value
            }
        excel_data.append(end_fitting)

        flange_addapter = {
            "ident_flange": sheet["A53"].value,
            "version_flange": sheet["A55"].value,
            "wt_air_flange": sheet["C52"].value,
            "wt_sw_flange": sheet["C53"].value,
            "length_flange": sheet["C51"].value,
            "od_flange": sheet["C57"].value,
            "id_flange": sheet["C58"].value,
            "contact_diameter_flange": sheet["C59"].value
            }
        excel_data.append(flange_addapter)

        sheet = workbook['MCV e Guindaste']
        vcm = {
            "subsea_equipment": sheet["B3"].value,
            "version_vcm": sheet["B4"].value,
            "supplier_vcm": sheet["B5"].value,
            "drawing_vcm": sheet["B6"].value,
            "subsea_equipment_type": sheet["B7"].value,
            "wt_sw_vcm": sheet["C19"].value,
            "declination": sheet["C28"].value,
            "a_vcm": sheet["B8"].value,
            "b_vcm": sheet["B9"].value,
            "c_vcm": sheet["B10"].value,
            "d_vcm": sheet["B11"].value,
            "e_vcm": sheet["B12"].value,
            "f_vcm": sheet["B13"].value,
            "g_vcm": sheet["B14"].value,
            "h_vcm": sheet["B15"].value
            }
        excel_data.append(vcm)

        bathymetric = [
            [cell.value for cell in sheet["N21:N24"]],
            [cell.value for cell in sheet["M21:M24"]]
        ]
        excel_data.append(bathymetric)

        sheet = workbook['Results']
        excel_data.append('RT ' + str(sheet["H22"].value))
        
        vessel = sheet["H20"].value
        excel_data.append(vessel_names[vessel])

        excel_data.append(vessel_buoys[vessel_names[vessel]])

        excel_data.append(rl_config)  # completamente aleatório

        sheet = workbook['Esforços']
        loads = {
            '2': [cell.value for cell in sheet["G10:G12"]],
            '3': [cell.value for cell in sheet["G15:G17"]],
            '3i': [cell.value for cell in sheet["G18:G20"]],
            '3ii': [max(abs(sheet["G23"].value), abs(sheet["G26"].value)),
                    max(abs(sheet["G24"].value), abs(sheet["G27"].value)),
                    max(abs(sheet["G25"].value), abs(sheet["G28"].value))]
        }
        excel_data.append(loads)

        return excel_data

    else:
        raise FileNotFoundError(f"Arquivo {file_path} não encontrado.")

# Coding

this_path = os.path.dirname(__file__)
excel_files = glob(os.path.join(this_path, "*.xlsm"))

if not excel_files:
    user_download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    json_files_1 = glob(os.path.join(user_download_path, "*.json"))
    json_files_2 = glob(os.path.join(this_path, "*.json"))
    if not json_files_1:
        if not json_files_2:
            raise FileNotFoundError("Nenhum arquivo encontrado.")
        else:
            download_path = json_files_2[0]
    else:
        download_path = json_files_1[0]

    json_name = os.path.basename(download_path)
    destiny_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'json')
    json_file_path = moving(download_path, destiny_dir)
    json_data = read_json(json_file_path)
    data = json_data
else:
    download_path = excel_files[0]
    excel_name = os.path.basename(download_path)
    destiny_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'excel')
    excel_file_path = moving(download_path, destiny_dir)
    excel_data = read_excel(excel_file_path)
    data = excel_data
