"""
Creates the OrcaFlex model with the data from methods.py
"""

import methods
import OrcFxAPI
import os


def modeling_accessory(obj_model: OrcFxAPI.OrcaFlexObject, obj: methods.Accessory) -> None:
    """
    Model accessory: flange adapter / bend_restrictor's rigid zone
    :param obj_model: accessory in orcaflex
    :param obj: flange object / bend_restrictor's rigid zone object
    :return:
    """
    obj_model.OD = obj.od
    obj_model.ID = obj.id
    obj_model.MassPerUnitLength = obj.lwa
    obj_model.EIx = obj.b_stiffness
    obj_model.EA = obj.a_stiffness
    obj_model.xMinRadius = obj.mbr
    obj_model.NormalDragLiftDiameter = obj.cd
    obj_model.AxialDragLiftDiameter = obj.cd
    obj_model.ContactDiameter = obj.cd
    obj_model.GJ = obj.t_stiffness
    obj_model.Name = obj.name


model = OrcFxAPI.Model("ModeloRTCVD1a.dat")

line = model['Linha']
line_type = model['Line']
bend_restrictor = model['Vértebra']
b_restrictor = model['Vert']
zr_vert = model["ZR_Vertebra"]
end_fitting = model['Conector']
flange = model['Adaptador']
vcm = model['MCV']
winch = model['Guindaste']
environment = model['Environment']
stiffness_1 = model['Stiffness1']
stiffness_2 = model['Stiffness2']

line_object = methods.new_combined_data[0]
bend_restrictor_object = methods.new_combined_data[1]
end_fitting_object = methods.new_combined_data[2]
vcm_object = methods.new_combined_data[3]
winch_length = methods.new_combined_data[4]
list_bathymetric = methods.new_combined_data[5]
height_to_seabed = methods.new_combined_data[6]
rt_number = methods.new_combined_data[7]
vessel = methods.new_combined_data[8]
buoy_set = methods.new_combined_data[9]
buoy_configuration = methods.new_combined_data[10]
structural_limits = methods.new_combined_data[11]
length = methods.new_combined_data[12]

line.OD = line_object.od
line.ID = line_object.id
line.MassPerUnitLength = line_object.eaw
line.ContactDiameter = line_object.cd
line.NormalDragLiftDiameter = line_object.cd
line.AxialDragLiftDiameter = line_object.cd
line.EA = line_object.a_stiffness
line.xMinRadius = line_object.mbr_i
line.GJ = line_object.t_stiffness
line.Name = line_object.name

bend_restrictor.OD = bend_restrictor_object.od
bend_restrictor.ID = bend_restrictor_object.id
bend_restrictor.MassPerUnitLength = bend_restrictor_object.lwa
bend_restrictor.EA = bend_restrictor_object.a_stiffness
bend_restrictor.xMinRadius = bend_restrictor_object.mbr
bend_restrictor.NormalDragLiftDiameter = bend_restrictor_object.cd
bend_restrictor.AxialDragLiftDiameter = bend_restrictor_object.cd
bend_restrictor.ContactDiameter = bend_restrictor_object.cd
bend_restrictor.GJ = bend_restrictor_object.t_stiffness
bend_restrictor.Name = bend_restrictor_object.name

modeling_accessory(end_fitting, end_fitting_object)

line_type.Length[0] = line_object.lda - length  #
line_type.Length[5] = bend_restrictor_object.length  #
line_type.Length[6] = end_fitting_object.length  #

if len(methods.new_combined_data) == 15:
    flange_object = methods.new_combined_data[13]
    rz_object = methods.new_combined_data[14]
    modeling_accessory(flange, flange_object)
    modeling_accessory(zr_vert, rz_object)
elif len(methods.new_combined_data) == 14:
    if bend_restrictor_object.material == "Polymer":
        rz_object = methods.new_combined_data[13]
        modeling_accessory(zr_vert, rz_object)
    else:
        flange_object = methods.new_combined_data[13]
        modeling_accessory(flange, flange_object)

if flange:
    line_type.Length[7] = dict_flange["length_flange"] / 1_000
    line_type.Attachmentz[0] = (dict_end_fitting["length_end_fitting"] + dict_flange["length_flange"]) / 1_000
else:
    line_type.NumberOfSections = 7
    line_type.LineType[6] = end_fitting.Name
    line_type.Attachmentz[0] = end_fitting_object.length

vcm.Mass = dict_vcm["wt_sw_vcm"] / 1_000
vcm.Height = dict_vcm["olhal_cz"]
vcm.InitialZ = - height_to_seabed
vcm.CentreOfMassX = dict_vcm["cg_bx"]
vcm.CentreOfMassZ = dict_vcm["cg_az"]
vcm.CentreOfVolumeX = dict_vcm["cg_bx"]
vcm.CentreOfVolumeZ = dict_vcm["cg_az"]
vcm.Name = vcm_object.name

line_type.EndBX = dict_vcm["flange_fx"]
line_type.EndBZ = dict_vcm["flange_ez"]
line_type.EndBDeclination = dict_vcm["declination"]

b_restrictor.Length = bend_restrictor_object.length

winch.ConnectionX[1] = dict_vcm["olhal_dx"]
winch.ConnectionZ[1] = dict_vcm["olhal_cz"]
winch.StageValue[0] = winch_length

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
                  end_fitting.name, flange.name, vcm.name,
                  b_restrictor.name, winch.name, environment.name,
                  stiffness_1.name, stiffness_2.name)
