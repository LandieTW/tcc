"""
Static analysis automation
"""

import OrcFxAPI
# import time
import sim_run
from orca import object_elements
from methods import info


# start_time = time.perf_counter()

rt_number = info[0]
vessel = info[1]
buoy_set = info[2]
rl_config = info[3]

model = OrcFxAPI.Model(rt_number + "\\" + rt_number + "_Static.dat")
model_general = model['General']

len_obj_pack = len(object_elements)

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

model_winch = model["Guindaste"]
model_environment = model["Environment"]
model_stiffness_line = model["Stiffness1"]
model_stiffness_bend_restrictor = model["Stiffness2"]

print("\nRunning without bend_restrictor")

model_line_type.NumberOfAttachments = 0

sim_run.run_static(model, rt_number, model_vcm, model_line_type, object_line, object_vcm,
                   model_general)
sim_run.user_specified(model, rt_number)

print("\nRunning with bend_restrictor")

model_line_type.NumberOfAttachments = 1
model_line_type.AttachmentType[0] = model_bend_restrictor_type.Name

bend_restrictor_ini_position = object_end_fitting.length

if object_bend_restrictor.material == "Polymer":
    object_zr_bend_restrictor = object_elements[4]
    model_zr_bend_restrictor = model[object_zr_bend_restrictor.name]
    if len_obj_pack == 6:  # EF + RZ + Flange
        object_flange = object_elements[5]
        model_flange = model[object_flange.name]
        bend_restrictor_ini_position += (object_zr_bend_restrictor.length + object_flange.length)
    else:  # EF + RZ
        bend_restrictor_ini_position += object_zr_bend_restrictor.length
else:
    if len_obj_pack == 5:  # EF + Flange
        object_flange = object_elements[4]
        model_flange = model[object_flange.name]
        bend_restrictor_ini_position += object_flange.length

model_line_type.Attachmentz[0] = bend_restrictor_ini_position
model_line_type.AttachmentzRelativeTo[0] = "End B"

sim_run.run_static(model, rt_number, model_vcm, model_line_type, object_line, object_vcm,
                   model_general)
sim_run.user_specified(model, rt_number)

print("\nRunning with buoys")

buoy_combination = sim_run.buoy_combination(buoy_set)
selection = {}

print("\nPartially adding buoyancy")
k = 1
while k <= 5:
    rl_config_fract = [rl_config[0], [round(k * x / 5, 0)
                                      for x in rl_config[1]]]
    selection = sim_run.buoyancy(rl_config_fract, buoy_combination)
    treated_buoys = sim_run.buoyancy_treatment(rl_config_fract, selection)
    num_buoys = sim_run.number_buoys(treated_buoys)
    sim_run.input_buoyancy(model_line_type, num_buoys, treated_buoys, vessel)
    print(f"\nPartial buoyancy: {rl_config_fract[1]}")
    sim_run.run_static(model, rt_number, model_vcm, model_line_type, object_line, object_vcm,
                       model_general)
    sim_run.user_specified(model, rt_number)
    k += 1

print("\nAutomation's start.")
sim_run.looping(model_line_type, selection, model, rt_number, vessel, rl_config, buoy_set,
                model_vcm, object_line, object_vcm, model_winch, model_general)

print(f"\n Automation's end.")

# Sugestão: utilizar o damping informado na ET.
# Sugestão: Ao invés de usar o temporizador, utilizar a quantidade de interações que o orcaflex
# executa em um comando run_static.
# Colocar a função run_static dentro de uma condição try/Exception ⇾ Tratar em caso de exceção.
