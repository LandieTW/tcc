import pandas as pd
from utils import excel_handler

xlsx_file = r"Installation Analysis Subsea - Daniel Wanderley\tcc\fleet_dvc\utils_teste.xlsx"

dd = excel_handler.load_data_range_to_df(
    xlsx_file=xlsx_file,
    range_name="VesselTable",
    is_table=True
)
print(dd)
de = excel_handler.load_data_range_to_df(
    xlsx_file=xlsx_file,
    range_name="UserName",
)
print(de)