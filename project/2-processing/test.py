import OrcFxAPI
import os


diretorio = os.path.dirname(os.path.abspath(__file__))
model_name = "RT 2517\\8-RT 2517_Static.sim"
executable = os.path.join(diretorio, model_name)


model = OrcFxAPI.Model(executable)

"""for object in model:
    print(f"Objeto: {object} - Tipo do objeto: {type(object)}")
"""
stiffener_type = model["Stiffener1"]

shear = stiffener_type.RangeGraph("Shear force")
shear = [sf
         for index, sf in enumerate(shear.Mean)]

print(int(max(shear)))
