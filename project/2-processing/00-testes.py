

import OrcFxAPI as Orca

model = Orca.Model("RT 2517\\6-RT 2517_Static.sim")

line = model["Line"]

depth = line.StaticResult("Z", Orca.oeEndB)

print(depth)
