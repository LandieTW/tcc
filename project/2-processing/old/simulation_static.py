"""
Static analysis automation
"""

import OrcFxAPI
import simulation
from extract import json_data
from orca import model_elements

print("""-----------------------------""")

model_aut = OrcFxAPI.Model(simulation.rt_number + "\\" +
                           simulation.rt_number + "_Static.dat")

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
general.LineStaticsStep2Policy = "Solve coupled systems"
general.StaticsMinDamping = 10
general.StaticsMaxDamping = 100
line_type.NumberOfAttachments = 0

simulation.run_static_simulation(model_aut)
print("\nRan without Bend_Restrictor!")

simulation.user_specified(model_aut)

simulation.insert_bend_restrictor(line_type, b_restrictor)

simulation.run_static_simulation(model_aut)
print("\nRan with Bend_Restrictor!")

simulation.user_specified(model_aut)

# buoys_set = build the first buoy_set
# select = returns the first buoy_set in a dict format
# next_comb = returns the possible combinations, excluding the actual buoy_set
next_comb, buoys_set, select = simulation.next_combination(
    simulation.first_buoys_set, simulation.n_run - 2)

# inputs the buoys in the model
simulation.input_buoyancy(line_type, buoys_set)

simulation.run_static_simulation(model_aut)
print("\nRan with Bend_Restrictor and Buoys")

rotation = vcm.StaticResult("Rotation 2")
print(f"\nRotation: {rotation}")
clearance = simulation.verify_line_clearance(line_type)
print(f"Clearance: {clearance}")

print("\nLoop initialization.")
simulation.loop_initialization(
    rotation, clearance, next_comb, line_type, select, model_aut, vcm)

rotation = vcm.StaticResult("Rotation 2")
print(f"\nRotation: {rotation}")
clearance = simulation.verify_line_clearance(line_type)
print(f"Clearance: {clearance}")
