import OrcFxAPI
import os
from methods import info
from orca import object_elements
import sim_run

heave_up = [2.5, 2.0, 1.8]  # heave up options
heave_up_period = OrcFxAPI.SpecifiedPeriod(0, 2.15)  # period in which 'heave up' occurs
transition_period = OrcFxAPI.SpecifiedPeriod(2.15, 32.15)  # period between heave up and tdp
tdp_period = OrcFxAPI.SpecifiedPeriod(32.15, 72.15)  # period in which tdp occurs
total_period = OrcFxAPI.SpecifiedPeriod(0, 72.15)  # all period

def verify_normalised_curvature(bend_restrictor_model: OrcFxAPI.OrcaFlexObject, magnitude: str) -> float:
    if magnitude == "Mean":
        n_curve = bend_restrictor_model.RangeGraph("Normalised curvature")
        nc = [nc for _, nc in enumerate(n_curve.Mean)]
    elif magnitude == "Max":
        n_curve = bend_restrictor_model.RangeGraph("Normalised curvature", OrcFxAPI.PeriodNum.WholeSimulation)
        nc = [nc for _, nc in enumerate(n_curve.Max)]
    nc_max = round(max(nc), 3)
    if nc_max >= 1:
        print(f"\n Bend Restrictor's locked")
    return nc_max

rt_number = info[0]
structural_limits = info[4]

diretorio = os.path.dirname(os.path.abspath(__file__))
model_name = "RT 2517\\Dynamic\\RT 2517 - heave_2.5m.sim"
executable = os.path.join(diretorio, model_name)

model = OrcFxAPI.Model(executable)

line = model['Line']
vcm = model['FD-3A00.00-1514-276-PEK-001']
stiffener = model["Stiffener1"]
a_r = model['A/R']

heave = heave_up[0]

this_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(this_path, rt_number)
dyn_dir = "Dynamic"
dyn_path = os.path.join(file_path, dyn_dir)
file_name = rt_number + " - heave_" + str(heave) + "m.sim"
simulation = os.path.join(dyn_path, file_name)

obj_bend_restrictor = object_elements[1]

result = sim_run.run_dynamic(model, line, stiffener, obj_bend_restrictor, 
                             structural_limits, simulation)
