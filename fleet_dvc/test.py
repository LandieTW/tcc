
import OrcFxAPI as orca
import os


def verify_normalised_curvature(
        element: orca.OrcaFlexObject,
        magnitude: str,
        ) -> float:
    """
    Description:
        Verify element's normalised curvature value
    Parameters:
        element: OrcaFlex object (Line or bend restrictor)
        magnitude: 'Mean' for static calculation and 'Max' for simulation
    Returns:
        Element's normalised curvature value
    """
    if magnitude == 'Mean':
        n_curve = element.RangeGraph('Normalised curvature').Mean
        # nc = [nc for _, nc in enumerate(n_curve.Mean)]      # Static calculation
    
    elif magnitude == 'Max':
        n_curve = element.RangeGraph('Normalised curvature', period=orca.PeriodNum.WholeSimulation).Max
        # nc = [nc for _, nc in enumerate(n_curve.Max)]       # Simulation
    
    return round(max(n_curve), DECIMAL)

this_path = os.path.dirname(__file__)
file = os.path.join(this_path, "Estatico.dat")

model = orca.Model(file)

model.CalculateStatics()

line = model['Line']
vert = model['Stiffener1']

nc_vert = verify_normalised_curvature(vert, 'Mean')
