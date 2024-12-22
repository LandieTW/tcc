import OrcFxAPI
import os

this_path = os.path.dirname(__file__)
file_name = 'test.sim'

file_path = os.path.join(this_path, file_name)

model = OrcFxAPI.Model(file_path)

model.CalculateStatics()
print(model.warnings)