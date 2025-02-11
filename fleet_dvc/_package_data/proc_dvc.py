"""Module to generate the DVC cases 4 and 5."""

__author__ = ["Mauro Rodrigues", "Yan Nascimento"]
__copyright__ = "TechnipFMC"
__credits__ = ""
__license__ = ""
__version__ = "2.0"
__maintainer__ = ["Matheus Amaral", "Yan Nascimento"]
__email__ = [
    "matheus.amaral@technipfmc.com",
    "yan.donascimento@technipfmc.com",
]
__status__ = "Under Developement"
__last_release__ = "February, 2025"

"""Reference Document: ET-3000.00-1500-941-PMU-006 - Rev C"""

# Public(Python) Libraries
import os
import sys
import glob
import time
import locale
import OrcFxAPI as orca
from pathlib import Path
from collections import defaultdict
# Private(IAS) Libraries
from utils import orcaflex

# Constants
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

######## ATTENTION - IT IS NOT NECESSARY TO CHANGE ANYTHING FROM HERE #########

"""General Functions"""

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

"""Cases 4 and 5 Functions"""

def get_buoys3d(model: orca.Model) -> list:
    """
    Get the buoys/dead weight list.

    Args:
        model: it is the python representation of the model file.

    Returns:
        list of links.
    """
    
    obj_type = orca.ObjectType.Buoy3D.value
    obj_list = orcaflex.search_objects(model, pattern="B*", obj_type=obj_type)
    obj_list.extend(orcaflex.search_objects(model, pattern="P*", obj_type=obj_type))

    return obj_list

def get_links(model: orca.Model) -> list:
    """
    Get the link list of buoys.

    Args:
        model: it is the python representation of the model file.

    Returns:
        list of links.
    """
    
    obj_type = orca.ObjectType.Link.value
    return orcaflex.search_objects(model, pattern="L*", obj_type=obj_type)

def update_coordinates_buoys3d(model: orca.Model, coord_buoys3d: dict) -> orca.Model:
    """
    Update the 3D buoys coordinates.

    Args:
        model: it is the python representation of the model file.
        coord_buoys3d: a dict of the 3D buoys coordinates

    Returns:
        orca.Model - it is the model updated after the function is called.
    """

    for key in coord_buoys3d.keys():
        obj = model[key]
        obj.InitialX = coord_buoys3d[key]["X"]
        obj.InitialY = coord_buoys3d[key]["Y"]
        obj.InitialZ = coord_buoys3d[key]["Z"]

    return model

def get_buoys3d_coordinates(model: orca.Model) -> dict:
    """
    Get the 3D buoys coordinates.

    Args:
        model: it is the python representation of the model file.

    Returns:
        a dict of the coordinates
    """

    buoys3d = get_buoys3d(model)
    buoys3d_dict = dict()

    for item in buoys3d:
        obj = model[item.Name]
        buoys3d_dict[obj.Name] = {
            "X": obj.InitialX, "Y": obj.InitialY, "Z": obj.InitialZ,
        }
    
    return buoys3d_dict

def remove_release_links(model: orca.Model) -> orca.Model:
    """
    Remove the release of links - change for the default value.

    Args:
        model: it is the python representation of the model file.

    Returns:
        orca.Model - it is the model updated after the function is called.
    """

    links = get_links(model)

    for item in links:
        # Default value of ReleaseStage
        model[item.Name].ReleaseStage = orca.OrcinaDefaultWord

    return model

def remove_buoys_dead_weights(model: orca.Model) -> orca.Model:
    """
    Remove the buoys and dead weights - Links and Buoys3D.

    Args:
        model: it is the python representation of the model file.

    Returns:
        orca.Model - it is the model updated after the function is called.
    """

    obj_list = get_buoys3d(model)
    obj_list.extend(get_links(model))

    for item in obj_list:
        model.DestroyObject(model[item.Name])
    
    return model

def create_filename(filename: str, has_buoys: bool) -> str:
    """
    Get the orcaflex filename.

    Args:
        filename: it is the filename without the extension and the suffix.
        has_buoys: bool to indicate whether it has buoys or not.

    Returns:
        the orcaflex line object is returned.
    """

    if has_buoys:
        return f"{filename}_comflut.dat"
    else:
        return f"{filename}_semflut.dat"

