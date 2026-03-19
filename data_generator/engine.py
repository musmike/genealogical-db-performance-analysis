"""
Core simulation engine for the genealogical population generator.

SimulationEngine drives year-by-year population dynamics: it initializes a
founding generation, then iterates forward in time processing deaths, divorces,
births, and marriages until the target population size is reached. On completion
it exports all records to CSV files (PostgreSQL-compatible and Neo4j-admin-import-
compatible) and runs a graph-analytics report covering LCA path lengths and
ancestor-retrieval metrics.
"""

import csv
import random
import os
import sys
from typing import Dict, Set, List, Optional
from models import Person, Family
from config import MALE_NAMES, FEMALE_NAMES, SURNAMES, PLACES, CAUSES_OF_DEATH, OCCUPATIONS, SEED, SCENARIOS
from demographics import (get_planned_children_count, get_widow_planned_children_count, get_marriage_age,
                          get_lifespan, is_too_closely_related, random_date,
                          adjust_surname, get_family_status, get_child_relationship_type)


# German city names that appear in the PLACES pool alongside their modern Polish equivalents.
# Used in the analytics report to count how many records require a place-name update.
GERMAN_TO_POLISH = {
    'Posen':    'Poznań',
    'Danzig':   'Gdańsk',
    'Breslau':  'Wrocław',
    'Stettin':  'Szczecin',
    'Bromberg': 'Bydgoszcz',
    'Thorn':    'Toruń',
}


class TargetReachedException(Exception):
    """Raised when the total number of generated individuals reaches the configured target."""
    pass


