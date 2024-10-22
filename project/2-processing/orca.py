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
b_restrictor = model['Vert']
zr_vert = model["ZR_Vertebra"]
end_fitting = model['Conector']
flange_adapter = model['Adaptador']
vcm = model['MCV']
winch = model['Guindaste']
environment = model['Environment']
stiffness_1 = model['Stiffness1']
stiffness_2 = model['Stiffness2']

line_object = new_combined_data[0]
bend_restrictor_object = new_combined_data[1]
end_fitting_object = new_combined_data[2]
vcm_object = new_combined_data[3]
winch_length = new_combined_data[4]
list_bathymetric = new_combined_data[5]
height_to_seabed = new_combined_data[6]
rt_number = new_combined_data[7]
vessel = new_combined_data[8]
buoy_set = new_combined_data[9]
buoy_configuration = new_combined_data[10]
structural_limits = new_combined_data[11]
length = new_combined_data[12]

line.OD = line_object.od
line.ID = line_object.id
line.MassPerUnitLength = line_object.eaw
line.ContactDiameter = line_object.cd
line.NormalDragLiftDiameter = line_object.cd
line.AxialDragLiftDiameter = line_object.cd
line.EA = line_object.a_stiffness
line.xMinRadius = line_object.mbr_i
line.GJ = line_object.t_stiffness

bend_restrictor.OD = bend_restrictor_object.od
bend_restrictor.ID = bend_restrictor_object.id
bend_restrictor.MassPerUnitLength = bend_restrictor_object.lwa
bend_restrictor.EA = bend_restrictor_object.a_stiffness
bend_restrictor.xMinRadius = bend_restrictor_object.mbr
bend_restrictor.NormalDragLiftDiameter = bend_restrictor_object.cd
bend_restrictor.AxialDragLiftDiameter = bend_restrictor_object.cd
bend_restrictor.ContactDiameter = bend_restrictor_object.cd
bend_restrictor.GJ = bend_restrictor_object.t_stiffness

end_fitting.OD = end_fitting_object.od
end_fitting.ID = end_fitting_object.id
end_fitting.MassPerUnitLength = end_fitting_object.lwa
end_fitting.EIx = end_fitting_object.b_stiffness
end_fitting.EA = end_fitting_object.a_stiffness
end_fitting.xMinRadius = bend_restrictor_object.mbr  # igual ao da vertebra
end_fitting.NormalDragLiftDiameter = end_fitting_object.cd
end_fitting.AxialDragLiftDiameter = end_fitting_object.cd
end_fitting.ContactDiameter = end_fitting_object.cd
end_fitting.GJ = end_fitting_object.t_stiffness

line_type.Length[0] = line_object.lda - length
line_type.Length[5] = bend_restrictor_object.length
line_type.Length[6] = end_fitting_object.length

if len(new_combined_data) > 15:  # adaptador de flange
    dict_flange = new_combined_data[5]
    length = new_combined_data[6]
    dict_vcm = new_combined_data[7]
    winch_length = new_combined_data[8]
    list_bathymetric = new_combined_data[9]
    height_to_seabed = new_combined_data[10]
    rt_number = new_combined_data[11]

    flange_adapter.OD = dict_flange["outside_diameter_flange"]
    flange_adapter.ID = dict_flange["id_flange"] / 1_000
    flange_adapter.MassPerUnitLength = dict_flange["linear_weight_in_air_flange"]
    flange_adapter.EIx = dict_flange["bending_stiffness_flange"]
    flange_adapter.EA = dict_flange["axial_stiffness_flange"]
    flange_adapter.xMinRadius = dict_bend_restrictor["locking_mbr_bend_restrictor"]
    flange_adapter.NormalDragLiftDiameter = (dict_flange["contact_diameter_flange"] / 1_000)
    flange_adapter.AxialDragLiftDiameter = (dict_flange["contact_diameter_flange"] / 1_000)
    flange_adapter.ContactDiameter = (dict_flange["contact_diameter_flange"] / 1_000)
    flange_adapter.GJ = dict_flange["torsional_stiffness_flange"]
    flange_adapter.Name = dict_flange["ident_flange"]
    line_type.Length[7] = dict_flange["length_flange"] / 1_000
    line_type.Attachmentz[0] = (dict_end_fitting["length_end_fitting"] + dict_flange["length_flange"]) / 1_000
else:
    line_type.NumberOfSections = 7
    line_type.LineType[6] = end_fitting.Name
    line_type.Attachmentz[0] = dict_end_fitting["length_end_fitting"] / 1_000

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
    stiffness_1.DependentValue[i] = (list_curvature_bend_moment_line[1][i] / 1_000)

environment.SeabedType = "Profile"
environment.SeabedProfileDepth[0] = dict_line["water_depth"]
environment.SeabedProfileNumberOfPoints = len(list_bathymetric[0])
for i in range(len(list_bathymetric[1])):
    environment.SeabedProfileDistanceFromSeabedOrigin[i] = list_bathymetric[0][i]
    environment.SeabedProfileDepth[i] = list_bathymetric[2][i]

for i in range(1, len(list_curvature_bend_moment_bend_restrictor[0])):
    stiffness_2.IndependentValue[i] = list_curvature_bend_moment_bend_restrictor[0][i]
    stiffness_2.DependentValue[i] = list_curvature_bend_moment_bend_restrictor[1][i]

os.makedirs(rt_number, exist_ok=True)
model.SaveData(rt_number + "\\" + rt_number + "_Static.dat")

model_elements = (line.name, line_type.name, bend_restrictor.name,
                  end_fitting.name, flange_adapter.name, vcm.name,
                  b_restrictor.name, winch.name, environment.name,
                  stiffness_1.name, stiffness_2.name)
