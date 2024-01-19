##### Method 1: use Farthest points in baybe #####

from baybe.targets import NumericalTarget
from baybe.objective import Objective
from baybe.parameters import NumericalContinuousParameter
from baybe.searchspace import SearchSpace
from baybe import Campaign


target = NumericalTarget(
    name="Yield",
    mode="MAX",
)
objective = Objective(mode="SINGLE", targets=[target])


parameters = [
    NumericalContinuousParameter(
        name="Temp",
        bounds=(25, 80),
    ),
    NumericalContinuousParameter(
        name="Liq flow rate",
        bounds=(10, 100),
    ),
    NumericalContinuousParameter(
        name="Flue gas flow rate",
        bounds=(10, 1000),
    ),
    NumericalContinuousParameter(
        name="Current density",
        bounds=(100, 300),
    ),
]


searchspace = SearchSpace.from_product(parameters)
campaign = Campaign(searchspace, objective)
df = campaign.recommend(batch_quantity=8)
print(df)


##### Method 2: use Latin Hypercube Sampling (LHS) #####
import numpy as np
import pyDOE2

# Define the ranges for each parameter
param_ranges = {
    'Temperature': (25, 80),  # ºC
    'Liquid flow rate': (10, 100),  # mL min–1
    'Flue gas flow rate': (10, 1000),  # sccm
    'Current density': (100, 300)  # mA cm–2
}

# Define the number of levels (points) and the number of parameters
num_levels = 8
num_params = len(param_ranges)

# Generate the Latin Hypercube Sample
lhs_sample = pyDOE2.lhs(num_params, samples=num_levels, criterion='center')

# Scale the LHS sample to the range of each parameter
for i, (key, (low, high)) in enumerate(param_ranges.items()):
    lhs_sample[:, i] = lhs_sample[:, i] * (high - low) + low
    lhs_sample[:, i] = np.round(lhs_sample[:, i])  # Round to nearest integer

# Print selected parameter sets
for i, params in enumerate(lhs_sample):
    print(f"Set {i+1}: Temperature = {int(params[0])} ºC, "
          f"Liquid flow rate = {int(params[1])} mL min–1, "
          f"Flue gas flow rate = {int(params[2])} sccm, "
          f"Current density = {int(params[3])} mA cm–2")
