"""
DVC analysis automation
"""

import OrcFxAPI
import time
import os
import sys
import sim_run
from io import StringIO
from orca import object_elements
from methods import info

statics_max_iterations = 400  # Maximum number of iterations
statics_min_damping = 5  # Minimum damping
statics_max_damping = 15  # Maximum damping
vcm_delta_x = 20  # VCM's movement: 20m (helps convergence when adjusting flange height)

class DualOutput:
    def __init__(self, original_stdout, buffer):
        self.original_stdout = original_stdout
        self.buffer = buffer

    def write(self, message):
        self.original_stdout.write(message)
        self.buffer.write(message)

    def flush(self):
        self.original_stdout.flush()

original_stdout = sys.stdout
buffer = StringIO()
sys.stdout = DualOutput(original_stdout, buffer)

start_time = time.time()

rt_number = info[0]
vessel = info[1]
buoy_set = info[2]
rl_config = info[3]
structural_limits = info[4]

this_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(this_path, rt_number)
file = rt_number + ".dat"
executable = os.path.join(file_path, file)
model = OrcFxAPI.Model(executable)

model_general = model['General']

len_obj_pack = len(object_elements)

object_line = object_elements[0]
model_line = model[object_line.name]
model_line_type = model["Line"]

object_bend_restrictor = object_elements[1]
model_bend_restrictor = model[object_bend_restrictor.name]

object_end_fitting = object_elements[2]
model_end_fitting = model[object_end_fitting.name]

object_vcm = object_elements[3]
model_vcm = model[object_vcm.name]

model_winch = model["Guindaste"]
model_environment = model["Environment"]
model_stiffness_line = model["Stiffness1"]
model_stiffness_bend_restrictor = model["Stiffness2"]

a_r = model['A/R']
if object_line.length != object_line.lda:
    model_general.StaticsMinDamping = 4 * statics_min_damping
    model_general.StaticsMaxDamping = 4 * statics_max_damping
    model_general.StaticsMaxIterations = 3 * statics_max_iterations

print("\nRunning without bend_restrictor")

model_line_type.NumberOfAttachments = 0

sim_run.previous_run_static(model, model_general, model_line_type, model_vcm)
sim_run.user_specified(model, rt_number, file_path)

model_general.StaticsMinDamping = statics_min_damping
model_general.StaticsMaxDamping = statics_max_damping
model_general.StaticsMaxIterations = statics_max_iterations

print("\nRunning with bend_restrictor")

model_line_type.NumberOfAttachments = 1
model_line_type.AttachmentType[0] = "Vert"
stiffener_type = model["Stiffener1"]

bend_restrictor_ini_position = object_end_fitting.length

if object_bend_restrictor.material == "Polymer":
    object_zr_bend_restrictor = object_elements[4]
    model_zr_bend_restrictor = model[object_zr_bend_restrictor.name]
    if len_obj_pack == 7:  # EF + RZ + Flange
        object_flange = object_elements[5]
        model_flange = model[object_flange.name]
        bend_restrictor_ini_position += (object_zr_bend_restrictor.length + object_flange.length)
    else:  # EF + RZ
        bend_restrictor_ini_position += object_zr_bend_restrictor.length
else:
    if len_obj_pack == 6:  # EF + Flange
        object_flange = object_elements[4]
        model_flange = model[object_flange.name]
        bend_restrictor_ini_position += object_flange.length

model_line_type.Attachmentz[0] = bend_restrictor_ini_position
model_line_type.AttachmentzRelativeTo[0] = "End B"

stiffener_fin_position = round(bend_restrictor_ini_position + object_bend_restrictor.length, 3)
prohibited_position = (stiffener_fin_position // .5) * .5

# Restrição de colocação de flutuadores na interface 
# final da vértebra, por motivos de dificuldades operacionais na instalação.
"""num_pos = len(rl_config[0])
# MUDANDO O RL CONFIG
for i in range(len(rl_config[0])):
    if rl_config[0][i] == prohibited_position:
        print(
            f"\nAjustando a configuração proposta no RL para evitar dificuldades"
            f"operacionais na instalação de boias na interface final da vértebra."
            )
        rl_config[0][i] += .5
        if num_pos == 3:
            if i == 1:
                rl_config[0][2] += .5"""

sim_run.previous_run_static(model, model_general, model_line_type, model_vcm)
sim_run.user_specified(model, rt_number, file_path)

model_general.StaticsMinDamping = statics_min_damping
model_general.StaticsMaxDamping = statics_max_damping
model_general.StaticsMaxIterations = statics_max_iterations

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
    sim_run.previous_run_static(model, model_general, model_line_type, model_vcm)
    sim_run.user_specified(model, rt_number, file_path)

    model_general.StaticsMinDamping = statics_min_damping
    model_general.StaticsMaxDamping = statics_max_damping
    model_general.StaticsMaxIterations = statics_max_iterations
    k += 1

print("\nAutomation's start.")
sim_run.looping(model_line_type, selection, model, stiffener_type, rt_number, vessel,
                rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm,
                model_winch, model_general, model_environment, file_path, structural_limits,
                prohibited_position, a_r)

static_end_time = time.time()
exec_static_time = static_end_time - start_time

print(f"\n Static automation's end."
      f"\n Execution time: {exec_static_time:.2f}s")
print(f"\n Starting dynamics...")

sys.stdout = original_stdout
captured_text = buffer.getvalue()
txt_file = "Static\\" + rt_number + " - Report.txt"
results_path = os.path.join(file_path, txt_file)

with open(results_path, "w", encoding="utf-8") as file:
    file.write(captured_text)

original_stdout = sys.stdout
buffer = StringIO()
sys.stdout = DualOutput(original_stdout, buffer)

dyn_dir = "Dynamic"
dyn_path = os.path.join(file_path, dyn_dir)
os.makedirs(dyn_path, exist_ok=True)
file_name = rt_number + ".sim"
save_simulation = os.path.join(dyn_path, file_name)

sim_run.dynamic_simulation(model, model_line_type, model_vcm, stiffener_type, 
                           object_bend_restrictor, a_r, dyn_path, structural_limits, rt_number)

dynamic_end_time = time.time()
exec_dynamic_time = dynamic_end_time - static_end_time

print(f"\n Dynamic automation's end."
      f"\n Execution time: {exec_dynamic_time:.2f}s")

sys.stdout = original_stdout
captured_text = buffer.getvalue()
txt_file = "Dynamic\\" + rt_number + " - Report.txt"
results_path = os.path.join(file_path, txt_file)

with open(results_path, "w", encoding="utf-8") as file:
    file.write(captured_text)
