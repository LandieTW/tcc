"""
Static analysis automation
"""

import OrcFxAPI
import sim_run
from orca import object_elements
from methods import info

rt_number = info[0]
vessel = info[1]
buoy_set = info[2]
rl_config = info[3]
structural_limits = info[4]

model = OrcFxAPI.Model(rt_number + "\\" + rt_number + "_Static.dat")
model_general = model['General']

object_line = object_elements[0]
model_line = model[object_line.name]
model_line_type = model["Line"]

object_bend_restrictor = object_elements[1]
model_bend_restrictor = model[object_bend_restrictor.name]
model_bend_restrictor_type = model["Vert"]

object_end_fitting = object_elements[2]
model_end_fitting = model[object_end_fitting.name]

object_vcm = object_elements[3]
model_vcm = model[object_vcm.name]

if object_bend_restrictor.material == "Polymer":
    object_zr_bend_restrictor = object_elements[4]
    model_zr_bend_restrictor = model[object_zr_bend_restrictor.name]
    if len(object_elements) == 6:
        object_flange = object_elements[5]
        model_flange = model[object_flange.name]
else:
    if len(object_elements) == 5:
        object_flange = object_elements[4]
        model_flange = model[object_flange.name]

model_winch = model["Guindaste"]
model_environment = model["Environment"]
model_stiffness_line = model["Stiffness1"]
model_stiffness_bend_restrictor = model["Stiffness2"]

# RODANDO SEM VÉRTEBRA
model_line_type.NumberOfAttachments = 0
sim_run.run_static_simulation(model, rt_number)
sim_run.user_specified(model, rt_number)

# RODANDO COM A VÉRTEBRA
sim_run.insert_bend_restrictor()
