
from openpyxl import load_workbook
import os


'This file path'
THIS_PATH = os.path.dirname(os.path.abspath(__file__))

'Excel sheets'
SHEET_PATH = os.path.join(THIS_PATH, [sheet 
                                      for sheet in os.listdir(THIS_PATH) 
                                      if sheet.endswith(".xlsm")][0])

EXCEL = load_workbook(filename=SHEET_PATH, data_only=True)
VALUES_SHEET = EXCEL['Values']

value = VALUES_SHEET['A31'].value

print(value)
