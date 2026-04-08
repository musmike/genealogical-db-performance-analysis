import math
import random
from datetime import date
from typing import Set


def get_planned_children_count(target_avg: float) -> int:
    weights = []
    for i in range(14):
        # Poisson PMF formula: (lambda^k * e^-lambda) / k!
        w = (math.pow(target_avg, i) * math.exp(-target_avg)) / math.factorial(i)
        weights.append(w)
    return random.choices(list(range(14)), weights=weights, k=1)[0]


def get_marriage_age(sex: str) -> int:
    if sex == 'F':
        while True:
            age = int(random.gauss(24, 3.5))
            if 16 <= age <= 50: return age
    else:
        while True:
            age = int(random.gauss(26, 4))
            if 18 <= age <= 65: return age


def get_lifespan() -> int:
    if random.random() < 0.15:
        return random.randint(0, 5)
    while True:
        lifespan = int(random.gauss(65, 15))
        if 6 <= lifespan <= 100: return lifespan


def get_ancestors_with_depth(person_id: int, max_depth: int, people: dict, families: dict) -> dict:
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
    if p_a_id == p_b_id:
        return True

    if is_direct_ancestor(p_a_id, p_b_id, people, families) or is_direct_ancestor(p_b_id, p_a_id, people, families):
        return True

    anc_a = get_ancestors_with_depth(p_a_id, max_depth=5, people=people, families=families)
    anc_b = get_ancestors_with_depth(p_b_id, max_depth=5, people=people, families=families)

    for ancestor_id in set(anc_a) & set(anc_b):
        if anc_a[ancestor_id] + anc_b[ancestor_id] <= 6:
            return True

    return False


def is_direct_ancestor(older_id: int, younger_id: int, people: dict, families: dict) -> bool:
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
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)


def adjust_surname(surname: str, sex: str) -> str:
    if sex == 'F':
        if surname.endswith('ski'): return surname[:-3] + 'ska'
        if surname.endswith('cki'): return surname[:-3] + 'cka'
        if surname.endswith('dzki'): return surname[:-3] + 'dzka'
    return surname


def get_family_status() -> str:
    return random.choices(['MARRIED', 'PARTNERS', 'OTHER', 'ANNULLED'], weights=[0.90, 0.06, 0.03, 0.01], k=1)[0]


def get_child_relationship_type() -> str:
    return random.choices(['BIOLOGICAL', 'ADOPTED', 'FOSTER'], weights=[0.96, 0.03, 0.01], k=1)[0]