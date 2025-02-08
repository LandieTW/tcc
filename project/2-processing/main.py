"""
DVC analysis automation
"""

# Libs

import OrcFxAPI
import time
import os
import sys
import sim_run
from io import StringIO
from orca import object_elements
from methods import info

# Constants
'Maximum number of iterations'
statics_max_iterations = 400
'Minimum damping'
statics_min_damping = 5
'Maximum damping'
statics_max_damping = 15
'VCM displace - when trying to adjust the model convergence'
vcm_delta_x = 20
'Heave up heights'
heave_up = [2.5, 2.0, 1.8, 1.5]

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
file = rt_number + '.dat'
executable = os.path.join(file_path, file)
model = OrcFxAPI.Model(executable)

model_general = model['General']

len_obj_pack = len(object_elements)

object_line = object_elements[0]
model_line = model[object_line.name]
model_line_type = model["Line"]

object_bend_restrictor = object_elements[1]
model_bend_restrictor = model[object_bend_restrictor.name]
stiffener_type = model["Stiffener1"]

object_end_fitting = object_elements[2]
model_end_fitting = model[object_end_fitting.name]

object_vcm = object_elements[3]
model_vcm = model[object_vcm.name]

model_winch = model["Guindaste"]
model_environment = model["Environment"]
model_stiffness_line = model["Stiffness1"]
model_stiffness_bend_restrictor = model["Stiffness2"]

a_r = model['A/R']

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

print("\n>>>>>>>>\nRunning without bend_restrictor")

model_line_type.NumberOfAttachments = 0

ini_time = time.time()
sim_run.previous_run_static(model, model_general, model_line_type, model_vcm, object_line, object_vcm, ini_time)
sim_run.user_specified(model, rt_number, file_path)

if model_general.StaticsMinDamping != statics_min_damping:
    model_general.StaticsMinDamping = statics_min_damping
    model_general.StaticsMaxDamping = statics_max_damping
    model_general.StaticsMaxIterations = statics_max_iterations
if model_environment.SeabedNormalStiffness != 100:
    model_environment.SeabedNormalStiffness = 100

print("\n>>>>>>>>\nRunning with bend_restrictor")

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

ini_time = time.time()
sim_run.previous_run_static(model, model_general, model_line_type, model_vcm, object_line, object_vcm, ini_time)
sim_run.user_specified(model, rt_number, file_path)

if model_general.StaticsMinDamping != statics_min_damping:
    model_general.StaticsMinDamping = statics_min_damping
    model_general.StaticsMaxDamping = statics_max_damping
    model_general.StaticsMaxIterations = statics_max_iterations
if model_environment.SeabedNormalStiffness != 100:
    model_environment.SeabedNormalStiffness = 100

print("\n>>>>>>>>\nRunning with buoys")

buoy_combination = sim_run.buoy_combination(buoy_set)
selection = {}

print("\n>>>>>>>>\nPartially adding buoyancy")
k = 1
while k <= 5:
    rl_config_fract = [rl_config[0], [round(k * x / 5, 0) for x in rl_config[1]]]
    selection = sim_run.buoyancy(rl_config_fract, buoy_combination)
    treated_buoys = sim_run.buoyancy_treatment(rl_config_fract, selection)
    num_buoys = sim_run.number_buoys(treated_buoys)
    sim_run.input_buoyancy(model_line_type, num_buoys, treated_buoys, vessel)
    print(f"\n>>>>>>>>\nPartial buoyancy: {rl_config_fract[1]}")
    ini_time = time.time()
    sim_run.previous_run_static(model, model_general, model_line_type, model_vcm, object_line, object_vcm, ini_time)
    sim_run.user_specified(model, rt_number, file_path)

    if model_general.StaticsMinDamping != statics_min_damping:
        model_general.StaticsMinDamping = statics_min_damping
        model_general.StaticsMaxDamping = statics_max_damping
        model_general.StaticsMaxIterations = statics_max_iterations
    if model_environment.SeabedNormalStiffness != 100:
        model_environment.SeabedNormalStiffness = 100
        
    k += 1

if rl_config != rl_config_fract:
    rl_config = rl_config_fract

static_dir = os.path.join(file_path, "Static")
os.makedirs(static_dir, exist_ok=True)

print("\n>>>>>>>>\nAutomation's start.")
sim_run.looping(model_line_type, selection, model, stiffener_type, rt_number, vessel, rl_config, buoy_set, model_vcm, object_line, object_bend_restrictor, object_vcm, model_winch, model_general, 
                model_environment, file_path, structural_limits, a_r, static_dir)

static_end_time = time.time()
exec_static_time = static_end_time - start_time

print(f"\n>>>>>>>>\nStatic automation's end."
      f"\n>>>>>>>>\nExecution time: {exec_static_time:.2f}s")

sys.stdout = original_stdout            # resets stdout
captured_text = buffer.getvalue()       # 
txt_file = "Static\\" + rt_number + " - Report.txt"
results_path = os.path.join(file_path, txt_file)

with open(results_path, "w", encoding="utf-8") as file:
    file.write(captured_text)

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

print(f"\n>>>>>>>>\nStarting dynamics...")

original_stdout = sys.stdout
buffer = StringIO()
sys.stdout = DualOutput(original_stdout, buffer)

dyn_dir = "Dynamic"
dyn_path = os.path.join(file_path, dyn_dir)
os.makedirs(dyn_path, exist_ok=True)

for heave in heave_up:
    dyn_result = sim_run.dynamic_simulation(model, model_line_type, stiffener_type, object_bend_restrictor, a_r, dyn_path, structural_limits, rt_number, heave, model_vcm, model_general)
    
    if dyn_result:
        break

dynamic_end_time = time.time()
exec_dynamic_time = dynamic_end_time - static_end_time

print(f"\n>>>>>>>>\nDynamic automation's end."
      f"\n>>>>>>>>\nExecution time: {exec_dynamic_time:.2f}s")

sys.stdout = original_stdout
captured_text = buffer.getvalue()
txt_file = "Dynamic\\" + rt_number + " - Report.txt"
results_path = os.path.join(file_path, txt_file)

with open(results_path, "w", encoding="utf-8") as file:
    file.write(captured_text)

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

print(f"\n>>>>>>>>\nStarting Contingencies...")

original_stdout = sys.stdout
buffer = StringIO()
sys.stdout = DualOutput(original_stdout, buffer)

cont_dir = "Contingencies"
cont_path = os.path.join(file_path, cont_dir)
os.makedirs(cont_path, exist_ok=True)

sim_run.contingencies(model, model_line_type, stiffener_type, object_bend_restrictor, cont_path, structural_limits, model_vcm, object_line, a_r, model_general, model_environment)

cont_end_time = time.time()
exec_cont_time = cont_end_time - dynamic_end_time

print(f"\n>>>>>>>>\nContingencies automation's end."
      f"\n>>>>>>>>\nExecution time: {exec_cont_time:.2f}s")

sys.stdout = original_stdout
captured_text = buffer.getvalue()
txt_file = "Contingencies\\" + rt_number + " - Report.txt"
results_path = os.path.join(file_path, txt_file)

with open(results_path, "w", encoding="utf-8") as file:
    file.write(captured_text)
