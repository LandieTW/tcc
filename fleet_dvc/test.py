
import OrcFxAPI as orca
import os

this_path = os.path.dirname(__file__)
file_path = os.path.join(this_path, "Estatico.dat")

model = orca.Model(file_path)

with model.CalculateStatics():
    print(model.warnings)
    print(orca._GetNumOfWarnings)
