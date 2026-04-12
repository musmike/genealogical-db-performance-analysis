import math
import random
from datetime import date

def get_planned_children_count(target_avg: float) -> int:
    """
    Draws a family size from a Poisson distribution with lambda = target_avg.
    Poisson is a good fit here because it naturally models count-based events
    (births) and produces realistic tails for both small and large families.
    PMF formula: P(k) = (λ^k * e^-λ) / k!
    """
    weights = []
    for i in range(14):
        w = (math.pow(target_avg, i) * math.exp(-target_avg)) / math.factorial(i)
        weights.append(w)
    return random.choices(list(range(14)), weights=weights, k=1)[0]

def get_marriage_age(sex: str) -> int:
    """
    Draws a marriage age from a Gaussian distribution, separately for men and women.
    A rejection loop keeps the result within biologically valid bounds.
    """
    if sex == 'F':
        while True:
            age = int(random.gauss(24, 3.5))
            if 16 <= age <= 50: return age
    else:
        while True:
            age = int(random.gauss(26, 4))
            if 18 <= age <= 65: return age

def get_lifespan() -> int:
    """
    Draws a lifespan, accounting for historical infant and child mortality.
    20% of individuals die before age 5. The remaining population follows a Gaussian distribution.
    """
    if random.random() < 0.20:
        return random.randint(0, 5)
    while True:
        lifespan = int(random.gauss(65, 15))
        if 6 <= lifespan <= 100: return lifespan

def get_ancestors_with_depth(person_id: int, max_depth: int, people: dict, families: dict) -> dict:
    """
    BFS traversal up the genealogical tree up to max_depth generations.
    Returns a dict of {ancestor_id: minimum_generational_distance}.
    Used when checking kinship before allowing a marriage to take place.
    """
    result = {}
    queue = [(person_id, 0)]
    while queue:
        current_id, depth = queue.pop(0)
        if depth < max_depth:
            p = people.get(current_id)
            if p and p.parents_family_id:
                parent_family = families.get(p.parents_family_id)
                if parent_family:
                    for parent_id in (parent_family.husband_id, parent_family.wife_id):
                        if parent_id:
                            new_depth = depth + 1
                            if parent_id not in result or result[parent_id] > new_depth:
                                result[parent_id] = new_depth
                                queue.append((parent_id, new_depth))
    return result

def is_too_closely_related(p_a_id: int, p_b_id: int, people: dict, families: dict) -> bool:
    """
    Determines whether two individuals are too closely related to marry.
    Rules:
    - If they are the same person, return True.
    - If one is a direct ancestor of the other, return True.
    - If the sum of their distances to any common ancestor is <= 6, return True
    """
    if p_a_id == p_b_id:
        return True

    if is_direct_ancestor(p_a_id, p_b_id, people, families) or is_direct_ancestor(p_b_id, p_a_id, people, families):
        return True

    anc_a = get_ancestors_with_depth(p_a_id, max_depth=5, people=people, families=families)
    anc_b = get_ancestors_with_depth(p_b_id, max_depth=5, people=people, families=families)

    for ancestor_id in set(anc_a) & set(anc_b):
        # Sum of both individuals' distances to a shared ancestor <= 6 means too closely related
        if anc_a[ancestor_id] + anc_b[ancestor_id] <= 6:
            return True

    return False

def is_direct_ancestor(older_id: int, younger_id: int, people: dict, families: dict) -> bool:
    """
    Checks whether older_id is a direct ancestor of younger_id (linea recta).
    BFS limited to 7 generations — sufficient to cover all realistic cases in the dataset.
    """
    queue = [(younger_id, 0)]
    while queue:
        curr_id, depth = queue.pop(0)
        if curr_id == older_id: return True
        if depth < 7:
            p = people.get(curr_id)
            if p and p.parents_family_id:
                fam = families.get(p.parents_family_id)
                if fam:
                    if fam.husband_id: queue.append((fam.husband_id, depth + 1))
                    if fam.wife_id: queue.append((fam.wife_id, depth + 1))
    return False

def random_date(year: int) -> date:
    """
    Returns a random date within the given year. The day is capped at 28
    to avoid dealing with leap year validation and varying month lengths.
    """
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)

def adjust_surname(surname: str, sex: str) -> str:
    """
    Applies Polish grammatical gender rules to the most common surname suffixes:
    -ski → -ska, -cki → -cka, -dzki → -dzka.
    Surnames that don't match any of these patterns are returned unchanged.
    """
    if sex == 'F':
        if surname.endswith('ski'): return surname[:-3] + 'ska'
        if surname.endswith('cki'): return surname[:-3] + 'cka'
        if surname.endswith('dzki'): return surname[:-3] + 'dzka'
    return surname

def get_family_status() -> str:
    """Draws a family status for a married couple, with dominant 'MARRIED' status 
    and smaller probabilities for 'PARTNERS', and 'OTHER'."""
    return random.choices(['MARRIED', 'PARTNERS', 'OTHER'],
                          weights=[0.90, 0.06, 0.04], k=1)[0]

def get_child_relationship_type() -> str:
    """Draws a child's relationship type to the family (biological, adopted, or foster)."""
    return random.choices(['BIOLOGICAL', 'ADOPTED', 'FOSTER'],
                          weights=[0.96, 0.03, 0.01], k=1)[0]