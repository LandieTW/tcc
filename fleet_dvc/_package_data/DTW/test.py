
import locale
import sys
import os
import OrcFxAPI as orca
import glob
from pathlib import Path
from collections import defaultdict
from utils import orcaflex

PREFIX_ATTACH = ["SKA", "SKB", "SKN", "SKRO", "TOP", "CDA", "PESO"]
OBJ_REMOVE_2ND_DVD = ["Cabrestante 1", "Cabrestante 2", "A/R", "Junção"]
PATHS_MAP = {
    "dir_cases_4_5": "cases_4_5",
    "file_case_3ii": "Dinamico.sim",
    "file_contingency": "Cont1.dat",
    "file_layaway": "Caso3ii_lançamento.dat",
    "file_lançamento": "Caso4_lançamento",
    "file_teste": "Caso4_teste",
    "file_operação": "Caso5_operação",
}

STIFF_CURVE_NAMES = {
    "lan": {"curve_name": "Stiffness_Lançamento"},
    "hid": {"curve_name": "Stiffness_Teste"},
    "ope": {"curve_name": "Stiffness_Operação"},    
}

def split_buoys_and_non_buoys(
        line: orca.OrcaFlexLineObject, prefix_attachments: list,
    ) -> dict:
    """
    Get a dict of two lists of attachments, the first list with 
    non-dead weights or buoys and other list with remaining attchment.
    
    Args:
        line: orcaflex line object.
        prefix_attachments: prefix of the buoys and dead weights.

    Returns:
        dict of two lists:
            "non_buoys_dw" is a list of attachment that are non-dead weights or buoys.
            "buoys_dw" is a list of attachment that are dead weights or buoys.
    """

    non_buoys_dw_list = list()
    buoys_dw_list = list()
    
    for i, atach_type in enumerate(line.AttachmentType):

        attach = {
            "att_name": line.AttachmentName[i],
            "name": line.AttachmentType[i],
            "z": line.Attachmentz[i],
            "relative": line.AttachmentzRelativeTo[i]
        }

        if atach_type.split("_")[0].upper() not in prefix_attachments:
            non_buoys_dw_list.append(attach)
        else: 
            buoys_dw_list.append(attach)

    return {"non_buoys_dw": non_buoys_dw_list, "buoys_dw": buoys_dw_list}

def create_base_link(
        model: orca.Model, line: orca.ObjectType.Line,
    ) -> orca.ObjectType.Link:
    """
    Create a Link object with the reference document (ET) data. 

    Args:
        model: it is the python representation of the model file.
        line: orcaflex line object.

    Returns:
        None
    """

    link = model.CreateObject(orca.ObjectType.Link)
    # Item 5.2.5 of ET
    link.UnstretchedLength = 3.0
    link.Stiffness = 1000.0
    link.EndBConnection = line.Name

    return link

def create_base_buoys3d(model: orca.Model) -> orca.ObjectType.Buoy3D:
    """
    Create a 3D buoys object with the reference document (ET) data. 

    Args:
        model: it is the python representation of the model file.

    Returns:
        None
    """

    buoys_3d = model.CreateObject(orca.ObjectType.Buoy3D)
    buoys_3d.CdX = buoys_3d.CdY = buoys_3d.CdZ = 0.0
    buoys_3d.CaX = buoys_3d.CaY = buoys_3d.CaZ = 0.0
    buoys_3d.DragAreaX = buoys_3d.DragAreaY = buoys_3d.DragAreaZ = 0.0
    buoys_3d.Volume = 1000.0 # 1.0 to make calculations easier
    buoys_3d.Height = 1.7 # Arbitrary value

    return buoys_3d

def update_attachment_list(
        line: orca.OrcaFlexLineObject, attach_list: list,
    ) -> orca.OrcaFlexLineObject:
    """
    Update the line attachment ignoring dead weights and buoys.

    Args:
        line: orcaflex line object.
        attach_list: attachment list - not buoys and not dead weights.

    Returns:
        the orcaflex line object is returned.
    """

    line.NumberOfAttachments = len(attach_list)

    for i, attach in enumerate(attach_list):
        line.AttachmentType[i] = attach["name"]
        line.Attachmentz[i] = attach["z"]
        line.AttachmentzRelativeTo[i] = attach["relative"]

        if attach["att_name"] is not None:
            line.AttachmentName[i] = attach["att_name"]

    return line

