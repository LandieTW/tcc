"""
Static analysis automation
"""

import OrcFxAPI
import time
import sim_run
from collections import Counter
from orca import object_elements
from methods import info


start_time = time.perf_counter()

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

# RUNNING WITHOUT BEND_RESTRICTOR

model_line_type.NumberOfAttachments = 0

sim_run.run_static_simulation(model, rt_number)
sim_run.user_specified(model, rt_number)

# ADDING BEND RESTRICTOR

model_line_type.NumberOfAttachments = 1
model_line_type.AttachmentType[0] = model_bend_restrictor_type.Name

bend_restrictor_ini_position = object_end_fitting.length

if object_bend_restrictor.material == "Polymer":
    object_zr_bend_restrictor = object_elements[4]
    model_zr_bend_restrictor = model[object_zr_bend_restrictor.name]
    if len_obj_pack == 6:  # EF + RZ + Flange
        object_flange = object_elements[5]
        model_flange = model[object_flange.name]
        bend_restrictor_ini_position += (object_zr_bend_restrictor.length
                                         + object_flange.length)
    else:  # EF + RZ
        bend_restrictor_ini_position += object_zr_bend_restrictor.length
else:
    if len_obj_pack == 5:  # EF + Flange
        object_flange = object_elements[4]
        model_flange = model[object_flange.name]
        bend_restrictor_ini_position += object_flange.length

model_line_type.Attachmentz[0] = bend_restrictor_ini_position
model_line_type.AttachmentzRelativeTo[0] = "End B"

sim_run.run_static_simulation(model, rt_number)
sim_run.user_specified(model, rt_number)

# ADDING BUOYS

"Buoyancy combination"
buoy_combination = sim_run.buoy_combination(buoy_set)

# RUNNING UNTIL RL CONDITIONS

"Partially adding buoyancy"
k = 1
while k <= 5:
    rl_config_fract = [
        rl_config[0], [round(k * x / 5, 0) for x in rl_config[1]]
    ]
    selection = sim_run.buoyancy(rl_config_fract, buoy_combination)
    treated_buoys = sim_run.buoyancy_treatment(rl_config_fract, selection)
    num_buoys = sim_run.number_buoys(treated_buoys)

    sim_run.input_buoyancy(model_line_type, num_buoys, treated_buoys, vessel)
    sim_run.run_static_simulation(model, rt_number)
    sim_run.user_specified(model, rt_number)

    k += 1

# GETTING RESULTS

selection = sim_run.buoyancy(rl_config, buoy_combination)
treated_buoys = sim_run.buoyancy_treatment(rl_config, selection)
num_buoys = sim_run.number_buoys(treated_buoys)

sim_run.input_buoyancy(model_line_type, num_buoys, treated_buoys, vessel)
sim_run.run_static_simulation(model, rt_number)

rotation = sim_run.verify_vcm_rotation(model_vcm)
clearance = sim_run.verify_line_clearance(model_line_type)
delta_flange_height = sim_run.verify_flange_height(model_line_type, object_line, object_vcm)

sim_run.user_specified(model, rt_number)

# LOOPING

"Looping entry"
result = sim_run.get_result(rotation, clearance, delta_flange_height)

p_parameter = 0  # to make the pointer

while result == "red":

    number = model_line_type.NumberOfAttachments

    model_buoys_position = []
    k = 1
    for _ in range(1, number):
        model_buoys_position.append(model_line_type.Attachmentz[k])
        k += 1
    model_buoys = list(selection.values())
    new_rl_config = [
        model_buoys_position,
        model_buoys
    ]

    while rotation > .5 or rotation < -.5:

        case = len(Counter(model_buoys_position))
        pointer, p_parameter = sim_run.make_pointer(case, p_parameter)
        print(f"Pointer: {pointer}")

        if rotation > .5:
            print(f"Rotation > .5")
            new_positions = [j + .5
                             for j in model_buoys_position]
            limits = []
            if case == 1:
                limits = [3]
            elif case == 2:
                limits = [3, 6]
            elif case == 3:
                limits = [3, 6, 9]

            if model_buoys_position != limits:

                rotation, clearance, delta_flange_height = \
                    sim_run.l_c_b_p(new_positions, model_line_type, number, model_buoys_position,
                                    pointer, model, rt_number, model_vcm, object_line, object_vcm)
            else:
                new_rl_config = sim_run.changing_buoyancy(rl_config, pointer, rotation)
                sim_run.changing_buoys(selection, buoy_set, new_rl_config, model_line_type, vessel)
                sim_run.run_static_simulation(model, rt_number)

                rotation = sim_run.verify_vcm_rotation(model_vcm)
                clearance = sim_run.verify_line_clearance(model_line_type)
                delta_flange_height = sim_run.verify_flange_height(model_line_type, object_line,
                                                                   object_vcm)

        elif rotation < -.5:
            print(f"Rotation < -.5")
            new_positions = [j - .5
                             for j in model_buoys_position]
            limits = []
            if case == 1:
                limits = [4]
            elif case == 2:
                limits = [4, 8]
            elif case == 3:
                limits = [4, 8, 12]

            if model_buoys_position != limits:
                rotation, clearance, delta_flange_height = \
                    sim_run.l_c_b_p(new_positions, model_line_type, number, model_buoys_position,
                                    pointer, model, rt_number, model_vcm, object_line, object_vcm)
            else:
                new_rl_config = sim_run.changing_buoyancy(rl_config, pointer, rotation)
                sim_run.changing_buoys(selection, buoy_set, new_rl_config, model_line_type, vessel)
                sim_run.run_static_simulation(model, rt_number)

                rotation = sim_run.verify_vcm_rotation(model_vcm)
                clearance = sim_run.verify_line_clearance(model_line_type)
                delta_flange_height = sim_run.verify_flange_height(model_line_type, object_line,
                                                                   object_vcm)

    while clearance < .5 or clearance > .6:
        delta = sim_run.define_delta_line(clearance)
        if clearance > .6:
            print(f"Clearance > .6")
            sim_run.payout_line(model_line_type, delta)
            sim_run.run_static_simulation(model, rt_number)

            rotation = sim_run.verify_vcm_rotation(model_vcm)
            clearance = sim_run.verify_line_clearance(model_line_type)
            delta_flange_height = sim_run.verify_flange_height(model_line_type, object_line,
                                                               object_vcm)
        elif clearance < .5:
            print(f"Clearance < .5")
            sim_run.retrieve_line(model_line_type, delta)
            sim_run.run_static_simulation(model, rt_number)

            rotation = sim_run.verify_vcm_rotation(model_vcm)
            clearance = sim_run.verify_line_clearance(model_line_type)
            delta_flange_height = sim_run.verify_flange_height(model_line_type, object_line,
                                                               object_vcm)

    """if delta_flange_height != 0:"""
    """
    # Ajusta o comprimento do guindaste
    # Aumenta bastante o damping
    # muda config para catenária e puxa o MCV
    # Roda, puxa resultados e volta para o damping normal"""
    """
    # Ajusta o x do solo igual ao x do MCV"""
    sim_run.user_specified(model, rt_number)
    result = sim_run.get_result(rotation, clearance, delta_flange_height)

# FINAL

rotation = sim_run.verify_vcm_rotation(model_vcm)
clearance = sim_run.verify_line_clearance(model_line_type)
print(f"\n Automation's end."
      f"\n Line clearance: {clearance} m."
      f"\n MCV rotation: {rotation} °")
