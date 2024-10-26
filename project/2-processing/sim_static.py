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

# LOOPING

"Looping entry"
result = sim_run.get_result(rotation, clearance, delta_flange_height)

while result != "red":
    sim_run.user_specified(model, rt_number)
    change_buoys = "no"
    if .5 < rotation < -.5:
        number = model_line_type.NumberOfAttachments
        model_buoys_position = []
        k = 1
        for _ in range(1, number):
            model_buoys_position.append(model_line_type.Attachmentz[k])
            k += 1
        case = len(Counter(model_buoys_position))

        # Podemos iterar a list position de forma manual
        # alterando a ordem dos seus elementos
        # itera o primeiro, em seguida coloca o 1° elemento no lugar do último
        # e todo o restante dos elementos avança uma posição
        # roda a análise e o looping segue em frente.

        if rotation > .5:
            if case == 1:
                limits = [3]
                if model_buoys_position != limits:
                    pointer = sim_run.make_pointer(case)

                    new_model_buoys_position = []
                    for position in model_buoys_position:
                        new_model_buoys_position.append(position - .5)

                else:
                    "Troca boias"
            elif case == 2:
                limits = [3, 6]
                if model_buoys_position != limits:
                    ""
                else:
                    "Troca boias"
            elif case == 3:
                limits = [3, 6, 9]
                if model_buoys_position != limits:
                    ""
                else:
                    "Troca boias"
            """PLAN
            MOVER A BOIA MAIS PRA PERTO DO MCV
            change_buoys = "no"
            pega o RL_config e olha as posições de boias
                caso 1 -  o limite é [3, 4]m
                caso 2 -  o limite é [3, 4]m para a primeira 
                                     [6, 8]m para a segunda
                caso 3 -  o limite é [3, 4]m para a primeira
                                     [6, 8]m para a segunda
                                     [9, 12]m para a terceira
            verifica, para cada condição, se a boia está posicionada no limite
                se houve uma condição ainda não satisfeita, move a boia
                se todas forem satisfeitas, troca conjunto de boias
                    change_buoys = "yes"
            if change_buoys == "yes":
                change_buoys
            PLAN"""
        elif rotation < -.5:
            if case == 1:
                limits = [4]
                if model_buoys_position != limits:
                    ""
                else:
                    "Troca boias"
            elif case == 2:
                limits = [4, 8]
                if model_buoys_position != limits:
                    ""
                else:
                    "Troca boias"
            elif case == 3:
                limits = [4, 8, 12]
                if model_buoys_position != limits:
                    ""
                else:
                    "Troca boias"
            """PLAN
            MOVER A BOIA MAIS PRA DISTANTE DO MCV
            change_buoys = "no"
            pega o RL_config e olha as posições de boias
                caso 1 -  o limite é [3, 4]m
                caso 2 -  o limite é [3, 4]m para a primeira 
                                     [6, 8]m para a segunda
                caso 3 -  o limite é [3, 4]m para a primeira
                                     [6, 8]m para a segunda
                                     [9, 12]m para a terceira
            verifica, para cada condição, se a boia está posicionada no limite
                se houve uma condição ainda não satisfeita, move a boia
                se todas forem satisfeitas, troca conjunto de boias
                    change_buoys = "yes"
            if change_buoys == "yes":
                change_buoys
            PLAN"""

    if .5 > clearance > .6:
        delta = sim_run.define_delta_line(clearance)
        if clearance > .6:
            sim_run.payout_line(model_line, delta)
        elif clearance < .5:
            sim_run.retrieve_line(model_line, delta)

    if delta_flange_height != 0:
        """
        # Ajusta o comprimento do guindaste
        # Aumenta pra kcete o damping
        # muda config para Catenary e puxa o MCV
        # Roda, puxa resultados e volta para o damping normal"""
    """
    # Ajusta o x do solo igual ao x do MCV"""
    result = sim_run.get_result(rotation, clearance, delta_flange_height)

# FINAL

rotation = sim_run.verify_vcm_rotation(model_vcm)
clearance = sim_run.verify_line_clearance(model_line_type)
print(f"\n Automation's end."
      f"\n Line clearance: {clearance} m."
      f"\n MCV rotation: {rotation} °")
