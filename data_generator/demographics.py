"""
Demographic and genealogical utility functions.

This module provides the stochastic models used to determine individual
life events — childbirth counts, marriage ages, lifespans — as well as
graph-traversal helpers for kinship detection and ancestor retrieval.
All probability distributions are calibrated to approximate pre-industrial
Polish demographic patterns.
"""

import random
from datetime import date
from typing import Set


def get_planned_children_count(current_living: int, target_living: int) -> int:
    """
    Return the number of children planned for a newly formed family.

    The fertility distribution is dynamically adjusted based on the ratio of
    the current living population to a target living threshold. When the
    population is well below target, higher child counts are favoured to
    accelerate growth; when it exceeds the target, lower counts are preferred
    to limit overshoot.
    """
    ratio = current_living / max(1, target_living)

    if ratio < 0.5:
        # Severe underpopulation — strongly favour large families.
        weights = [0.0, 0.0, 0.0, 0.05, 0.15, 0.25, 0.30, 0.15, 0.10]
    elif ratio < 0.7:
        # Moderate underpopulation — lean toward above-average family sizes.
        weights = [0.01, 0.02, 0.05, 0.20, 0.30, 0.25, 0.10, 0.05, 0.02]
    elif ratio < 0.9:
        # Near target — distribute around a typical family size.
        weights = [0.05, 0.10, 0.25, 0.30, 0.20, 0.08, 0.02, 0.0, 0.0]
    elif ratio > 1.3:
        # Significant overpopulation — strongly favour childlessness or small families.
        weights = [0.50, 0.30, 0.15, 0.05, 0.0, 0.0, 0.0, 0.0, 0.0]
    elif ratio > 1.1:
        # Mild overpopulation — prefer smaller families.
        weights = [0.25, 0.30, 0.30, 0.10, 0.05, 0.0, 0.0, 0.0, 0.0]
    else:
        # Population is at or near the target — use a balanced baseline distribution.
        weights = [0.12, 0.15, 0.30, 0.23, 0.12, 0.05, 0.02, 0.01, 0.0]

    return random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8], weights=weights, k=1)[0]


def get_widow_planned_children_count() -> int:
    """
    Return the planned child count for a remarried widow or widower.

    Remarriages are modelled with a reduced fertility expectation, reflecting
    both older parental age at remarriage and historically lower birth rates
    in second unions.
    """
    return random.choices([0, 1, 2, 3], weights=[0.40, 0.35, 0.20, 0.05], k=1)[0]


def get_marriage_age(sex: str) -> int:
    """
    Sample a target marriage age for an individual.

    Ages are drawn from a truncated Gaussian distribution calibrated separately
    for each sex. The sampling loop discards values outside the acceptable range
    to avoid biologically or historically implausible ages.
    """
    if sex == 'F':
        # Women: mean age 24, standard deviation 3.5, bounded to [16, 50].
        while True:
            age = int(random.gauss(24, 3.5))
            if 16 <= age <= 50: return age
    else:
        # Men: mean age 26, standard deviation 4, bounded to [18, 65].
        while True:
            age = int(random.gauss(26, 4))
            if 18 <= age <= 65: return age


def get_lifespan() -> int:
    """
    Sample a total lifespan in years for a newly created individual.

    A 15% probability of early childhood death (age 0–5) is applied first,
    reflecting historically high infant and child mortality rates. Surviving
    individuals receive a lifespan drawn from a truncated Gaussian distribution.
    """
    if random.random() < 0.15:
        # Childhood mortality: the individual dies before reaching age 6.
        return random.randint(0, 5)
    # Adult lifespan: mean 65 years, standard deviation 15, bounded to [6, 100].
    while True:
        lifespan = int(random.gauss(65, 15))
        if 6 <= lifespan <= 100: return lifespan


def get_ancestors_with_depth(person_id: int, max_depth: int, people: dict, families: dict) -> dict:
    """
    Return a dictionary mapping each ancestor ID to their minimum distance
    (in generations) from the given individual, up to max_depth generations.

    Performs a breadth-first traversal of the parent graph. The starting
    individual is excluded from the returned dictionary.
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


def get_ancestors_up_to_depth(person_id: int, max_depth: int, people: dict, families: dict) -> Set[int]:
    """
    Return the set of all ancestors of a given individual up to a specified depth.

    Performs a breadth-first traversal of the parent graph, collecting ancestor IDs
    at each generation level up to and including max_depth. The starting individual
    is excluded from the returned set.
    """
    return set(get_ancestors_with_depth(person_id, max_depth, people, families).keys())


def is_too_closely_related(p_a_id: int, p_b_id: int, people: dict, families: dict) -> bool:
    """
    Determine whether two individuals are too closely related to be permitted to marry.

    Returns True if any of the following conditions hold:
    - The two individuals are the same person.
    - One is a direct ancestor of the other (checked up to 7 generations).
    - They share a common ancestor for whom the sum of distances from both
      individuals is less than 7 (i.e., the combined generational distance
      through the shared ancestor is at most 6).
    """
    if p_a_id == p_b_id:
        return True

    if is_direct_ancestor(p_a_id, p_b_id, people, families) or is_direct_ancestor(p_b_id, p_a_id, people, families):
        return True

    # Collect ancestors with their minimum depths from each individual.
    # max_depth=5 is sufficient: the minimum distance on the other side is at least 1,
    # so any forbidden relationship has a combined distance of at most 6.
    anc_a = get_ancestors_with_depth(p_a_id, max_depth=5, people=people, families=families)
    anc_b = get_ancestors_with_depth(p_b_id, max_depth=5, people=people, families=families)

    for ancestor_id in set(anc_a) & set(anc_b):
        if anc_a[ancestor_id] + anc_b[ancestor_id] <= 6:
            return True

    return False


def is_direct_ancestor(older_id: int, younger_id: int, people: dict, families: dict) -> bool:
    """
    Determine whether one individual is a direct ancestor of another.

    Traverses the parent graph upward from younger_id up to 7 generations,
    returning True if older_id is encountered anywhere along the path.
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
    Generate a random calendar date within the given year.

    Day is limited to a maximum of 28 to ensure validity across all months
    without requiring month-specific day-range logic.
    """
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)


def adjust_surname(surname: str, sex: str) -> str:
    """
    Apply Polish grammatical feminization rules to a surname.

    Common masculine adjectival surname suffixes are replaced with their
    feminine equivalents. Surnames not matching any known pattern are
    returned unchanged.
    """
    if sex == 'F':
        if surname.endswith('ski'): return surname[:-3] + 'ska'
        if surname.endswith('cki'): return surname[:-3] + 'cka'
        if surname.endswith('dzki'): return surname[:-3] + 'dzka'
    return surname


def get_family_status() -> str:
    """
    Sample a legal status for a newly formed family union.

    The distribution strongly favours formal marriage, with small probabilities
    assigned to less formal or irregular arrangements.
    """
    return random.choices(['MARRIED', 'PARTNERS', 'OTHER', 'ANNULLED'],
                          weights=[0.90, 0.06, 0.03, 0.01], k=1)[0]


def get_child_relationship_type() -> str:
    """
    Sample the relationship type between a child and the family record.

    The overwhelming majority of children are biological; small probabilities
    are assigned to adoption and foster care arrangements.
    """
    return random.choices(['BIOLOGICAL', 'ADOPTED', 'FOSTER'],
                          weights=[0.96, 0.03, 0.01], k=1)[0]