def convert_attach_to_3dbuoys(
        model: orca.Model, 
        line: orca.OrcaFlexLineObject, 
        prefix_attachments: list, 
        stage_release_link: int,
    ) -> orca.Model:
    """
    Convert the attachment buoys and dead weights to 3D buoys.

    Args:
        model: it is the python representation of the model file.
        line: orcaflex line object.
        prefix_attachments: prefix of the buoys and dead weights.
        stage_release_link: it is the simulation stage which the buoys will be released.

    Returns:
        orca.Model - it is the model updated after the function is called.
    """

    attach_dict = split_buoys_and_non_buoys(line, prefix_attachments)

    if not attach_dict["buoys_dw"]:
        return model
    
    base_link = create_base_link(model, line)
    base_buoys3d = create_base_buoys3d(model)

    counter = defaultdict(int)
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

    for item in attach_dict["buoys_dw"]:

        attach_type, attach_value = item["name"].split("_")      
        # It is not possible to create objects with the same name
        # counter creates a dict with default values of 0 for any new key.
        item_name = f"{attach_value}_{counter[attach_value]}"
        # add one to item["name"] key 
        counter[attach_value] += 1

        # Convert "," to "." and get a float variable
        attach_value = locale.atof(attach_value)

        # If buoy, buoyancy (+) and "B". If dead weight, weight (-) and "P". 
        prefix, factor = ("B", 1) if "PESO" not in attach_type.upper() else ("P", -1)

        # Calculte the buoys or dead weights mass
        displaced_mass = model.environment.Density * base_buoys3d.Volume
        # attach_value - from kg to Te
        mass = displaced_mass - (factor * (attach_value / 1000))
   
        new_buoys3d = base_buoys3d.CreateClone(name=f"{prefix}{item_name}")
        new_link = base_link.CreateClone(name=f"L{item_name}")
        # Inputs
        new_buoys3d.Mass = mass
        new_link.ReleaseStage = stage_release_link - 1
        new_link.EndAConnection = new_buoys3d.Name
        # Coordinates - the constants are arbitrary to facilitate convergence
        new_buoys3d.InitialZ = model.environment.SeabedOriginZ + 4
        new_link.EndBzRelativeTo = item["relative"] 
        new_link.EndBZ = item["z"]
        new_buoys3d.InitialX = item["z"] + 2
        new_link.EndBX = new_link.EndBY = new_buoys3d.InitialY = 0.0
        
    model.DestroyObject(base_link.Name)
    model.DestroyObject(base_buoys3d.Name)

    line = update_attachment_list(line, attach_dict["non_buoys_dw"])

    return model

def manager_workspace(
        spreadsheet_dir: str, paths: dict, stiff_curves: dict,
    ) -> tuple:
    """
    Manager the folders and files of the workspace.
    - Create the cases 4 and 5 folder. 
    - Get the complete file paths.

    Args:
        spreadsheet_dir: it is the DVC spreadsheet directory.
        paths: it is a dict of folder and file names.
        stiff_curves: it is a dict of stiffness curve names.

    Returns:
        Two dictionaries.
        - First: full paths of the files.
        - Second: stiffness curve name and simulation file paths. 
    """

    # Get the root path
    root_path = os.path.abspath(spreadsheet_dir)

    # Create folder of the cases 4 and 5
    cases_4_5_dir = os.path.join(root_path, paths["dir_cases_4_5"])
    Path(cases_4_5_dir).mkdir(parents=True, exist_ok=True)

    full_paths = dict()

    # Get the Case3ii model FILE
    model_path = os.path.join(root_path, paths["file_case_3ii"])
    model_file = glob.glob(model_path)

    if not  model_file:
        raise ValueError("The case3ii (Dinamico.sim) file was not found!")

    full_paths["file_dynamic"] = model_file[0]
    full_paths["file_contingency"] = os.path.join(root_path, paths["file_contingency"])
    
    full_paths["file_layaway"] = os.path.join(cases_4_5_dir, paths["file_layaway"])

    stiff_curves["lan"]["basename"] = os.path.join(cases_4_5_dir, paths["file_lançamento"])
    stiff_curves["hid"]["basename"] = os.path.join(cases_4_5_dir, paths["file_teste"])
    stiff_curves["ope"]["basename"] = os.path.join(cases_4_5_dir, paths["file_operação"])

    return full_paths, stiff_curves

def generate_contingency_model(file_names: dict) -> None:
    """
    Generate the contingency case.
    Note: this function DOES NOT added contingency buoys in the model.

    Args:
        file_names: it is a dict of the names of the analysis files.

    Returns:
        None
    """
    # Prepare model
    model = orcaflex.load_model(file_names["file_dynamic"])

    # Get winch length
    winch = model["A/R"]
    winch_length = winch.TimeHistory("Length")

    # Before changes the model, set lines to user specified starting shape
    model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)

    # ET - Item 6.4 (Pay AR cable)
    winch.StageValue[0] = winch_length[-1]
    winch.StageValue[-1] = 0

    model.SaveData(file_names["file_contingency"])

    return None

