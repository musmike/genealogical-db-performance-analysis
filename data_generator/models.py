from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Dict


@dataclass
class Person:
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

    parents_family_id: Optional[int] = None  

    birth_year: int = 0             
    lifespan: int = 0               
    spouse_id: Optional[int] = None 
    marriages_count: int = 0        
    is_celibate: bool = False       
    region_id: int = 0              
    target_marriage_age: int = 0    


@dataclass
class Family:
    id: int                     
    status: str                 
    marriage_date: date         
    marriage_place: str         
    husband_id: int            
    wife_id: int                

    children: List[Dict[str, any]] = field(default_factory=list)