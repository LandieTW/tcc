import OrcFxAPI
import os

diretorio = os.path.dirname(os.path.abspath(__file__))
model_name = "RT 2517\\RT 2517.dat"
executable = os.path.join(diretorio, model_name)

model = OrcFxAPI.Model(executable)

line = model['Line']

attach = list(line.AttachmentType)
print(attach)

model_environment = model["Environment"]

print(model_environment.SeabedNormalStiffness)

model_environment.SeabedNormalStiffness = 0

print(model_environment.SeabedNormalStiffness)


