"""
Creates the OrcaFlex model with the data from methods.py
"""

from methods import new_combined_data
import OrcFxAPI
import os

model = OrcFxAPI.Model("ModeloRTCVD1a.dat")

line = model['Linha']
line_type = model['Line']
bend_restrictor = model['Vértebra']
end_fitting = model['Conector']
flange_adapter = model['Adaptador']
vcm = model['MCV']
b_restrictor = model['Vert']
winch = model['Guindaste']
environment = model['Environment']
stiffness_1 = model['Stiffness1']
stiffness_2 = model['Stiffness2']

dict_line = new_combined_data[0]
list_curvature_bend_moment_line = new_combined_data[1]
dict_bend_restrictor = new_combined_data[2]
list_curvature_bend_moment_bend_restrictor = new_combined_data[3]
dict_end_fitting = new_combined_data[4]
length = new_combined_data[5]
dict_vcm = new_combined_data[6]
winch_length = new_combined_data[7]
list_bathymetric = new_combined_data[8]
height_to_seabed = new_combined_data[9]
rt_number = new_combined_data[10]

line.OD = dict_line["outside_diameter_line"]
line.ID = dict_line["interior_diameter_line"]
line.MassPerUnitLength = dict_line["wt_air_line"] / 1_000
line.ContactDiameter = dict_line["contact_diameter_line"] / 1_000
line.NormalDragLiftDiameter = dict_line["contact_diameter_line"] / 1_000
line.AxialDragLiftDiameter = dict_line["contact_diameter_line"] / 1_000
line_type.Length[0] = winch_length - length
line_type.Length[5] = dict_bend_restrictor["length_bend_restrictor"] / 1_000
bend_restrictor.OD = dict_bend_restrictor["outside_diameter_bend_restrictor"]
bend_restrictor.ID = dict_bend_restrictor["id_bend_restrictor"] / 1_000
bend_restrictor.MassPerUnitLength = dict_bend_restrictor[
    "linear_weight_in_air_bend_restrictor"]
line_type.Length[6] = dict_end_fitting["length_end_fitting"] / 1_000
end_fitting.OD = dict_end_fitting["outside_diameter_end_fitting"]
end_fitting.ID = dict_end_fitting["id_end_fitting"] / 1_000
end_fitting.MassPerUnitLength = (
    dict_end_fitting)["linear_weight_in_air_end_fitting"]
line.EA = dict_line["axial_stiffness_line"]
bend_restrictor.EA = dict_bend_restrictor["axial_stiffness_bend_restrictor"]
end_fitting.EIx = dict_end_fitting["bending_stiffness_end_fitting"]
end_fitting.EA = dict_end_fitting["axial_stiffness_end_fitting"]
line.xMinRadius = dict_line["mbr_installation_line"]
bend_restrictor.xMinRadius = (
    dict_bend_restrictor)["locking_mbr_bend_restrictor"]
end_fitting.xMinRadius = dict_bend_restrictor["locking_mbr_bend_restrictor"]
bend_restrictor.NormalDragLiftDiameter = (
        dict_bend_restrictor["contact_diameter_bend_restrictor"] / 1_000)
end_fitting.NormalDragLiftDiameter = (
        dict_end_fitting["contact_diameter_end_fitting"] / 1_000)
bend_restrictor.AxialDragLiftDiameter = (
        dict_bend_restrictor["contact_diameter_bend_restrictor"] / 1_000)
end_fitting.AxialDragLiftDiameter = (
        dict_end_fitting["contact_diameter_end_fitting"] / 1_000)
bend_restrictor.ContactDiameter = (
        dict_bend_restrictor["contact_diameter_bend_restrictor"] / 1_000)
end_fitting.ContactDiameter = (
        dict_end_fitting["contact_diameter_end_fitting"] / 1_000)
bend_restrictor.GJ = dict_bend_restrictor[
    "torsional_stiffness_bend_restrictor"]
end_fitting.GJ = dict_end_fitting["torsional_stiffness_end_fitting"]
line.GJ = dict_line["torsional_stiffness_line"]
line_type.NumberOfSections = 7
line_type.Attachmentz[0] = dict_end_fitting["length_end_fitting"] / 1_000