def change_stiffness(
        model: orca.Model, 
        flex_linetype: orca.ObjectType.LineType, 
        stiff_data: dict, 
        has_buoys: bool = True,
    ) -> None:
    """
    This function updates the stiffness curve and replace the line EIx value.

    Args:
        model: it is the python representation of the model file.
        flex_linetype: it is the flexible linetype.
        stiff_data: it is a dict of the curve names and the simulation file paths. 
        has_buoys: if the simulation has buoys or not.

    Returns:
        None
    """
    root_path = os.path.dirname(model.latestFileName)
    base_filename = create_filename(stiff_data["basename"], has_buoys)
    filename = os.path.join(root_path, base_filename)

    flex_linetype.EIx = stiff_data["curve_name"]
    model[stiff_data["curve_name"]].Hysteretic = "No"

    model.SaveData(filename)   

    return None

def generate_cases_4_5(
        model_file: str,
        cvd_type: int,
        stiffness_dict: dict,
        obj_to_remove: list,
    ) -> None:
    """
    Generate the cases 4 and 5 - ET of DVC.

    Args:
        model_file: it is the orcaflex model file (layaway).
        cvd_type: 1 to 1st dvc and 2 to 2nd dvc.
        stiffness_dict: it is a dict of curve and filename of each case.
        obj_to_remove: object list to remove from the 2nd DVC model.

    Returns:
        None
    """

    sim_file = model_file.replace("dat", "sim")

    model = orcaflex.load_model(sim_file)

    if "SimulationStopped" not in model.state.name:
        raise AttributeError("É preciso rodar a análise dinâmica para gerar os casos 4 e 5.")

    coordinates_buoys3d = get_buoys3d_coordinates(model)

    # Before changes the model, set lines to user specified starting shape
    model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)

    line = model["Line"]
    general = model.general

    # ET - Item 6.4 (Update Line)
    line.FullStaticsTolerance = 10
    # To avoid moving the line
    line.StaticsStep2 = "None" 
    general.WholeSystemStaticsEnabled = "No" 

    # ET - Item 6.4 (Update General)
    general.StageCount = 2
    general.StageDuration[1] = 50

    # Remove objects - both dvc types
    cw = model["Guindaste"]
    model.DestroyObject(cw)

    if cvd_type == 2:
        # Remove objects - only 2nd dvc
        for item in obj_to_remove:
            model.DestroyObject(model[item])

    model = remove_release_links(model)
    model = update_coordinates_buoys3d(model, coordinates_buoys3d)

    # Get the flexible linetype
    flex_linetype = model[line.LineType[0]]

    for flut in [True, False]:

        # Case 4 - Laying case (Hysteretic disabled)
        change_stiffness(model, flex_linetype, stiffness_dict["lan"], flut)

        # Case 4 - Hydrostatic case (Hysteretic disabled)
        change_stiffness(model, flex_linetype, stiffness_dict["hid"], flut)

        # Remove buoys and dead weights for the next loop - links and Buoys 3D
        model = remove_buoys_dead_weights(model) 

    # Case 5 - Operation case (Hysteretic disabled)
    change_stiffness(model, flex_linetype, stiffness_dict["ope"], False)

    return None

"""Contigency Functions"""

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

"""Layaway Functions"""

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

