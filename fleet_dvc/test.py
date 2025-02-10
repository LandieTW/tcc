
from collections import Counter

'Submerged mass limit, in kg, for a combination of buoys'
buoyancy_limit = 2_000

'Submerged mass limit, in kg for a small buoy'
small_buoy_buoyancy_limit = 100

'Maximum number of buoys for each position'
n_buoys = 3  

# Vessel's set of buoys
cda_buoys = [1252, 1252, 1252, 973, 828, 573, 573, 573, 283, 283, 283, 205, 205, 205, 205, 118, 118, 118, 118, 118, 118, 100]
ska_buoys = [1416, 1376, 1345, 1323, 1320, 871, 741, 741, 660, 647, 381, 377, 155, 104, 101, 100]
skb_buoys = [1508, 1451, 1428, 1425, 1416, 1320, 760, 726, 708, 385]
skn_buoys = [1000, 1000, 1000, 1000, 1000, 500, 500, 500, 343, 100, 100, 100, 100, 100]
sko_buoys = [1213, 1213, 1213, 1213, 1213, 576, 576, 576, 576, 576, 381, 381, 381,381,381, 100, 100, 100, 100, 100]
skr_buoys = [1000, 1000, 1000, 1000, 1000, 500, 500, 500, 250, 250, 100, 100, 100, 100, 100]
skv_buoys = [1000, 1000, 1000, 1000, 1000, 500, 500, 500, 300, 100, 100, 100, 100, 100]

vessel_buoys = {
    'Skandi Niterói': [list(Counter(skn_buoys).keys()), list(Counter(skn_buoys).values())], 
    'Skandi Búzios': [list(Counter(skb_buoys).keys()), list(Counter(skb_buoys).values())], 
    'Skandi Açu': [list(Counter(ska_buoys).keys()), list(Counter(ska_buoys).values())], 
    'Skandi Vitória': [list(Counter(skv_buoys).keys()), list(Counter(skv_buoys).values())], 
    'Skandi Recife': [list(Counter(skr_buoys).keys()), list(Counter(skr_buoys).values())], 
    'Skandi Olinda': [list(Counter(sko_buoys).keys()), list(Counter(sko_buoys).values())], 
    'Coral do Atlântico': [list(Counter(cda_buoys).keys()), list(Counter(cda_buoys).values())]
}

set_buoys = vessel_buoys['Skandi Açu']

print(set_buoys)

def buoy_combination(b_set: list) -> dict:
    """
    Description:
        Generate all possible buoy's combination, considering:
        1 - Each combination must have, at maximum, n_buoys buoys.
        2 - Each combination must have less than buoyancy_limit of submerged mass.
        3 - Combinations with 3 buoys must have at least one buoy ≤ small_buoy_limit.
    Parameter:
        set_of_buoys (list): The available vessel buoys, in the format [[quantities], [buoyancies]].
    Returns:
        dict: A dictionary with all possible buoy combinations.
    """
    # Creating a list of buoys with repeated elements based on their frequency
    buoys = [str(b_set[0][i]) for i in range(len(b_set[0])) for _ in range(b_set[1][i])]
    
    small_buoys = [b for b in buoys if float(b) <= small_buoy_buoyancy_limit]

    # One buoy combinations
    one_buoy = {buoy: float(buoy) for buoy in buoys}

    # Two buoy combinations
    two_buoys = {}
    for i, buoy1 in enumerate(buoys):
        for j, buoy2 in enumerate(buoys[i+1:], start=i+1):  # Avoid repeating combinations
            combined_buoy = one_buoy[buoy1] + one_buoy[buoy2]
            if combined_buoy <= buoyancy_limit:
                two_buoys[f"{buoy1}+{buoy2}"] = combined_buoy

    # Three buoy combinations (with at least one small buoy)
    three_buoys = {}
    for i, buoy1 in enumerate(buoys):
        for j, buoy2 in enumerate(buoys[i+1:], start=i+1):
            for small_buoy in small_buoys:
                combined_buoy = one_buoy[buoy1] + one_buoy[buoy2] + float(small_buoy)
                if combined_buoy <= buoyancy_limit:
                    three_buoys[f"{buoy1}+{buoy2}+{small_buoy}"] = combined_buoy

    # Combine all based on n_buoys
    combination = {}
    if n_buoys == 1:
        combination.update(one_buoy)
    elif n_buoys == 2:
        combination.update(one_buoy)
        combination.update(two_buoys)
    elif n_buoys == 3:
        combination.update(one_buoy)
        combination.update(two_buoys)
        combination.update(three_buoys)
    
    # Sort combinations by buoyancy
    sorted_combinations = dict(sorted(combination.items(), key=lambda item: item[1], reverse=False))
    return sorted_combinations

buoy_comb = buoy_combination(set_buoys)

print(buoy_comb)
