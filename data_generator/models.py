from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Dict, Set


@dataclass
class Person:
    """
    Represents a single node in the genealogical graph.
    Fields used only by the simulation engine (birth_year, lifespan, spouse_id, etc.)
    are runtime-only and are not exported to the database.
    """
    id: int
    given_name: str                 
    surname: str                 
    sex: str

    is_deceased: bool               
    birth_date: date                
    birth_place: str                
    death_date: Optional[date] = None
    death_place: Optional[str] = None
    cause_of_death: Optional[str] = None
    burial_place: Optional[str] = None
    occupation: Optional[str] = None   

    # Foreign key pointing to the family unit this person was born into or adopted by
    parents_family_id: Optional[int] = None  

    # Helper fields used by the simulation engine — not included in CSV export
    birth_year: int = 0             
    lifespan: int = 0               
    spouse_id: Optional[int] = None 
    marriages_count: int = 0        
    is_celibate: bool = False       
    region_id: int = 0              
    target_marriage_age: int = 0
    widowed_year: int = 0
    ex_spouses: Set[int] = field(default_factory=set)

@dataclass
class Family:
    """
    Represents the unit connecting parents and children in the genealogical graph.
    """
    id: int                     
    status: str                 
    marriage_date: date         
    marriage_place: str    
    husband_id: int            
    wife_id: int                

    # List of dicts specifying child id and relationship type, e.g. {'id': 123, 'type': 'BIOLOGICAL'}
    children: List[Dict[str, any]] = field(default_factory=list)