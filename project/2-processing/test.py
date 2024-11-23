import OrcFxAPI
import os
from methods import info

structural = info[4]

diretorio = os.path.dirname(os.path.abspath(__file__))
model_name = "RT 2517\\Static\\2-RT 2517.sim"
executable = os.path.join(diretorio, model_name)

model = OrcFxAPI.Model(executable)

line = model["Line"]

normal = abs(round(line.StaticResult("End Ez force", OrcFxAPI.oeEndB), 3))
shear = abs(round(line.StaticResult("End Ex force", OrcFxAPI.oeEndB), 3))
moment = abs(round(line.StaticResult("End Ey moment", OrcFxAPI.oeEndB), 3))

flange_loads = [normal, shear, moment]

print(flange_loads)

for case, values in structural.items():
    print(f"Case: {case} / Load: {values}")

load_check = []
for case in structural.values():
    if len(load_check) == 3:
        if all(load_check):
            print("Os esforços verificados são admissíveis.")
            break
        load_check.clear()
        
    for i in range(len(case)):
        if flange_loads[i] < abs(round(case[i], 3)):
            load_check.append(True)
        else:
            load_check.append(False)

print(load_check)
print(all(load_check))
