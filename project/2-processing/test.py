import OrcFxAPI
import os


diretorio = os.path.dirname(os.path.abspath(__file__))
model_name = "RT 2517\\Static\\2-RT 2517.sim"
executable = os.path.join(diretorio, model_name)


model = OrcFxAPI.Model(executable)

"""for object in model:
    print(f"Objeto: {object} - Tipo do objeto: {type(object)}")
"""

line = model["Line"]

tract = line.StaticResult("End Ex force", OrcFxAPI.oeEndB)
print(abs(round(tract, 3)))
shear = line.StaticResult("End Ez force", OrcFxAPI.oeEndB)
print(abs(round(shear, 3)))
moment = line.StaticResult("End Ey moment", OrcFxAPI.oeEndB)
print(abs(round(moment, 3)))
