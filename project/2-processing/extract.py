"""
Realizes the moving of the json's file
Then, extracts file's data and passes it ot the next script
"""

import json
import os
from shutil import copy
from glob import glob

user_download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
json_files = glob(os.path.join(user_download_path, "*.json"))
if not json_files:
    raise FileNotFoundError(
        "Nenhum arquivo JSON encontrado na pasta Downloads.")
download_path = json_files[0]
json_name = os.path.basename(download_path)


def json_moving(origin_file_path: str, destiny_file_path: str) -> str:
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
            raise FileNotFoundError(
                f"Arquivo {origin_file_path} não encontrado.")
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


destiny_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'json')
json_file_path = json_moving(download_path, destiny_dir)
json_data = read_json(json_file_path)