class SimulationEngine:
    """
    Year-by-year genealogical population simulator.

    The engine maintains dictionaries of Person and Family objects, tracks
    which individuals are currently alive and which families are still active,
    and schedules future births at the time each marriage is formed. All
    randomness is seeded once at construction time to guarantee reproducibility.
    """

    def __init__(self, start_year: int, end_year: int, target_population: int, output_dir: str):
        """
        Initialize the engine and prepare all internal data structures.

        Args:
            start_year:        The calendar year in which the simulation begins.
            end_year:          The latest calendar year the simulation may run to.
            target_population: The total number of individuals to generate before halting.
            output_dir:        Directory path where CSV exports and the analytics report are saved.
        """
        random.seed(SEED)

        self.start_year = start_year
        self.end_year = end_year
        self.target_population = target_population
        self.output_dir = output_dir
        self.current_year = start_year

        # Auto-incrementing ID counters for persons and families.
        self.next_person_id = 1
        self.next_family_id = 1

        # Primary data stores.
        self.people: Dict[int, Person] = {}
        self.families: Dict[int, Family] = {}

        # Living individuals and currently active (non-dissolved) family units.
        self.living_people_ids: Set[int] = set()
        self.active_families: Set[int] = set()

        # Births keyed by the year in which they are scheduled to occur.
        self.planned_births: Dict[int, List[dict]] = {}

        # Sequential log of population snapshots recorded at intervals during the run.
        self.history_log = []

        os.makedirs(self.output_dir, exist_ok=True)

    def create_person(self, sex: str, raw_surname: str, birth_year: int, parents_fam_id: Optional[int] = None,
                      region_id: int = 0) -> Person:
        """
        Instantiate a new Person and register them in the simulation.

        Raises TargetReachedException immediately if the population cap is reached,
        allowing the caller to abort further creation attempts cleanly.

        Args:
            sex:            'M' or 'F'.
            raw_surname:    Base surname before gender-based adjustment.
            birth_year:     Year of birth; used to compute current age and schedule death.
            parents_fam_id: ID of the Family record representing the individual's parents, if any.
            region_id:      Geographic region (0–4) used to constrain future marriage matching.

        Returns:
            The newly created and registered Person instance.
        """
        if len(self.people) >= self.target_population:
            raise TargetReachedException()

        p_id = self.next_person_id
        self.next_person_id += 1
        name = random.choice(MALE_NAMES) if sex == 'M' else random.choice(FEMALE_NAMES)
        surname = adjust_surname(raw_surname, sex)
        lifespan = get_lifespan()
        target_marriage_age = get_marriage_age(sex)

        # Ensure the individual's lifespan is not already exhausted at the moment of creation,
        # which can occur when back-dating birth years during population initialization.
        age_now = self.current_year - birth_year
        if lifespan <= age_now:
            lifespan = age_now + random.randint(5, 35)

        # A small fraction of individuals are designated as permanently celibate
        # and will never enter the marriage-matching pool.
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
        Create the founding generation as a set of already-married couples.

        Couples are distributed evenly across the five geographic regions.
        Both spouses are born slightly before the simulation start year so that
        they are of marriageable age from year one.
        """
        for i in range(initial_pairs):
            reg = i % 5
            husband = self.create_person('M', random.choice(SURNAMES), self.start_year - random.randint(20, 30),
                                         region_id=reg)
            wife = self.create_person('F', random.choice(SURNAMES), self.start_year - random.randint(18, 28),
                                      region_id=reg)
            self._create_marriage(husband, wife, self.start_year)

    def _create_marriage(self, husband: Person, wife: Person, year: int):
        """
        Form a family unit between two individuals and schedule their future children.

        A Family record is created and registered as active. Both spouses are linked
        to each other, receive an occupation if not already assigned, and the number
        of planned children is sampled and distributed across future years.

        The planned child count uses a dynamic fertility model: the target living
        population at marriage time is estimated from remaining years and outstanding
        population deficit, then used to calibrate the fertility distribution.
        Remarriages (either spouse has been married before) use a reduced fertility model.

        Args:
            husband: The male partner.
            wife:    The female partner.
            year:    The calendar year of the marriage.
        """
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

        if not husband.occupation: husband.occupation = random.choice(OCCUPATIONS)
        if not wife.occupation: wife.occupation = random.choice(OCCUPATIONS)

        # Estimate the number of living individuals the simulation should maintain
        # to stay on track for reaching the target population by the end year.
        years_left = max(1, self.end_year - self.current_year)
        people_to_generate = max(1, self.target_population - len(self.people))

        dynamic_target_living = int((people_to_generate / years_left) * 50)

        # Enforce a minimum living-population floor to prevent the fertility model from
        # collapsing into near-zero birth rates when the living count temporarily spikes.
        if self.target_population <= 1000:
            min_biological_floor = 120
        elif self.target_population <= 10000:
            min_biological_floor = 350
        else:
            min_biological_floor = 1500

        dynamic_target_living = max(dynamic_target_living, min_biological_floor)

        if husband.marriages_count > 1 or wife.marriages_count > 1:
            planned_count = get_widow_planned_children_count()
        else:
            planned_count = get_planned_children_count(len(self.living_people_ids), dynamic_target_living)

        # Distribute births across subsequent years, spacing them by a random inter-birth interval.
        # Births are capped at the mother's 45th birthday to reflect biological limits.
        current_y = year
        for _ in range(planned_count):
            gap = random.choices([1, 2, 3], weights=[0.3, 0.5, 0.2], k=1)[0]
            current_y += gap
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
        dead_this_year = []
        for p_id in self.living_people_ids:
            p = self.people[p_id]
            if (self.current_year - p.birth_year) >= p.lifespan:
                p.is_deceased = True
                p.death_date = random_date(self.current_year)
                p.death_place = random.choice(PLACES)
                p.cause_of_death = random.choice(CAUSES_OF_DEATH)
                p.burial_place = f"Cemetery in {p.death_place}"

                if not p.occupation and (self.current_year - p.birth_year) >= 18:
                    p.occupation = random.choice(OCCUPATIONS)

                dead_this_year.append(p_id)

                if p.spouse_id:
                    spouse = self.people.get(p.spouse_id)
                    if spouse and not spouse.is_deceased:
                        spouse.spouse_id = None
                        for f_id in list(self.active_families):
                            fam = self.families[f_id]
                            if (fam.husband_id == p.id and fam.wife_id == spouse.id) or \
                                    (fam.wife_id == p.id and fam.husband_id == spouse.id):
                                fam.status = 'WIDOWED'
                                self.active_families.remove(f_id)

        for p_id in dead_this_year:
            self.living_people_ids.remove(p_id)

    def _process_divorces(self):
        """
        Apply a small annual probability of divorce to each active family.

        Dissolved families are removed from the active set and both spouses
        have their spousal links cleared, making them eligible to remarry.
        """
        divorced_this_year = []
        for f_id in self.active_families:
            if random.random() < 0.005:
                fam = self.families[f_id]
                fam.status = 'DIVORCED'
                husband = self.people.get(fam.husband_id)
                wife = self.people.get(fam.wife_id)
                if husband and wife:
                    husband.spouse_id = None
                    wife.spouse_id = None
                    divorced_this_year.append(f_id)

        for f_id in divorced_this_year:
            self.active_families.remove(f_id)

    def _process_births(self):
        """
        Deliver all children scheduled for the current year.

        A child is only created if the mother is still alive. The child inherits
        the father's surname (feminized if female), is assigned to the same
        geographic region as the father, and is linked to the parents' family record
        with a sampled relationship type (biological, adopted, or foster).
        """
        births_today = self.planned_births.get(self.current_year, [])
        for b in births_today:
            mother = self.people[b['mother_id']]
            father = self.people[b['father_id']]

            if not mother.is_deceased:
                child_sex = random.choice(['M', 'F'])
                child = self.create_person(
                    child_sex, father.surname, self.current_year,
                    parents_fam_id=b['family_id'],
                    region_id=b['region_id']
                )
                rel_type = get_child_relationship_type()
                self.families[b['family_id']].children.append({'id': child.id, 'type': rel_type})

    def _process_marriages(self):
        """
        Match eligible single individuals into new marriages for the current year.

        Candidates are collected per region and sex. Each male is first offered
        a match within his own region (99% probability); if no compatible female
        is found there, the search falls back to other regions in random order.
        Compatibility is determined by is_too_closely_related(): candidates who
        share recent common ancestry are excluded from being matched.
        """
        singles_m = {0: [], 1: [], 2: [], 3: [], 4: []}
        singles_f = {0: [], 1: [], 2: [], 3: [], 4: []}

        for p_id in self.living_people_ids:
            p = self.people[p_id]
            if p.spouse_id is None and not p.is_celibate:
                age = self.current_year - p.birth_year
                if p.sex == 'M' and p.target_marriage_age <= age < 65:
                    singles_m[p.region_id].append(p)
                elif p.sex == 'F' and p.target_marriage_age <= age < 50:
                    singles_f[p.region_id].append(p)

        # Shuffle within each region to randomize match order.
        for r in range(5):
            random.shuffle(singles_m[r])
            random.shuffle(singles_f[r])

        for r_m in range(5):
            for male in singles_m[r_m]:
                target_reg = r_m if random.random() < 0.99 else random.choice(
                    [x for x in range(5) if x != r_m] or [r_m])
                married = False

                # Attempt to find a compatible partner in the preferred region.
                for i, female in enumerate(singles_f[target_reg]):
                    if not is_too_closely_related(male.id, female.id, self.people, self.families):
                        self._create_marriage(male, female, self.current_year)
                        singles_f[target_reg].pop(i)
                        married = True
                        break

                # If no match was found, search all remaining regions before giving up.
                if not married:
                    other_regions = [x for x in range(5) if x != target_reg]
                    random.shuffle(other_regions)
                    for fallback_reg in other_regions:
                        for i, female in enumerate(singles_f[fallback_reg]):
                            if not is_too_closely_related(male.id, female.id, self.people, self.families):
                                self._create_marriage(male, female, self.current_year)
                                singles_f[fallback_reg].pop(i)
                                married = True
                                break
                        if married:
                            break

    def export_to_postgres_csv(self):
        """
        Write all simulation records to three CSV files in the output directory.

        Files are written to a postgres/ subdirectory to keep them separate
        from the Neo4j export.

        Files produced:
        - people.csv:          One row per individual with biographical attributes.
        - families.csv:        One row per family unit with marriage metadata.
        - family_children.csv: One row per parent-child link with relationship type.
        """
        pg_dir = os.path.join(self.output_dir, 'postgres')
        os.makedirs(pg_dir, exist_ok=True)

        with open(f'{pg_dir}/people.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(
                ['id', 'given_name', 'surname', 'sex', 'is_deceased', 'birth_place', 'birth_date', 'death_place',
                 'death_date', 'cause_of_death', 'burial_place', 'occupation'])
            for p in self.people.values():
                writer.writerow([
                    p.id, p.given_name, p.surname, p.sex, 1 if p.is_deceased else 0,
                    p.birth_place, p.birth_date.isoformat() if p.birth_date else '',
                    p.death_place if p.is_deceased else '',
                    p.death_date.isoformat() if p.death_date else '',
                    p.cause_of_death if p.is_deceased else '',
                    p.burial_place if p.is_deceased else '',
                    p.occupation
                ])

        with open(f'{pg_dir}/families.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'status', 'marriage_date', 'marriage_place', 'husband_id', 'wife_id'])
            for fam in self.families.values():
                writer.writerow([
                    fam.id, fam.status, fam.marriage_date.isoformat() if fam.marriage_date else '',
                    fam.marriage_place, fam.husband_id, fam.wife_id
                ])

        with open(f'{pg_dir}/family_children.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['family_id', 'child_id', 'relationship_type'])
            for fam in self.families.values():
                for child_dict in fam.children:
                    writer.writerow([fam.id, child_dict['id'], child_dict['type']])

        print(f"[{self.target_population}] PostgreSQL CSV export complete → {pg_dir}/")

    def export_to_neo4j_csv(self):
        """
        Write Neo4j-admin-import-compatible CSV files to <output_dir>/neo4j/.

        neo4j-admin database import requires:
          • Node files   — header column ':ID' (with optional ID-space) plus ':LABEL'
          • Rel files    — ':START_ID', ':END_ID', ':TYPE'

        Property names follow Neo4j camelCase convention.

        Files produced:
        - nodes_person.csv:    Every Person record as a Neo4j node labelled 'Person'.
        - nodes_family.csv:    Every Family record as a Neo4j node labelled 'Family'.
        - rels_husband_of.csv: HUSBAND_OF relationship: husband Person → Family node.
        - rels_wife_of.csv:    WIFE_OF relationship: wife Person → Family node.
        - rels_child_of.csv:   HAS_CHILD relationship: Family node → child Person,
                               with 'relationshipType' property.

        Import command (run from Neo4j home, database must be stopped):

            neo4j-admin database import full \\
              --database=genealogy \\
              --nodes=Person=neo4j/nodes_person.csv \\
              --nodes=Family=neo4j/nodes_family.csv \\
              --relationships=HUSBAND_OF=neo4j/rels_husband_of.csv \\
              --relationships=WIFE_OF=neo4j/rels_wife_of.csv \\
              --relationships=HAS_CHILD=neo4j/rels_child_of.csv \\
              --overwrite-destination
        """
        neo4j_dir = os.path.join(self.output_dir, 'neo4j')
        os.makedirs(neo4j_dir, exist_ok=True)

        # ---- Person nodes -----------------------------------------------
        with open(f'{neo4j_dir}/nodes_person.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id:ID(Person)',
                'givenName:STRING',
                'surname:STRING',
                'sex:STRING',
                'isDeceased:BOOLEAN',
                'birthPlace:STRING',
                'birthDate:DATE',
                'deathPlace:STRING',
                'deathDate:DATE',
                'causeOfDeath:STRING',
                'burialPlace:STRING',
                'occupation:STRING',
                ':LABEL'
            ])
            for p in self.people.values():
                writer.writerow([
                    p.id,
                    p.given_name,
                    p.surname,
                    p.sex,
                    'true' if p.is_deceased else 'false',
                    p.birth_place,
                    p.birth_date.isoformat() if p.birth_date else '',
                    p.death_place if p.is_deceased else '',
                    p.death_date.isoformat() if p.death_date else '',
                    p.cause_of_death if p.is_deceased else '',
                    p.burial_place if p.is_deceased else '',
                    p.occupation if p.occupation else '',
                    'Person'
                ])

        # ---- Family nodes ------------------------------------------------
        with open(f'{neo4j_dir}/nodes_family.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id:ID(Family)',
                'status:STRING',
                'marriageDate:DATE',
                'marriagePlace:STRING',
                ':LABEL'
            ])
            for fam in self.families.values():
                writer.writerow([
                    fam.id,
                    fam.status,
                    fam.marriage_date.isoformat() if fam.marriage_date else '',
                    fam.marriage_place,
                    'Family'
                ])

        # ---- HUSBAND_OF relationships ------------------------------------
        with open(f'{neo4j_dir}/rels_husband_of.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([':START_ID(Person)', ':END_ID(Family)', ':TYPE'])
            for fam in self.families.values():
                if fam.husband_id:
                    writer.writerow([fam.husband_id, fam.id, 'HUSBAND_OF'])

        # ---- WIFE_OF relationships ---------------------------------------
        with open(f'{neo4j_dir}/rels_wife_of.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([':START_ID(Person)', ':END_ID(Family)', ':TYPE'])
            for fam in self.families.values():
                if fam.wife_id:
                    writer.writerow([fam.wife_id, fam.id, 'WIFE_OF'])

        # ---- HAS_CHILD relationships (Family → Person) -------------------
        # Direction: Family is the source, Person (child) is the target.
        # Spouses point into the family node (HUSBAND_OF / WIFE_OF); children
        # flow outward from it, which makes traversal patterns more natural.
        with open(f'{neo4j_dir}/rels_child_of.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([':START_ID(Family)', ':END_ID(Person)', 'relationshipType:STRING', ':TYPE'])
            for fam in self.families.values():
                for child_dict in fam.children:
                    writer.writerow([fam.id, child_dict['id'], child_dict['type'], 'HAS_CHILD'])

        print(f"[{self.target_population}] Neo4j CSV export complete → {neo4j_dir}/")

    def run_analytics(self):
        """
        Compute and write a graph-analytics report for the completed simulation.

        All traversals in this report follow biological relationships only.
        Adopted and foster children are excluded from every graph scenario.

        The report covers the following items:

        1. Population growth log — snapshots recorded during the simulation run.

        2. Graph topology — the maximum generational depth of the family tree,
           measured as the longest path from any root individual (no parents) to
           any descendant, following biological links only.

        3. LCA (Lowest Common Ancestor) search — biological paths only. A
           randomized search over pairs of young individuals from different
           regions to find a pair whose shortest biological path through a
           common ancestor matches the configured target length.

        4. Ancestor retrieval scenario — biological paths only. Identifies the
           individual with the greatest number of distinct biological ancestors
           within the configured depth limit.

        5. Descendant retrieval scenario — biological paths only. Identifies the
           individual with the greatest number of distinct biological descendants
           within the configured depth limit.

        6. Surname and birth year filter scenario — selects a surname and 50-year
           birth window that returns a representative result set.

        7. Births per city per quarter-century — counts births grouped by place
           and 25-year period across the top 10 cities by birth volume.

        8. Youngest parent scenario — biological relationships only. Identifies
           the person who had their first biological child at the youngest age.

        9. Insert/Delete test candidate — identifies an adopted person with no
           biological parents in the dataset, recommended as the anchor for
           manual insert/delete benchmark queries.

        10. Place name update scope — row counts for the German-to-Polish city
            name migration.

        Results are written to summary.txt in the output directory.
        """
        from collections import Counter, defaultdict

        config = SCENARIOS.get(self.target_population, {'min_lca_path': 8, 'max_lca_path': 99, 'ancestors_depth': 5})
        target_lca_min = config['min_lca_path']
        target_lca_max = config.get('max_lca_path', 999)
        target_ancestors_depth = config['ancestors_depth']

        # Descendant traversal depth is deliberately shallower than ancestor depth:
        # the descendant tree fans out exponentially, so smaller N already yields
        # a large and representative result set. Controlled via SCENARIOS in config.py.
        target_descendants_depth = config.get('descendants_depth', 3 if self.target_population <= 1000
            else (6 if self.target_population <= 10000 else 10))

        if target_lca_min == target_lca_max:
            target_label = str(target_lca_min)
        else:
            target_label = f"{target_lca_min}-{target_lca_max}"

        # ------------------------------------------------------------------
        # Helper: check whether a person's link to their parents_family_id
        # is biological (i.e. their entry in fam.children has type 'BIOLOGICAL').
        # ------------------------------------------------------------------
        def is_biological_child(p_id):
            p = self.people.get(p_id)
            if not p or not p.parents_family_id:
                return False
            fam = self.families.get(p.parents_family_id)
            if not fam:
                return False
            return any(c['id'] == p_id and c['type'] == 'BIOLOGICAL' for c in fam.children)

        filepath = os.path.join(self.output_dir, 'summary.txt')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=== GRAPH AND LCA ANALYSIS REPORT ===\n")
            f.write(f"Target population: {self.target_population}\n")
            f.write(f"Total people generated: {len(self.people)}\n")
            f.write(f"People alive at end of simulation ({self.current_year}): {len(self.living_people_ids)}\n")
            f.write(f"Total families: {len(self.families)}\n")
            f.write("Note: all graph traversals follow biological relationships only.\n\n")

            # ── 1. POPULATION GROWTH ──────────────────────────────────────────
            f.write("--- POPULATION GROWTH OVER TIME ---\n")
            for log in self.history_log:
                f.write(log + "\n")
            f.write("\n")

            # ── 2. GRAPH TOPOLOGY ─────────────────────────────────────────────
            # Compute generational depth via a single forward pass over IDs in
            # insertion order (parents always have lower IDs than children).
            # Only biological parent links are followed.
            depths = {}
            max_depth = 0
            for p_id in sorted(self.people.keys()):
                p = self.people[p_id]
                if is_biological_child(p_id):
                    fam = self.families[p.parents_family_id]
                    d_husband = depths.get(fam.husband_id, 0) if fam.husband_id else 0
                    d_wife    = depths.get(fam.wife_id, 0)    if fam.wife_id    else 0
                    d = max(d_husband, d_wife) + 1
                else:
                    d = 1
                depths[p_id] = d
                if d > max_depth:
                    max_depth = d

            f.write("--- GRAPH TOPOLOGY ---\n")
            f.write(f"Max graph depth (biological links only, oldest ancestor to youngest descendant): {max_depth} generations.\n\n")

            # Sample pool shared by LCA, ancestor retrieval and descendant retrieval.
            if self.target_population >= 100000:
                sample_size = 8000
            elif self.target_population >= 10000:
                sample_size = 4000
            else:
                sample_size = 2000

            youngest_ids = sorted(
                [p.id for p in self.people.values()],
                key=lambda x: self.people[x].birth_date,
                reverse=True
            )[:sample_size]

            # ── 3. LCA SEARCH ─────────────────────────────────────────────────
            # Bucket sampled individuals by region to enforce cross-region pairs.
            regions = {0: [], 1: [], 2: [], 3: [], 4: []}
            for p_id in youngest_ids:
                regions[self.people[p_id].region_id].append(p_id)

            bfs_limit = (target_lca_max // 2) + 10

            def get_ancestors_biological(p_id, limit):
                """
                BFS upward through biological parent links only.
                Returns a dict mapping ancestor IDs to their distance from p_id.
                Traversal is capped at 'limit' steps.
                """
                ancestors_paths = {p_id: 0}
                queue = [(p_id, 0)]
                while queue:
                    curr_id, dist = queue.pop(0)
                    if dist >= limit:
                        continue
                    if not is_biological_child(curr_id):
                        continue
                    fam = self.families[self.people[curr_id].parents_family_id]
                    for parent_id in (fam.husband_id, fam.wife_id):
                        if parent_id and parent_id not in ancestors_paths:
                            ancestors_paths[parent_id] = dist + 1
                            queue.append((parent_id, dist + 1))
                return ancestors_paths

            max_distance  = 0
            best_pair_info = None
            iterations    = 1500

            for i in range(iterations):
                msg = (f"\r[{self.target_population}] LCA search: {i + 1}/{iterations} | best so far: {max_distance} "
                       f"(target: {target_label})    ")
                sys.stdout.write(msg)
                sys.stdout.flush()

                available_regions = [r for r in regions if regions[r]]
                if len(available_regions) < 2:
                    break

                r1, r2 = random.sample(available_regions, 2)
                p1_id  = random.choice(regions[r1])
                p2_id  = random.choice(regions[r2])

                if not is_too_closely_related(p1_id, p2_id, self.people, self.families):
                    anc1 = get_ancestors_biological(p1_id, bfs_limit)
                    anc2 = get_ancestors_biological(p2_id, bfs_limit)

                    common = set(anc1.keys()).intersection(set(anc2.keys()))
                    # Both individuals must be at least 4 biological steps from the LCA.
                    valid_lcas = [x for x in common if anc1[x] > 3 and anc2[x] > 3]

                    if valid_lcas:
                        min_total_dist = min(anc1[x] + anc2[x] for x in valid_lcas)

                        if min_total_dist > max_distance and min_total_dist <= target_lca_max:
                            max_distance = min_total_dist
                            lcas_at_min  = [x for x in valid_lcas if anc1[x] + anc2[x] == min_total_dist]
                            lca_details  = [(x, anc1[x], anc2[x]) for x in lcas_at_min]

                            best_pair_info = {
                                'p1': p1_id, 'p2': p2_id,
                                'lcas': lca_details,
                                'dist1': lca_details[0][1],
                                'dist2': lca_details[0][2],
                                'total_dist': max_distance
                            }

                            if target_lca_min <= max_distance <= target_lca_max:
                                sys.stdout.write("\n")
                                sys.stdout.flush()
                                f.write(f"(Target value of {target_label} reached at iteration {i + 1}. Stopping search early.)\n")
                                break
            else:
                sys.stdout.write("\n")
                sys.stdout.flush()

            f.write("--- SCENARIO: LOWEST COMMON ANCESTOR (LCA) SEARCH ---\n")
            f.write("Biological relationships only.\n")
            f.write(f"Target LCA path length required: {target_label}\n")
            f.write("Constraint: Person A and Person B are not closely related AND\n")
            f.write("            biological distance to LCA > 3 for both sides.\n")

            if best_pair_info:
                if best_pair_info['total_dist'] < target_lca_min:
                    f.write(
                        f"[WARNING] Best found path ({best_pair_info['total_dist']}) is BELOW the required value "
                        f"({target_label}). Likely caused by pedigree collapse - consider changing SEED in config.py.\n"
                    )
                elif best_pair_info['total_dist'] > target_lca_max:
                    f.write(
                        f"[WARNING] Best found path ({best_pair_info['total_dist']}) EXCEEDS the required value "
                        f"({target_label}). Consider lowering the target in config.py.\n"
                    )
                f.write("Recommended for graph querying research:\n")
                f.write(f"- Person A (ID: {best_pair_info['p1']})\n")
                f.write(f"- Person B (ID: {best_pair_info['p2']})\n")
                f.write(f"Path length from Person A to LCA: {best_pair_info['dist1']}\n")
                f.write(f"Path length from Person B to LCA: {best_pair_info['dist2']}\n")
                f.write(f"Total path length between A and B: {best_pair_info['total_dist']}\n")
                f.write(f"Number of distinct LCAs at this exact shortest distance: {len(best_pair_info['lcas'])}\n")
                f.write("List of LCA IDs with their individual distances:\n")
                for lca_id, dist_a, dist_b in best_pair_info['lcas']:
                    f.write(f"  - LCA ID: {lca_id} (Dist A: {dist_a}, Dist B: {dist_b})\n")
                f.write("\n")
            else:
                f.write("No common biological ancestors found satisfying the strict criteria.\n\n")

            # ── 4. ANCESTOR RETRIEVAL SCENARIO ───────────────────────────────
            f.write("--- SCENARIO: ANCESTOR RETRIEVAL ---\n")
            f.write("Biological relationships only.\n")
            f.write(f"Objective: Find person with most distinct biological ancestors up to {target_ancestors_depth} generations back.\n")

            best_ancestor_count = 0
            best_ancestor_person_id = None
            sample_for_ancestors = youngest_ids[:200]

            for p_id in sample_for_ancestors:
                distinct_ancestors = set()
                visited = {p_id}
                queue   = [(p_id, 0)]
                while queue:
                    curr, d = queue.pop(0)
                    if d >= target_ancestors_depth:
                        continue
                    if not is_biological_child(curr):
                        continue
                    fam = self.families[self.people[curr].parents_family_id]
                    for parent_id in (fam.husband_id, fam.wife_id):
                        if parent_id and parent_id not in visited:
                            visited.add(parent_id)
                            distinct_ancestors.add(parent_id)
                            queue.append((parent_id, d + 1))

                count = len(distinct_ancestors)
                if count > best_ancestor_count:
                    best_ancestor_count     = count
                    best_ancestor_person_id = p_id

            if best_ancestor_person_id:
                f.write(f"Recommended Person ID: {best_ancestor_person_id}\n")
                f.write(f"Distinct biological ancestors found (depth <= {target_ancestors_depth}): {best_ancestor_count}\n")
                theoretical_max = sum(2 ** i for i in range(1, target_ancestors_depth + 1))
                f.write(f"Theoretical max (Perfect Tree): {theoretical_max}\n")
                if target_ancestors_depth > 10:
                    f.write("(Note: High pedigree collapse is biologically expected here.)\n")
            else:
                f.write("Could not find any biological ancestors for the sampled group.\n")
            f.write("\n")

            # ── 5. DESCENDANT RETRIEVAL SCENARIO ─────────────────────────────
            f.write("--- SCENARIO: DESCENDANT RETRIEVAL ---\n")
            f.write("Biological relationships only.\n")
            f.write(f"Objective: Find person with most distinct biological descendants up to {target_descendants_depth} generations forward.\n")
            # Build a map: person_id -> list of biological child IDs, for fast downward traversal.
            bio_children_map = defaultdict(list)
            for fam in self.families.values():
                for child_dict in fam.children:
                    if child_dict['type'] == 'BIOLOGICAL':
                        if fam.husband_id:
                            bio_children_map[fam.husband_id].append(child_dict['id'])
                        if fam.wife_id:
                            bio_children_map[fam.wife_id].append(child_dict['id'])

            best_descendant_count     = 0
            best_descendant_person_id = None
            # Sample up to 500 candidates from all persons to keep runtime bounded.
            all_ids = list(self.people.keys())
            sample_for_descendants = random.sample(all_ids, min(500, len(all_ids)))

            for p_id in sample_for_descendants:
                distinct_descendants = set()
                visited = {p_id}
                queue   = [(p_id, 0)]
                while queue:
                    curr, d = queue.pop(0)
                    if d >= target_descendants_depth:
                        continue
                    for child_id in bio_children_map.get(curr, []):
                        if child_id not in visited:
                            visited.add(child_id)
                            distinct_descendants.add(child_id)
                            queue.append((child_id, d + 1))

                count = len(distinct_descendants)
                if count > best_descendant_count:
                    best_descendant_count     = count
                    best_descendant_person_id = p_id

            if best_descendant_person_id:
                dp = self.people[best_descendant_person_id]
                f.write(f"Recommended Person ID: {best_descendant_person_id}\n")
                f.write(f"Name: {dp.given_name} {dp.surname}\n")
                f.write(f"Birth year: {dp.birth_year}\n")
                f.write(f"Distinct biological descendants found (depth <= {target_descendants_depth}): {best_descendant_count}\n")
            else:
                f.write("Could not find any biological descendants for the sampled group.\n")
            f.write("\n")

            # ── 6. SURNAME + BIRTH YEAR FILTER SCENARIO ──────────────────────
            surname_counts = Counter(p.surname for p in self.people.values())
            top_surnames   = [s for s, _ in surname_counts.most_common(5)]
            best_surname   = None
            best_year_start = None
            best_count      = 0
            target_min = max(5, len(self.people) // 20)
            target_max = max(20, len(self.people) // 8)

            for surname in top_surnames:
                birth_years = sorted(p.birth_year for p in self.people.values() if p.surname == surname)
                if len(birth_years) < 2:
                    continue
                for start in range(birth_years[0], birth_years[-1] - 49):
                    cnt = sum(1 for y in birth_years if start <= y < start + 50)
                    if target_min <= cnt <= target_max:
                        if best_surname is None or abs(cnt - target_min) < abs(best_count - target_min):
                            best_surname    = surname
                            best_year_start = start
                            best_count      = cnt

            f.write("--- SCENARIO: FILTERING BY SURNAME AND BIRTH YEAR RANGE ---\n")
            if best_surname:
                f.write(f"Recommended surname: {best_surname}\n")
                f.write(f"Recommended birth year range: {best_year_start}-{best_year_start + 49}\n")
                f.write(f"Matching records in dataset: {best_count}\n\n")
            else:
                fallback    = top_surnames[0] if top_surnames else 'Nowak'
                all_years   = sorted(p.birth_year for p in self.people.values() if p.surname == fallback)
                yr_start    = all_years[len(all_years) // 4] if all_years else self.start_year
                cnt         = sum(1 for p in self.people.values()
                                  if p.surname == fallback and yr_start <= p.birth_year < yr_start + 50)
                f.write(f"Recommended surname: {fallback}\n")
                f.write(f"Recommended birth year range: {yr_start}-{yr_start + 49}\n")
                f.write(f"Matching records in dataset: {cnt}\n\n")

            # ── 7. BIRTHS PER CITY PER QUARTER-CENTURY ───────────────────────
            births_by_city_quarter = defaultdict(lambda: defaultdict(int))
            for p in self.people.values():
                quarter = (p.birth_year // 25) * 25
                births_by_city_quarter[p.birth_place][quarter] += 1

            city_totals = {city: sum(q.values()) for city, q in births_by_city_quarter.items()}
            top_cities  = sorted(city_totals, key=city_totals.get, reverse=True)[:10]

            top_cities_alpha = sorted(top_cities)
            f.write("--- SCENARIO: BIRTHS PER CITY PER QUARTER-CENTURY (top 10 cities) ---\n")
            f.write("Cities: " + ", ".join(top_cities_alpha) + "\n")
            for city in top_cities_alpha:
                quarters = births_by_city_quarter[city]
                f.write(f"  {city} (total: {city_totals[city]}):\n")
                for quarter in sorted(quarters):
                    f.write(f"    {quarter}-{quarter + 24}: {quarters[quarter]}\n")
            f.write("\n")

            # ── 8. YOUNGEST PARENT SCENARIO ──────────────────────────────────
            # Collect all parents (both sexes) tied at the minimum age, then report
            # every one of them — there may be multiple individuals, male or female,
            # who had their first biological child at exactly the same age.
            f.write("--- SCENARIO: YOUNGEST PARENT ---\n")
            f.write("Biological relationships only. Both sexes considered.\n")

            youngest_parent_age = None
            # Maps parent_id -> age-at-first-biological-child (running minimum per parent).
            parent_first_child_age: dict = {}

            for fam in self.families.values():
                for child_dict in fam.children:
                    if child_dict['type'] != 'BIOLOGICAL':
                        continue
                    child = self.people.get(child_dict['id'])
                    if not child:
                        continue
                    for parent_id in (fam.husband_id, fam.wife_id):
                        parent = self.people.get(parent_id)
                        if not parent:
                            continue
                        if not child.birth_date or not parent.birth_date:
                            continue
                        age = (child.birth_date.year - parent.birth_date.year
                            - ((child.birth_date.month, child.birth_date.day)
                                < (parent.birth_date.month, parent.birth_date.day)))
                        if age < 0:
                            continue
                        # Keep the earliest (youngest-age) child per parent.
                        if parent_id not in parent_first_child_age or age < parent_first_child_age[parent_id]:
                            parent_first_child_age[parent_id] = age

            if parent_first_child_age:
                youngest_parent_age = min(parent_first_child_age.values())
                tied_parents = [pid for pid, age in parent_first_child_age.items() if age == youngest_parent_age]
                f.write(f"Age at first biological child birth: {youngest_parent_age}\n")
                f.write(f"Number of persons tied at this age: {len(tied_parents)}\n")
                for pid in tied_parents:
                    yp = self.people[pid]
                    f.write(f"  Person ID: {pid} | Sex: {yp.sex} | Name: {yp.given_name} {yp.surname} | Birth year: {yp.birth_year}\n")
                f.write("\n")
            else:
                f.write("No biological parent-child records found.\n\n")

            # ── 9. INSERT/DELETE TEST CANDIDATE ──────────────────────────────
            # Find an adopted person who has no biological parents in the dataset.
            # This person is the recommended anchor for manual insert/delete benchmarks:
            # add two biological parents + one sibling (INSERT), then remove them (DELETE).
            f.write("--- SCENARIO: INSERT/DELETE TEST CANDIDATE ---\n")
            f.write("Recommended: an adopted person with no biological parents in the dataset.\n")
            f.write("Benchmark: INSERT two biological parents + one sibling for this person,\n")
            f.write("           then DELETE those three persons and their Family node.\n")

            candidate = None
            for p in self.people.values():
                if not p.parents_family_id:
                    continue
                fam = self.families.get(p.parents_family_id)
                if not fam:
                    continue
                my_entry = next((c for c in fam.children if c['id'] == p.id), None)
                if my_entry and my_entry['type'] == 'ADOPTED':
                    candidate = p
                    break

            if candidate:
                f.write(f"Person ID:    {candidate.id}\n")
                f.write(f"Name:         {candidate.given_name} {candidate.surname}\n")
                f.write(f"Birth year:   {candidate.birth_year}\n")
                f.write(f"Adopting Family ID: {candidate.parents_family_id}\n")
                f.write("Biological parents: none in dataset — safe to INSERT new parents.\n\n")
            else:
                f.write("No suitable adopted person without biological parents found in dataset.\n\n")

            # ── 10. PLACE NAME UPDATE SCOPE ───────────────────────────────────
            # Substring match so values like 'Cemetery in Breslau' are included.
            people_to_update = sum(
                1 for p in self.people.values()
                if any(g in (p.birth_place or '') or g in (p.death_place or '') or g in (p.burial_place or '')
                       for g in GERMAN_TO_POLISH)
            )
            families_to_update = sum(
                1 for fam in self.families.values()
                if any(g in (fam.marriage_place or '') for g in GERMAN_TO_POLISH)
            )

            f.write("--- SCENARIO: PLACE NAME UPDATE SCOPE ---\n")
            f.write("Historical German city names to be replaced with their modern Polish equivalents:\n")
            for german, polish in GERMAN_TO_POLISH.items():
                f.write(f"  {german} -> {polish}\n")
            f.write("Match is substring-based (e.g. 'Cemetery in Breslau' is also captured).\n")
            f.write(f"people:   {people_to_update} rows affected\n")
            f.write(f"families: {families_to_update} rows affected\n")

        print(f"[{self.target_population}] Summary report saved to '{filepath}'.")


    def run(self):
        """
        Execute the full simulation lifecycle for this engine instance.

        Initializes the founding population, then advances year by year,
        processing deaths, divorces, births, and marriages in that order.
        The loop terminates when the target population count is reached,
        the living population goes extinct, or a 2000-year safety cap is hit.
        On completion, CSV export (PostgreSQL and Neo4j) and analytics are
        triggered automatically.
        """
        print(f"\nSimulation started from year {self.start_year}. Target population: {self.target_population}.")

        # Scale the founding generation size to the target population to reduce early-stage
        # pedigree collapse, which is more severe in smaller simulations.
        if self.target_population <= 1000:
            init_pairs = 80
        elif self.target_population <= 10000:
            init_pairs = 200
        else:
            init_pairs = 1000

        self._initialize_population(initial_pairs=init_pairs)

        log_start = f"Year {self.start_year}: Alive {len(self.living_people_ids)} people. Total generated: {len(self.people)}"
        self.history_log.append(log_start)
        print(log_start)

        try:
            while len(self.people) < self.target_population:
                self.current_year += 1
                self._process_deaths()
                self._process_divorces()
                self._process_births()
                self._process_marriages()

                if len(self.living_people_ids) == 0:
                    print(f"FATAL ERROR: Population went EXTINCT in year {self.current_year}!")
                    break

                if (self.current_year - self.start_year) % 25 == 0:
                    log = f"Year {self.current_year}: Alive {len(self.living_people_ids)} people. Total generated: {len(self.people)}"
                    self.history_log.append(log)
                    print(log)

                if self.current_year > self.start_year + 2000:
                    print("WARNING: Safety limit reached (2000 years).")
                    break

            log_end = f"Year {self.current_year} (END): Alive {len(self.living_people_ids)} people. Total generated: {len(self.people)}"
            self.history_log.append(log_end)
            print(log_end)

            if len(self.people) >= self.target_population:
                print(f"Success! Target of {len(self.people)} reached in year {self.current_year}.")
            else:
                print("Simulation finished without reaching target population.")

        except TargetReachedException:
            log_end = f"Year {self.current_year} (END): Alive {len(self.living_people_ids)} people. Total generated: {len(self.people)}"
            self.history_log.append(log_end)
            print(log_end)
            print(f"Success! Target of {len(self.people)} people reached exactly in year {self.current_year}.")

        self.export_to_postgres_csv()
        self.export_to_neo4j_csv()
        self.run_analytics()