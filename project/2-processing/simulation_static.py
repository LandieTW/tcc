"""
Static analysis automation

Revisar as fórmulas de rigidezes.

Há um erro na modelagem.
Onde deveria estar colocando o end-fitting, está sendo colocado ZR-vertebra.
Na RT 2517

Há um erro na modelagem.
Na consideração de Adaptador de flange ou ZR-vertebra.
Na RT 3004 e na RT 3024
"""

import OrcFxAPI
import sim_run
from extract import json_data
from orca import model_elements

endfitting = json_data[3]
flange = json_data[4]
rt_number = json_data[7]
vessel = json_data[8]
buoy_set = json_data[9]
buoys_configuration = json_data[10]
structural_limits = json_data[11]

model_aut = OrcFxAPI.Model(rt_number + "\\" + rt_number + "_Static.dat")

general = model_aut['General']
line = model_aut[model_elements[0]]
line_type = model_aut[model_elements[1]]
bend_restrictor = model_aut[model_elements[2]]
end_fitting = model_aut[model_elements[3]]
if json_data[4]["ident_flange"] != "":
    flange_adapter = model_aut[model_elements[4]]
vcm = model_aut[model_elements[5]]
b_restrictor = model_aut['Vert']
winch = model_aut['Guindaste']
environment = model_aut['Environment']
stiffness_1 = model_aut['Stiffness1']
stiffness_2 = model_aut['Stiffness2']

general.LineStaticsStep1Policy = "All lines included"
general.LineStaticsStep2Policy = "None"
general.StaticsMinDamping = 10
general.StaticsMaxDamping = 30

line_type.NumberOfAttachments = 0

sim_run.run_static_simulation(model_aut, rt_number)
print("\nRan without Bend_Restrictor!")
sim_run.user_specified(model_aut, rt_number)

sim_run.insert_bend_restrictor(line_type, b_restrictor, flange, endfitting)

sim_run.run_static_simulation(model_aut, rt_number)
print("\nRan with Bend_Restrictor!")
sim_run.user_specified(model_aut, rt_number)

combination_buoys = sim_run.buoy_combination(buoy_set)
sim_run.loop_input_buoyancy(buoys_configuration, line_type, model_aut, 1,
                            combination_buoys, vessel, rt_number)

selection = sim_run.buoyancy(buoys_configuration, combination_buoys)
treated_buoys = sim_run.buoyancy_treatment(buoys_configuration, selection)
num_buoys = sim_run.number_buoys(treated_buoys)
sim_run.input_buoyancy(line_type, num_buoys, treated_buoys, vessel)

sim_run.run_static_simulation(model_aut, rt_number)
print("\nRan with Bend_Restrictor and Buoys")

print("\nLoop initialization.")
rotation = sim_run.verify_vcm_rotation(vcm)
clearance = sim_run.verify_line_clearance(line_type)

sim_run.loop_initialization(line_type, vcm, model_aut, rotation, clearance,
                            buoy_set, buoys_configuration, vessel,
                            rt_number, False, selection)

print(f"\nEnd of the automation")
rotation = sim_run.verify_vcm_rotation(vcm)
clearance = sim_run.verify_line_clearance(line_type)
