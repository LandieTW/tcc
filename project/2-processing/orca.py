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
rt_number = methods.new_combined_data[6]
vessel = methods.new_combined_data[7]
buoy_set = methods.new_combined_data[8]
buoy_configuration = methods.new_combined_data[9]
structural_limits = methods.new_combined_data[10]
length = methods.new_combined_data[11]

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

vcm.Mass = vcm_object.weight
vcm.Height = vcm_object.cg_az
vcm.InitialZ = vcm_object.hts  # height to seabed
vcm.CentreOfMassX = vcm_object.cg_bx
vcm.CentreOfMassZ = vcm_object.cg_az
vcm.CentreOfVolumeX = vcm_object.cg_bx
vcm.CentreOfVolumeZ = vcm_object.cg_az
vcm.Name = vcm_object.name

line_type.Length[0] = line_object.lda - length  #
line_type.Length[5] = bend_restrictor_object.length  #
line_type.Length[6] = end_fitting_object.length  #

if bend_restrictor_object.material == "Polymer":
    rz_object = methods.new_combined_data[12]
    modeling_accessory(zr_vert, rz_object)
    if len(methods.new_combined_data) == 13:  # então tem rigid_zone e n tem flange_adapter
        line_type.NumberOfSections = 8
        line_type.Attachmentz[0] = end_fitting_object.length + rz_object.length
    else:  # tem rigid_zone e tem flange_adapter
        flange_object = methods.new_combined_data[13]
        modeling_accessory(flange, flange_object)
        line_type.Attachmentz[0] = (end_fitting_object.length + flange_object.length +
                                    rz_object.length)
else:
    if len(methods.new_combined_data) == 13:  # n tem rigid_zone, mas tem flange_adapter
        flange_object = methods.new_combined_data[12]
        modeling_accessory(flange, flange_object)
        line_type.NumberOfSections = 8
        line_type.Attachmentz[0] = flange_object.length
        line_type.LineType[6] = end_fitting.name
        line_type.LineType[7] = flange.name
    else:  # n tem rigid zone e n tem flange_adapter
        line_type.NumberOfSections = 7
        line_type.Attachmentz[0] = end_fitting_object.length
        line_type.LineType[6] = end_fitting.name

line_type.EndBX = vcm_object.flange_fx
line_type.EndBZ = vcm_object.flange_ez
line_type.EndBDeclination = vcm_object.declination

b_restrictor.Length = bend_restrictor_object.length

winch.ConnectionX[1] = vcm_object.olhal_dx
winch.ConnectionZ[1] = vcm_object.olhal_cz
winch.StageValue[0] = winch_length

stiffness_1.NumberOfRows = len(line_object.curvature)
for i in range(1, len(line_object.curvature)):
    stiffness_1.IndependentValue[i] = line_object.curvature[i]
    stiffness_1.DependentValue[i] = line_object.b_moment[i]

environment.SeabedType = "Profile"
environment.SeabedProfileDepth[0] = line_object.lda
environment.SeabedProfileNumberOfPoints = len(list_bathymetric[0])
for i in range(len(list_bathymetric[1])):
    environment.SeabedProfileDistanceFromSeabedOrigin[i] = list_bathymetric[0][i]
    environment.SeabedProfileDepth[i] = list_bathymetric[2][i]

stiffness_2.NumberOfRows = len(bend_restrictor_object.curvature)
for i in range(1, len(bend_restrictor_object.curvature)):
    stiffness_2.IndependentValue[i] = bend_restrictor_object.curvature[i]
    stiffness_2.DependentValue[i] = bend_restrictor_object.b_moment[i]

os.makedirs(rt_number, exist_ok=True)
model.SaveData(rt_number + "\\" + rt_number + "_Static.dat")

model_elements = (line.name, line_type.name, bend_restrictor.name,
                  end_fitting.name, flange.name, vcm.name,
                  b_restrictor.name, winch.name, environment.name,
                  stiffness_1.name, stiffness_2.name)