def create_constraint(
        model: orca.Model, 
        ar_cable: orca.ObjectType.Winch,
        top_coord: tuple,
        pay_line_stage: int, 
        pay_line_length: int,
    ) -> orca.Model:
    """
    ????????????????????????????????????????????????????????????????????????????????????????????????????????????

    Args:
        model: it is the python representation of the model file.

    Returns:
        orca.Model - it is the model updated after the function is called.
    """

    # Create constraint
    constraint = model.CreateObject(orca.ObjectType.Constraint, "PLSV") 
     
    # Constraint parameters
    constraint.InitialX, constraint.InitialY, constraint.InitialZ = top_coord
    constraint.ConstraintType = "Imposed motion"
    constraint.TimeHistoryDataSource = "Internal"
    constraint.TimeHistoryInterpolation = "Linear"

    # AR position
    ar_cable.Connection[0] = "PLSV"
    ar_cable.ConnectionX[0] = ar_cable.ConnectionY[0] = ar_cable.ConnectionZ[0] = 0

    # Constraint - Time history data
    n_stages = model.general.StageCount
    constraint.TimeHistoryDataCount = n_stages
    # All indexes of TimeHistoryDataz will be assigned the same value
    constraint.TimeHistoryDataz = [constraint.InitialZ] * n_stages
    constraint.TimeHistoryDatax[pay_line_stage:] = [constraint.InitialX]
    constraint.TimeHistoryDatax[:pay_line_stage] = [constraint.InitialX + pay_line_length]

    for i in range(n_stages):
        constraint.TimeHistoryDataTime[i] = model.general.StageEndTime[i]

    return model

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
    model = orcaflex.load_model(file_names["file_dynamic"])

    line = model["Line"]
    ar_cable = model["A/R"]
    # Get constraint's positions
    top_end_x = ar_cable.TimeHistory("X", orca.PeriodNum.StaticState, orca.oeWinch(1))
    top_end_z = ar_cable.TimeHistory("Z", orca.PeriodNum.StaticState, orca.oeWinch(1))
    top_coord = (top_end_x, 0, top_end_z)

    # ET - Item 6.3 - Simulation stages
    n_stages = model.general.StageCount
    stage_dur = model.general.StageDuration
    # Stage 4 - Laying line
    stabilization_time = 50
    pay_line_stage = n_stages + 1
    pay_line_time = 500
    pay_line_length = 50

    if cvd_type == 1:
        # Update the simulation stages
        model.general.StageCount = n_stages + 3
        # Do not forget - the first index is 0
        stage_dur[n_stages] = stage_dur[n_stages + 2] = stabilization_time
        stage_dur[pay_line_stage] = pay_line_time # laying_speed * line length
        ar_cable.StageValue[pay_line_stage] = pay_line_length # Pay line - 50m
        # Create Constraint
        model = create_constraint(model, ar_cable, top_coord, pay_line_stage, pay_line_length)
    elif cvd_type == 2:
        # Update the simulation stages
        model.general.StageCount = n_stages + 2
        # Do not forget - the first index is 0
        stage_dur[n_stages + 1] = stage_dur[n_stages] = stabilization_time
        model["Cabrestante 1"].ReleaseStage = n_stages
        model["Cabrestante 2"].ReleaseStage = n_stages

    model = convert_attach_to_3dbuoys(model, line, prefix_attachments, model.general.StageCount)

    model.SaveData(file_names["file_layaway"])

if __name__ == "__main__":

    """
    To run manually, replace sys.argv[1] with the dvc spreadsheet directory.
    Besides this, replace sys.argv[2] to the dvc type (boolean value).
    """
    
    if len(sys.argv) <= 1:
        raise ValueError("Inputs not found! Check the VBA code.")
    
    # sys.argv[1] - dvc spreadsheet DIRECTORY passed by VBA script
    spreadsheet_dir = sys.argv[1]
    # sys.argv[2] - if 1st dvc, 1. If 2nd dvc, 2.
    cvd_type = int(sys.argv[2])
    # sys.argv[3] - "layaway" or "cases4_5".
    function_name = sys.argv[3]

    print("Please wait, the cases are being created.")

    # Create the cases_4_5 folder. In addition, get the full path of the files.
    full_paths, stiff_data = manager_workspace(
        spreadsheet_dir=spreadsheet_dir, 
        paths=PATHS_MAP, 
        stiff_curves=STIFF_CURVE_NAMES,
    )

    if function_name.upper() in "LAYAWAY":
        # Generate the contingency BASE model
        generate_contingency_model(full_paths)
        # Generate the layaway model
        generate_layaway_model(full_paths, cvd_type, PREFIX_ATTACH)
    elif function_name.upper() in "CASES4_5":
        # Generate the cases 4 and 5 models
        generate_cases_4_5(
            model_file=full_paths["file_layaway"],
            cvd_type=cvd_type,
            stiffness_dict=stiff_data,
            obj_to_remove=OBJ_REMOVE_2ND_DVD,
        )

    print("The cases were created.")
    time.sleep(2)
