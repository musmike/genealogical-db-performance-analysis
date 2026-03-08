"""
Data models for the genealogical simulation.

Defines the two core entities — Person and Family — as lightweight
dataclasses. All simulation state is stored and passed using these structures.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Dict


@dataclass
class Person:
    """
    Represents a single simulated individual.

    Core biographical attributes are set at creation time. Optional fields
    (death details, occupation, spouse) are populated incrementally as the
    simulation progresses through annual processing steps.
    """

    # --- Identity ---
    id: int                         # Unique sequential identifier assigned at creation.
    given_name: str                 # Randomly selected from the appropriate name pool.
    surname: str                    # Inherited from the father; feminized for female individuals.
    sex: str                        # 'M' for male, 'F' for female.

    # --- Vital status ---
    is_deceased: bool               # Set to True when the individual's lifespan is exhausted.
    birth_date: date                # Randomly generated date within the birth year.
    birth_place: str                # Randomly selected from the PLACES pool.
    death_date: Optional[date] = None
    death_place: Optional[str] = None
    death_cause: Optional[str] = None
    burial_place: Optional[str] = None

    # --- Social attributes ---
    occupation: Optional[str] = None   # Assigned upon marriage or at the time of death.

    # --- Family linkage ---
    parents_family_id: Optional[int] = None  # References the Family record of the individual's parents.

    # --- Simulation internals ---
    birth_year: int = 0             # Integer birth year, used for age calculations.
    lifespan: int = 0               # Total number of years the individual will live.
    spouse_id: Optional[int] = None # Set when married; cleared upon divorce or spousal death.

    marriages_count: int = 0        # Tracks how many times the individual has been married.
    is_celibate: bool = False       # If True, the individual never enters the marriage pool.
    region_id: int = 0              # Geographic region (0–4), used to constrain marriage matching.
    target_marriage_age: int = 0    # The minimum age at which this individual becomes eligible to marry.


@dataclass
class Family:
    """
    Represents a marital union between two individuals.

    Tracks the legal status of the union and accumulates child records
    as births are processed during the simulation.
    """

    id: int                     # Unique sequential identifier assigned at creation.
    status: str                 # Current union status: MARRIED, PARTNERS, OTHER, ANNULLED, DIVORCED, or WIDOWED.
    marriage_date: date         # Randomly generated date within the marriage year.
    marriage_place: str         # Randomly selected from the PLACES pool.
    husband_id: int             # References the male partner's Person record.
    wife_id: int                # References the female partner's Person record.

    # Each entry is a dict with keys 'id' (child Person ID) and 'type' (relationship type).
    children: List[Dict[str, any]] = field(default_factory=list)