if len(new_combined_data) > 15:
    dict_flange = new_combined_data[5]
    length = new_combined_data[6]
    dict_vcm = new_combined_data[7]
    winch_length = new_combined_data[8]
    list_bathymetric = new_combined_data[9]
    height_to_seabed = new_combined_data[10]
    rt_number = new_combined_data[11]

    flange_adapter.OD = dict_flange["outside_diameter_flange"]
    flange_adapter.ID = dict_flange["id_flange"] / 1_000
    flange_adapter.MassPerUnitLength = dict_flange[
        "linear_weight_in_air_flange"]
    flange_adapter.EIx = dict_flange["bending_stiffness_flange"]
    flange_adapter.EA = dict_flange["axial_stiffness_flange"]
    flange_adapter.xMinRadius = dict_bend_restrictor[
        "locking_mbr_bend_restrictor"]
    flange_adapter.NormalDragLiftDiameter = (
            dict_flange["contact_diameter_flange"] / 1_000)
    flange_adapter.AxialDragLiftDiameter = (
            dict_flange["contact_diameter_flange"] / 1_000)
    flange_adapter.ContactDiameter = (
            dict_flange["contact_diameter_flange"] / 1_000)
    flange_adapter.GJ = dict_flange["torsional_stiffness_flange"]
    flange_adapter.Name = dict_flange["ident_flange"]
    line_type.Length[7] = dict_flange["length_flange"]
    line_type.Attachmentz[0] = (dict_end_fitting["length_end_fitting"] +
                                dict_flange["length_flange"]) / 1_000

vcm.Mass = dict_vcm["wt_sw_vcm"] / 1_000
vcm.Height = dict_vcm["olhal_cz"]
vcm.InitialZ = - height_to_seabed
vcm.CentreOfMassX = dict_vcm["cg_bx"]
vcm.CentreOfMassZ = dict_vcm["cg_az"]
vcm.CentreOfVolumeX = dict_vcm["cg_bx"]
vcm.CentreOfVolumeZ = dict_vcm["cg_az"]
line_type.EndBX = dict_vcm["flange_fx"]
line_type.EndBZ = dict_vcm["flange_ez"]
line_type.EndBDeclination = dict_vcm["declination"]
b_restrictor.Length = dict_bend_restrictor["length_bend_restrictor"] / 1_000
winch.ConnectionX[1] = dict_vcm["olhal_dx"]
winch.ConnectionZ[1] = dict_vcm["olhal_cz"]
winch.StageValue[0] = winch_length
line.Name = dict_line["ident_line"]
bend_restrictor.Name = dict_bend_restrictor["ident_bend_restrictor"]
end_fitting.Name = dict_end_fitting["ident_end_fitting"]
vcm.Name = dict_vcm["subsea_equipment"]
stiffness_1.NumberOfRows = len(list_curvature_bend_moment_line[0])
for i in range(1, len(list_curvature_bend_moment_line[0])):
    stiffness_1.IndependentValue[i] = list_curvature_bend_moment_line[0][i]
    stiffness_1.DependentValue[i] = (
            list_curvature_bend_moment_line[1][i] / 1_000)
environment.SeabedType = "Profile"
environment.SeabedProfileDepth[0] = dict_line["water_depth"]
environment.SeabedProfileNumberOfPoints = len(list_bathymetric[0])
for i in range(len(list_bathymetric[1])):
    environment.SeabedProfileDistanceFromSeabedOrigin[i] = (
        list_bathymetric)[0][i]
    environment.SeabedProfileDepth[i] = list_bathymetric[2][i]
for i in range(1, len(list_curvature_bend_moment_bend_restrictor[0])):
    stiffness_2.IndependentValue[i] = \
        list_curvature_bend_moment_bend_restrictor[0][i]
    stiffness_2.DependentValue[i] = \
        list_curvature_bend_moment_bend_restrictor[1][i]

model_elements = (line.name, line_type.name, bend_restrictor.name,
                  end_fitting.name, flange_adapter.name, vcm.name,
                  b_restrictor.name, winch.name, environment.name,
                  stiffness_1.name, stiffness_2.name)

os.makedirs(rt_number, exist_ok=True)
model.SaveData(rt_number + "\\" + rt_number + "_Static.dat")
