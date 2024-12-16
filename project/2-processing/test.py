import OrcFxAPI
import os
from collections import Counter
from sim_run import payout_retrieve_line


path = os.path.dirname(__file__)
file = 'test.sim'
file_path = os.path.join(path, file)
model = OrcFxAPI.Model(file_path)

line = model['Line']
vcm = model['MCV']

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

vcm.Connection = "Fixed"

positions = list(Counter(line.Attachmentz).keys())
positions.remove(positions[0])

mass = [round(.05 + k / 10, 2) for k in range(20)]

cont = model.CreateObject(OrcFxAPI.ObjectType.ClumpType, name='Cont')
cont.Name = 'Cont'
cont.Volume = 2
cont.Height = 1

n = line.NumberOfAttachments
line.NumberOfAttachments = n + 1
line.AttachmentType[n] = 'Cont'
line.Attachmentz[n] = positions[0] + 1

initial_length = line.Length[0]

for k in range(2):

    line.Length[0] = initial_length
    
    if len(positions) == 1:
        if k == 1:
            line.Attachmentz[n] = positions[k - 1] + 3
        else:
            line.Attachmentz[n] = positions[k] + 1
    else:
        line.Attachmentz[n] = positions[k] + 1

    j = 0
    for _ in mass:
        cont.Mass = mass[j]

        work = True
        while work == True:
            try:
                model.CalculateStatics()
                line_clearance = enumerate(line.RangeGraph("Seabed clearance").Mean)
                line_tdp = [arc_length for arc_length, clearance in line_clearance if clearance < 0]

                if abs(line_tdp[0] - line_tdp[-1]) < 3:
                    payout_retrieve_line(line, payout_retrieve_pace_max, object_line, a_r)
            except Exception:
                j += 1
                work = False 
        
        if work == False:
            continue

        model.UseCalculatedPositions(SetLinesToUserSpecifiedStartingShape=True)      

        loads = [abs(round(line.StaticResult("End Ez force", OrcFxAPI.oeEndB), 3)), abs(round(line.StaticResult("End Ex force", OrcFxAPI.oeEndB), 3)), abs(round(line.StaticResult("End Ey moment", OrcFxAPI.oeEndB), 3))]
        flange_loads = any([verify_flange_loads(line, structural_limits, '3', loads), verify_flange_loads(line, structural_limits, '3i', loads), verify_flange_loads(line, structural_limits, '3ii', loads)])

        normalised_curvature = verify_normalised_curvature(bend_restrictor, "Mean")   
        if normalised_curvature >= 1:
            br_load = verify_br_loads(bend_restrictor, bend_restrictor_obj, "Mean")
        
            cont_limit = all([flange_loads, br_load])
            if cont_limit:
                file_name = 'Cont_' + str(k + 1) + '.sim'
                path = os.path.join(save_simulation, file_name)
                model.SaveSimulation(path)
                print(f"\nCase {k + 1}: Contingency - {mass[j]}kg in {line.Attachmentz[n]}m to the VCM")
                break
        
        else:
            if flange_loads:
                file_name = 'Cont_' + str(k + 1) + '.sim'
                path = os.path.join(save_simulation, file_name)
                model.SaveSimulation(path)
                print(f"\nCase {k + 1}: Contingency - {mass[j]}kg in {line.Attachmentz[n]}m to the VCM")
                break

        j += 1