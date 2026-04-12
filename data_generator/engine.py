import random
import os
from typing import Dict, Set, List, Optional
from models import Person, Family
from config import MALE_NAMES, FEMALE_NAMES, SURNAMES, PLACES, CAUSES_OF_DEATH, OCCUPATIONS, SEED, SCENARIOS
from demographics import (get_planned_children_count, get_marriage_age,
                          get_lifespan, is_too_closely_related, random_date,
                          adjust_surname, get_family_status, get_child_relationship_type)
from exporter import DataExporter
from analytics import AnalyticsEngine

class TargetReachedException(Exception):
    """
    Raised to cleanly halt the simulation loop the moment the number of generated
    individuals reaches target_population. This avoids checking the stop condition
    inside every call to _create_person separately.
    """
    pass

class SimulationEngine:
    """
    Core chronological simulation engine. Processes life events (births, marriages,
    divorces, deaths) year by year. Maintains in-memory data structures for people and families, as well as
    auxiliary indices for living individuals and active families to optimize event processing.
    Upon completion, triggers export and analysis routines.
    """

    def __init__(self, target_population: int, output_dir: Optional[str]):
        random.seed(SEED)
        self.target_population = target_population
        self.output_dir = output_dir
        
        config = SCENARIOS.get(target_population, SCENARIOS[1000])
        self.start_year = config['start_year']
        self.current_year = self.start_year

        self.next_person_id = 1
        self.next_family_id = 1

        self.people: Dict[int, Person] = {}
        self.families: Dict[int, Family] = {}

        self.living_people_ids: Set[int] = set()
        self.active_families: Set[int] = set()

        # Pre-scheduled births indexed by year: year → list of birth descriptor dicts
        self.planned_births: Dict[int, List[dict]] = {}

        # Logs population statistics at regular intervals for later analysis and visualization
        self.history_log = []

        # Store yearly population data in memory for analytics
        self.yearly_data: List[tuple] = []

        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)

    def _create_person(self, sex: str, raw_surname: str, birth_year: int,
                       parents_fam_id: Optional[int] = None, region_id: int = 0) -> Person:
        # Checking the limit here guarantees atomicity: we never exceed target_population
        if len(self.people) >= self.target_population:
            raise TargetReachedException()

        p_id = self.next_person_id
        self.next_person_id += 1
        name = random.choice(MALE_NAMES) if sex == 'M' else random.choice(FEMALE_NAMES)
        surname = adjust_surname(raw_surname, sex)
        lifespan = get_lifespan()
        target_marriage_age = get_marriage_age(sex)

        # Correction for founding population members who may already be of age at start year —
        # without this, some founders would die before they even enter the simulation loop
        age_now = self.current_year - birth_year
        if lifespan <= age_now and age_now > 0:
            lifespan = age_now + random.randint(5, 35)

        # 3% of the population remains celibate and is excluded from the matchmaking process
        is_celibate = random.random() < 0.03

        p = Person(
            id=p_id, given_name=name, surname=surname, sex=sex, is_deceased=False,
            birth_date=random_date(birth_year), birth_place=random.choice(PLACES),
            parents_family_id=parents_fam_id, birth_year=birth_year, lifespan=lifespan,
            is_celibate=is_celibate, region_id=region_id, target_marriage_age=target_marriage_age
        )
        self.people[p_id] = p
        self.living_people_ids.add(p_id)
        return p

    def _initialize_population(self, initial_pairs: int):
        """
        Bootstraps the graph with an unrelated founding population of married pairs.
        Pairs are distributed evenly across 5 geographic regions, which establishes
        the spatial structure used later during matchmaking.
        """
        for i in range(initial_pairs):
            reg = i % 5

            age_husband = random.randint(20, 50)
            age_wife = max(18, min(45, age_husband + random.randint(-10, 5)))

            # age_husband = random.randint(20, 28)
            # age_wife = max(18, min(25, age_husband + random.randint(-3, 2)))

            husband = self._create_person('M', random.choice(SURNAMES),
                                          self.start_year - age_husband, region_id=reg)
            wife = self._create_person('F', random.choice(SURNAMES),
                                       self.start_year - age_wife, region_id=reg)

            # self._create_marriage(husband, wife, self.start_year)
            marriage_year = self.start_year + random.randint(0, 15)
            self._create_marriage(husband, wife, marriage_year)

    def _generate_immigrant_pair(self):
        """
        Injects a new fertile couple into the simulation to bridge the generation gap
        and prevent birth rates from crashing to 0.
        """
        reg = random.randint(0, 4)

        # Give them realistic young adult ages (e.g., 20-28) to maximize their fertile window
        age_husband = random.randint(20, 28)
        age_wife = max(18, min(30, age_husband + random.randint(-5, 2)))

        husband = self._create_person('M', random.choice(SURNAMES),
                                      self.current_year - age_husband, region_id=reg)
        wife = self._create_person('F', random.choice(SURNAMES),
                                   self.current_year - age_wife, region_id=reg)

        self._create_marriage(husband, wife, self.current_year)

    def _create_marriage(self, husband: Person, wife: Person, year: int):
        f_id = self.next_family_id
        self.next_family_id += 1

        status = get_family_status()
        family = Family(
            id=f_id, status=status, marriage_date=random_date(year),
            marriage_place=random.choice(PLACES), husband_id=husband.id, wife_id=wife.id
        )
        self.families[f_id] = family
        self.active_families.add(f_id)

        husband.spouse_id = wife.id
        wife.spouse_id = husband.id
        husband.marriages_count += 1
        wife.marriages_count += 1

        # Occupation is assigned at marriage if not already set
        if not husband.occupation: husband.occupation = random.choice(OCCUPATIONS)
        if not wife.occupation: wife.occupation = random.choice(OCCUPATIONS)

        config = SCENARIOS.get(self.target_population, SCENARIOS[1000])
        avg_children = config['avg_children']

        # Subsequent marriages produce fewer children on average —
        # this accounts for the older age of the parents and a shorter remaining fertile period
        if husband.marriages_count > 1 or wife.marriages_count > 1:
            planned_count = get_planned_children_count(avg_children * 0.6)
        else:
            planned_count = get_planned_children_count(avg_children)

        # Births are scheduled upfront at the time of marriage rather than drawn each year —
        # this decouples fertility logic from the chronological iteration loop
        current_y = year
        for _ in range(planned_count):
            gap = random.choices([1, 2, 3], weights=[0.3, 0.5, 0.2], k=1)[0]
            current_y += gap
            
            # Female fertility ends after age 45
            if (current_y - wife.birth_year) > 45: break

            if current_y not in self.planned_births:
                self.planned_births[current_y] = []
            self.planned_births[current_y].append({
                'family_id': f_id, 'mother_id': wife.id, 'father_id': husband.id, 'region_id': husband.region_id
            })

    def _process_deaths(self):
        """
        Identify and process all individuals whose lifespan has been exhausted this year.

        Each deceased individual is assigned death metadata (date, place, cause, burial).
        Individuals who die without a recorded occupation and are at least 18 years old
        receive one at this point. If the deceased had a living spouse, the spouse's
        link is cleared and the shared family record is transitioned to WIDOWED status.
        """
        dead_this_year = set()

        for p_id in self.living_people_ids:
            p = self.people[p_id]

            if (self.current_year - p.birth_year) >= p.lifespan:
                self._process_single_death(p)
                dead_this_year.add(p_id)

        self.living_people_ids.difference_update(dead_this_year)

    def _process_single_death(self, p: Person):
        """
        Handles the death of a single individual, including metadata assignment and family status updates.
        """
        p.is_deceased = True
        p.death_date = random_date(self.current_year)
        p.death_place = random.choice(PLACES)
        p.cause_of_death = random.choice(CAUSES_OF_DEATH)
        p.burial_place = f"Cemetery in {p.death_place}"

        if not p.occupation and (self.current_year - p.birth_year) >= 18:
            p.occupation = random.choice(OCCUPATIONS)

        if p.spouse_id:
            spouse = self.people.get(p.spouse_id)
            if spouse and not spouse.is_deceased:
                spouse.spouse_id = None
                spouse.widowed_year = self.current_year

                for f_id in list(self.active_families):
                    fam = self.families[f_id]
                    if (fam.husband_id == p.id and fam.wife_id == spouse.id) or \
                            (fam.wife_id == p.id and fam.husband_id == spouse.id):
                        fam.status = 'WIDOWED'
                        self.active_families.remove(f_id)
                        break

    def _process_divorces(self):
        """
        A small percentage of marriages end in divorce each year. Divorces are processed after deaths to avoid
        complications with widowing. When a divorce occurs, the family status is updated, spouses are marked as ex-spouses of each other, 
        and the family is removed from the active pool to prevent further births. Divorced individuals can remarry, 
        but they will not be matched with their ex-spouse or any previous spouses.
        """
        divorced_this_year = []
        for f_id in self.active_families:
            if random.random() < 0.0005:  # Very low probability
                fam = self.families[f_id]
                fam.status = 'DIVORCED'
                husband = self.people.get(fam.husband_id)
                wife = self.people.get(fam.wife_id)
                if husband and wife:
                    husband.spouse_id = None
                    wife.spouse_id = None
                    husband.ex_spouses.add(wife.id)
                    wife.ex_spouses.add(husband.id)
                    divorced_this_year.append(f_id)

        for f_id in divorced_this_year:
            self.active_families.remove(f_id)

    def _process_births(self):
        """
        Executes births scheduled for the current year.
        Includes a biological reality check: a birth is skipped if the mother is deceased,
        too old, or if the father died more than a year before the planned birth year.
        """
        births_today = self.planned_births.get(self.current_year, [])
        for b in births_today:
            mother = self.people[b['mother_id']]
            father = self.people[b['father_id']]

            age_at_birth = self.current_year - mother.birth_year
            
            if not mother.is_deceased and age_at_birth <= 50:
                
                is_biologically_possible = True
                if father.is_deceased and father.death_date:
                    if father.death_date.year < self.current_year - 1:
                        is_biologically_possible = False

                if is_biologically_possible:
                    child_sex = random.choice(['M', 'F'])
                    child = self._create_person(
                        child_sex, father.surname, self.current_year,
                        parents_fam_id=b['family_id'],
                        region_id=b['region_id']
                    )
                    rel_type = get_child_relationship_type()
                    self.families[b['family_id']].children.append({'id': child.id, 'type': rel_type})

    def _process_marriages(self):
        """
        Matches eligible singles to form new families using a two-phase approach:
        first attempting to find a partner within their local region, and if
        unsuccessful, searching across other regions (triggering migration).
        """

        def _is_valid_partner(male, female):
            return (
                    female.spouse_id is None and
                    female.id not in male.ex_spouses and
                    not is_too_closely_related(male.id, female.id, self.people, self.families)
            )

        # Split singles by region — simulates geographic constraints on partner selection
        singles_m = {r: [] for r in range(5)}
        singles_f = {r: [] for r in range(5)}

        # Gather eligible singles
        for p_id in self.living_people_ids:
            p = self.people[p_id]
            if p.spouse_id is None and not p.is_celibate and p.widowed_year < self.current_year - 1:
                age = self.current_year - p.birth_year
                if p.sex == 'M' and p.target_marriage_age <= age < 65:
                    singles_m[p.region_id].append(p)
                elif p.sex == 'F' and p.target_marriage_age <= age < 50:
                    singles_f[p.region_id].append(p)

        # Shuffle regional pools to ensure fairness
        for r in range(5):
            random.shuffle(singles_m[r])
            random.shuffle(singles_f[r])

        # Combine all eligible men into a master list and shuffle
        males_to_marry = []
        for r in range(5):
            males_to_marry.extend(singles_m[r])
        random.shuffle(males_to_marry)

        # Matchmaking Loop
        for male in males_to_marry:
            married = False

            # First attempt: find a partner within the same region
            for female in singles_f[male.region_id]:
                if _is_valid_partner(male, female):
                    self._create_marriage(male, female, self.current_year)
                    married = True
                    break

            # If no local match is found, search across other regions (simulating migration for marriage)
            if not married:
                other_females = []
                for r in range(5):
                    if r != male.region_id:
                        other_females.extend(singles_f[r])

                random.shuffle(other_females)

                for female in other_females:
                    if _is_valid_partner(male, female):
                        self._create_marriage(male, female, self.current_year)

                        # The wife migrates to the husband's region
                        female.region_id = male.region_id
                        break

    def run(self):
        """Main chronological event loop — advances year by year until the target population is reached."""
        print(f"\nSimulation started from year {self.start_year}. "
              f"Target population: {self.target_population}.")

        config = SCENARIOS.get(self.target_population, SCENARIOS[1000])
        init_pairs = config['initial_pairs']

        self._initialize_population(initial_pairs=init_pairs)

        log_start = (f"Year {self.start_year}: Alive {len(self.living_people_ids)} people. "
                     f"Total generated: {len(self.people)}")
        self.history_log.append(log_start)
        print(log_start)

        self.yearly_data.append((self.start_year, len(self.living_people_ids)))

        try:
            while len(self.people) < self.target_population:
                self.current_year += 1

                config_scen = SCENARIOS.get(self.target_population, SCENARIOS[1000])
                immigrants_per_year = config_scen.get('immigrants', 1)

                offset = self.current_year - self.start_year

                if 20 <= offset <= 25:
                    for _ in range(immigrants_per_year):
                        self._generate_immigrant_pair()

                self._process_births()
                self._process_marriages()
                self._process_divorces()
                self._process_deaths()

                self.yearly_data.append((self.current_year, len(self.living_people_ids)))

                if (self.current_year - self.start_year) % 25 == 0:
                    log = (f"Year {self.current_year}: Alive {len(self.living_people_ids)} people. "
                           f"Total generated: {len(self.people)}")
                    self.history_log.append(log)
                    print(log)

                # Safety net against infinite loops caused by bad seeding or misconfiguration —
                # 3000 years is a value that should never be reached with valid parameters
                if self.current_year > self.start_year + 3000:
                    print("WARNING: Safety limit reached (3000 years).")
                    break

            log_end = (f"Year {self.current_year} (END): Alive {len(self.living_people_ids)} people. "
                       f"Total generated: {len(self.people)}")
            self.history_log.append(log_end)
            print(log_end)
            print(f"Success! Target of {len(self.people)} reached in year {self.current_year}.")

        except TargetReachedException:
            log_end = (f"Year {self.current_year} (END): Alive {len(self.living_people_ids)} people. "
                       f"Total generated: {len(self.people)}")
            self.history_log.append(log_end)
            print(log_end)
            print(f"Success! Target of {len(self.people)} people reached exactly in year {self.current_year}.")

        # Export and analysis run automatically, but only if an output directory is provided.
        if self.output_dir:
            exporter = DataExporter(self.people, self.families, self.target_population, self.output_dir)
            exporter.export_to_postgres_csv()
            exporter.export_to_neo4j_csv()

            print(f"[{self.target_population}] Starting post-simulation analysis...")
            analytics_engine = AnalyticsEngine(
                people=self.people,
                families=self.families,
                target_population=self.target_population,
                start_year=self.start_year,
                current_year=self.current_year,
                history_log=self.history_log,
                output_dir=self.output_dir,
                yearly_data=self.yearly_data
            )
            analytics_engine.run()