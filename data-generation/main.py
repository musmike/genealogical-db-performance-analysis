from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Set
import random


@dataclass
class Person:
    id: int
    given_name: str
    surname: str
    sex: str  # 'M' or 'F'
    is_living: bool
    birth_date: date
    birth_place: str
    death_date: Optional[date] = None
    death_place: Optional[str] = None
    death_cause: Optional[str] = None
    burial_place: Optional[str] = None
    occupation: Optional[str] = None

    # --- Helper fields for simulation (NOT saved to the database) ---
    parents_family_id: Optional[int] = None  # The family in which the person was born
    spousal_families: List[int] = field(default_factory=list)  # Families in which the person is a spouse
    generation: int = 1  # Used to track the depth in the family tree


@dataclass
class Family:
    id: int
    status: str # e.g., 'Married', 'Divorced', 'Widowed'
    marriage_date: date
    marriage_place: str
    husband_id: int
    wife_id: int

    # --- Helper fields for simulation (NOT saved to the database) ---
    children_ids: List[int] = field(default_factory=list)  # List of children IDs from this relationship
    planned_children_count: int = 0  # Randomly determined number of children for this couple at the start
    children_born_so_far: int = 0



def get_planned_children_count() -> int:
    """
    Returns a random number of children from the range 0-8.
    The weights have been chosen so that the average of a large sample is approximately 2.2 - 2.25.
    """

    # Possible number of children
    population = [0, 1, 2, 3, 4, 5, 6, 7, 8]

    # Probability (weights). Together they sum up to 1.0 (100%)
    weights =[
        0.17,  # 0 children - 17%
        0.17,  # 1 child - 17%
        0.28,  # 2 children - 28% (most common case)
        0.18,  # 3 children - 18%
        0.10,  # 4 children - 10%
        0.05,  # 5 children - 5%
        0.03,  # 6 children - 3%
        0.015, # 7 children - 1.5%
        0.005  # 8 children - 0.5% (very rare)
    ]

    return random.choices(population, weights=weights, k=1)[0]


def get_marriage_age(sex: str) -> int:
    """
    It draws the age of marriage. It uses a normal (Gaussian) distribution
    truncated to the extreme values imposed by the boundary conditions.
    """
    if sex == 'F':
        # Average 24, deviation 3.5
        # This will give a peak between 21 and 27. With rare cases of 16-19 and 35+.
        while True:
            age = int(random.gauss(24, 3.5))
            if 16 <= age <= 50:
                return age
    else: # 'M'
        while True:
            age = int(random.gauss(26, 4))
            if 18 <= age <= 65:
                return age


def get_lifespan() -> int:
    """
    Simulation of life expectancy taking into account infant/child mortality
    """

    # 15% chance of dying in childhood (ages 0-5) - makes historical data more realistic
    if random.random() < 0.15:
        return random.randint(0, 5)

    # If they survive early childhood, they live an average of 65 years (standard deviation 15 years).
    while True:
        lifespan = int(random.gauss(65, 15))
        if 6 <= lifespan <= 100:
            return lifespan


def plan_children_birth_years(marriage_year: int, wife_birth_year: int, planned_count: int) -> list[int]:
    """
    Called when creating a marriage.
    Determines the birth years of children, ensuring that the mother is no older than 45.
    """

    birth_years = []
    current_year = marriage_year

    for _ in range(planned_count):
        # Age gap between children: 1 to 4 years (usually 2 years)
        gap = random.choices([1, 2, 3, 4], weights=[0.2, 0.5, 0.2, 0.1], k=1)[0]
        current_year += gap

        wife_age = current_year - wife_birth_year

        if wife_age > 45:
            break

        birth_years.append(current_year)

    return birth_years


def get_ancestors_up_to_depth(person_id: int, max_depth: int, people: dict, families: dict) -> Set[int]:
    """
    Collects a set of IDs of all ancestors of a given person to a specified depth.
    Depth:
    1 = parents only
    2 = parents + grandparents
    3 = parents + grandparents + great-grandparents
    """

    ancestors = set()
    queue = [(person_id, 0)]

    while queue:
        current_id, depth = queue.pop(0)

        if depth > 0:
            ancestors.add(current_id)

        # If the generation limit has not been reached, the parents of that person are searched for.
        if depth < max_depth:
            person = people.get(current_id)
            if person and person.parents_family_id is not None:
                parent_family = families.get(person.parents_family_id)
                if parent_family:
                    if parent_family.husband_id is not None:
                        queue.append((parent_family.husband_id, depth + 1))
                    if parent_family.wife_id is not None:
                        queue.append((parent_family.wife_id, depth + 1))

    return ancestors

def is_too_closely_related(person_a_id: int, person_b_id: int, people: dict, families: dict) -> bool:
    """
    Checks whether two people are too closely related.
    The prohibition covers: siblings (depth 1), first cousins (depth 2),
    and second cousins (depth 3).
    This also includes intergenerational relationships (e.g., uncle-niece).
    """

    if person_a_id == person_b_id:
        return True

    ancestors_a = get_ancestors_up_to_depth(person_a_id, 3, people, families)
    ancestors_b = get_ancestors_up_to_depth(person_b_id, 3, people, families)

    ancestors_a.add(person_a_id)
    ancestors_b.add(person_b_id)

    common_ancestors = ancestors_a.intersection(ancestors_b)

    # If the intersection is not empty, it means they have a common ancestor <= 3 generations back.
    return len(common_ancestors) > 0