def generate_layaway_model(
        file_names: dict, cvd_type: int, prefix_attachments: list,
    ) -> None:
    """
    Generate the layaway model file.

    Args:
        file_names: it is a dict of the names of the analysis files.
        cvd_type: 1 to 1st dvc and 2 to 2nd dvc.
        prefix_attachments: prefix of the buoys and dead weights.

    Returns:
        None
    """
    # Prepare model
    file_name = os.path.join(os.path.dirname(__file__), "Dinamico.sim")
    model = orca.Model(file_name)

    a_r_cable = model["A/R"]
    top_end_x = a_r_cable.TimeHistory("X", orca.PeriodNum.StaticState, orca.oeWinch(1))
    top_end_z = a_r_cable.TimeHistory("Z", orca.PeriodNum.StaticState, orca.oeWinch(1))       # taking constraint's positions

    line = model["Line"]
    general = model.general

    # ET - Item 6.3 (Simulation stages)
    pay_line_walk_time = 500  # laying_speed * line length (vessel_walk)
    stabilization_time = 50
    n_stages = general.StageCount

    if cvd_type == 1:
        general.StageCount = general.StageCount + 3
        # Do not forget - the first index is 0
        general.StageDuration[n_stages] = pay_line_walk_time
        general.StageDuration[n_stages + 1] = stabilization_time
        general.StageDuration[n_stages + 2] = stabilization_time

        constraint = model.CreateObject(orca.ObjectType.Constraint, "PLSV")     # creating constraint
        constraint.InitialX, constraint.InitialY, constraint.InitialZ = top_end_x, 0, top_end_z     # inputting constraint's positions

        constraint.ConstraintType = "Imposed motion"        # setting constraint's motion
        constraint.TimeHistoryDataSource = "Internal"       # internal source for time history data
        constraint.TimeHistoryInterpolation = "Linear"      # interpolation method for motion

        a_r_cable.Connection[0] = "PLSV"
        a_r_cable.ConnectionX[0], a_r_cable.ConnectionY[0],a_r_cable.ConnectionZ[0] = 0, 0, 0       # connecting A/R to Constraint

        motion = {
            "Time": [8, 2.15, 50, 100, pay_line_walk_time, stabilization_time, stabilization_time],
            "x": [top_end_x, top_end_x, top_end_x, top_end_x, top_end_x + 50, top_end_x + 50, top_end_x + 50],
            "z": [top_end_z, top_end_z, top_end_z, top_end_z, top_end_z, top_end_z, top_end_z],
        }     # Ramping + heave up + stabilization + pay 10m +  pay 50m + stabilization + no buoys

        n = len(motion["Time"])
        constraint.TimeHistoryDataCount = n

        for i in range(n):
            constraint.TimeHistoryDataTime[i] = motion["Time"][i]
            constraint.TimeHistoryDatax[i] = motion["x"][i]
            constraint.TimeHistoryDataz[i] = motion['z'][i]
            if i == 4:
                a_r_cable.StageValue[i] = 50        # pay 50m line in stage 4 (500s)
        
    elif cvd_type == 2:
        general.StageCount = general.StageCount + 2
        # Do not forget - the first index is 0
        general.StageDuration[n_stages] = stabilization_time
        general.StageDuration[n_stages + 1] = stabilization_time

    stage_release_link = general.StageCount
    model = convert_attach_to_3dbuoys(model, line, prefix_attachments, stage_release_link)

    model.SaveData(file_names["file_layaway"])

# ---------------------------------------------------------------------------------------------------
    
# sys.argv[1] - dvc spreadsheet DIRECTORY passed by VBA script
spreadsheet_dir = os.path.dirname(__file__)
# sys.argv[2] - if 1st dvc, 1. If 2nd dvc, 2.
cvd_type = 1
# sys.argv[3] - "layaway" or "cases4_5".
function_name = "layaway"

# Create the cases_4_5 folder. In addition, get the full path of the files.
full_paths, stiff_data = manager_workspace(
    spreadsheet_dir=spreadsheet_dir, 
    paths=PATHS_MAP, 
    stiff_curves=STIFF_CURVE_NAMES,
)

generate_layaway_model(full_paths, cvd_type, PREFIX_ATTACH)
