import OrcFxAPI
import os
import sim_run

diretorio = os.path.dirname(os.path.abspath(__file__))
model_name = "RT 2517\\RT 2517.dat"
executable = os.path.join(diretorio, model_name)

model = OrcFxAPI.Model(executable)

line = model['Line']

attach = list(line.AttachmentType)
print(attach)

index = attach.index('Vert')

line.AttachmentType.DeleteRow(index)

if not 'Vert' in list(line.AttachmentType):
    print("Está funcionando")

start_pos = line.Length[6]

sim_run.insert_vert(line, start_pos)

if 'Vert' in list(line.AttachmentType):
    attach = list(line.AttachmentType)
    print(attach)
    index = attach.index('Vert')
    print(index)
    print("Está funcionando")
