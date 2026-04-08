import csv
import random
import os
import sys
import re
from collections import Counter, defaultdict
from typing import Dict, Set, List, Optional
from models import Person, Family
from config import MALE_NAMES, FEMALE_NAMES, SURNAMES, PLACES, CAUSES_OF_DEATH, OCCUPATIONS, SEED, SCENARIOS
from demographics import (get_planned_children_count, get_marriage_age,
                          get_lifespan, is_too_closely_related, random_date,
                          adjust_surname, get_family_status, get_child_relationship_type)

GERMAN_TO_POLISH = {
    'Posen':    'Poznań',
    'Danzig':   'Gdańsk',
    'Breslau':  'Wrocław',
    'Stettin':  'Szczecin',
    'Bromberg': 'Bydgoszcz',
    'Thorn':    'Toruń',
}

class TargetReachedException(Exception):
    pass

class SimulationEngine:
    def __init__(self, target_population: int, output_dir: str):
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
        
        self.max_living_history = 0 
        self.planned_births: Dict[int, List[dict]] = {}
        self.history_log = []

        os.makedirs(self.output_dir, exist_ok=True)

    def create_person(self, sex: str, raw_surname: str, birth_year: int, parents_fam_id: Optional[int] = None,
                      region_id: int = 0) -> Person:
        if len(self.people) >= self.target_population:
            raise TargetReachedException()

        p_id = self.next_person_id
        self.next_person_id += 1
        name = random.choice(MALE_NAMES) if sex == 'M' else random.choice(FEMALE_NAMES)
        surname = adjust_surname(raw_surname, sex)
        lifespan = get_lifespan()
        target_marriage_age = get_marriage_age(sex)

        age_now = self.current_year - birth_year
        if lifespan <= age_now:
            lifespan = age_now + random.randint(5, 35)

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
        for i in range(initial_pairs):
            reg = i % 5
            age_husband = random.randint(20, 50)
            age_wife = random.randint(18, 45)
            
            husband = self.create_person('M', random.choice(SURNAMES), self.start_year - age_husband, region_id=reg)
            wife = self.create_person('F', random.choice(SURNAMES), self.start_year - age_wife, region_id=reg)
            self._create_marriage(husband, wife, self.start_year)

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

        if not husband.occupation: husband.occupation = random.choice(OCCUPATIONS)
        if not wife.occupation: wife.occupation = random.choice(OCCUPATIONS)

        config = SCENARIOS.get(self.target_population, SCENARIOS[1000])
        avg_children = config['avg_children']

        if husband.marriages_count > 1 or wife.marriages_count > 1:
            planned_count = get_planned_children_count(avg_children * 0.6)
        else:
            planned_count = get_planned_children_count(avg_children)

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
        HARD_LIFESPAN_CAP = 105
        critical_candidates = []
        normal_candidates = []
        
        for p_id in self.living_people_ids:
            p = self.people[p_id]
            age = self.current_year - p.birth_year
            if age > HARD_LIFESPAN_CAP:
                critical_candidates.append(p)
            elif age >= p.lifespan:
                normal_candidates.append(p)
        
        critical_candidates.sort(key=lambda p: (self.current_year - p.birth_year), reverse=True)
        normal_candidates.sort(key=lambda p: (self.current_year - p.birth_year), reverse=True)
        
        dead_this_year = set()

        for p in critical_candidates:
            self._process_single_death(p)
            dead_this_year.add(p.id)

        current_living = len(self.living_people_ids) - len(dead_this_year)
        allowed_deaths = max(0, current_living - self.max_living_history)

        for p in normal_candidates:
            if p.id in dead_this_year: continue
            
            if allowed_deaths > 0:
                allowed_deaths -= 1
                self._process_single_death(p)
                dead_this_year.add(p.id)
            else:
                p.lifespan += 1 
        
        self.living_people_ids.difference_update(dead_this_year)
            
        if len(self.living_people_ids) > self.max_living_history:
            self.max_living_history = len(self.living_people_ids)

    def _process_single_death(self, p: Person):
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
                for f_id in list(self.active_families):
                    fam = self.families[f_id]
                    if (fam.husband_id == p.id and fam.wife_id == spouse.id) or \
                            (fam.wife_id == p.id and fam.husband_id == spouse.id):
                        fam.status = 'WIDOWED'
                        self.active_families.remove(f_id)

    def _process_divorces(self):
        divorced_this_year = []
        for f_id in self.active_families:
            if random.random() < 0.0005: 
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
        singles_m = {r: [] for r in range(5)}
        singles_f = {r: [] for r in range(5)}

        for p_id in self.living_people_ids:
            p = self.people[p_id]
            if p.spouse_id is None and not p.is_celibate:
                age = self.current_year - p.birth_year
                if p.sex == 'M' and p.target_marriage_age <= age < 65:
                    singles_m[p.region_id].append(p)
                elif p.sex == 'F' and p.target_marriage_age <= age < 50:
                    singles_f[p.region_id].append(p)

        for r in range(5):
            random.shuffle(singles_m[r])
            random.shuffle(singles_f[r])

        males_to_marry = [p for region_list in singles_m.values() for p in region_list]
        random.shuffle(males_to_marry)

        for male in males_to_marry:
            if male.spouse_id is not None:
                continue

            all_available_females = [p for region_list in singles_f.values() for p in region_list if p.spouse_id is None]
            random.shuffle(all_available_females)
            
            for female in all_available_females:
                if not is_too_closely_related(male.id, female.id, self.people, self.families):
                    self._create_marriage(male, female, self.current_year)
                    break 

    def run(self):
        print(f"\nSimulation started from year {self.start_year}. Target population: {self.target_population}.")

        config = SCENARIOS.get(self.target_population, SCENARIOS[1000])
        init_pairs = config['initial_pairs']

        self._initialize_population(initial_pairs=init_pairs)
        self.max_living_history = len(self.living_people_ids)

        log_start = f"Year {self.start_year}: Alive {len(self.living_people_ids)} people. Total generated: {len(self.people)}"
        self.history_log.append(log_start)
        print(log_start)

        try:
            while len(self.people) < self.target_population:
                self.current_year += 1
                
                self._process_births()
                self._process_marriages()
                self._process_divorces()
                self._process_deaths()
                
                if len(self.living_people_ids) > self.max_living_history:
                    self.max_living_history = len(self.living_people_ids)

                if (self.current_year - self.start_year) % 25 == 0:
                    log = f"Year {self.current_year}: Alive {len(self.living_people_ids)} people. Total generated: {len(self.people)}"
                    self.history_log.append(log)
                    print(log)

                if self.current_year > self.start_year + 3000:
                    print("WARNING: Safety limit reached (3000 years).")
                    break

            log_end = f"Year {self.current_year} (END): Alive {len(self.living_people_ids)} people. Total generated: {len(self.people)}"
            self.history_log.append(log_end)
            print(log_end)
            print(f"Success! Target of {len(self.people)} reached in year {self.current_year}.")

        except TargetReachedException:
            log_end = f"Year {self.current_year} (END): Alive {len(self.living_people_ids)} people. Total generated: {len(self.people)}"
            self.history_log.append(log_end)
            print(log_end)
            print(f"Success! Target of {len(self.people)} people reached exactly in year {self.current_year}.")

        self.export_to_postgres_csv()
        self.export_to_neo4j_csv()
        self.run_analytics()
    
    def export_to_postgres_csv(self):
        pg_dir = os.path.join(self.output_dir, 'postgres')
        os.makedirs(pg_dir, exist_ok=True)

        with open(os.path.join(pg_dir, 'people.csv'), 'w', newline='', encoding='utf-8') as f:
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

        with open(os.path.join(pg_dir, 'families.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'status', 'marriage_date', 'marriage_place', 'husband_id', 'wife_id'])
            for fam in self.families.values():
                writer.writerow([
                    fam.id, fam.status, fam.marriage_date.isoformat() if fam.marriage_date else '',
                    fam.marriage_place, fam.husband_id, fam.wife_id
                ])

        with open(os.path.join(pg_dir, 'family_children.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['family_id', 'child_id', 'relationship_type'])
            for fam in self.families.values():
                for child_dict in fam.children:
                    writer.writerow([fam.id, child_dict['id'], child_dict['type']])

        print(f"[{self.target_population}] PostgreSQL CSV export complete → {pg_dir}/")

    def export_to_neo4j_csv(self):
        neo4j_dir = os.path.join(self.output_dir, 'neo4j')
        os.makedirs(neo4j_dir, exist_ok=True)

        with open(os.path.join(neo4j_dir, 'nodes_person.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id:ID(Person)', 'givenName:STRING', 'surname:STRING', 'sex:STRING',
                'isDeceased:BOOLEAN', 'birthPlace:STRING', 'birthDate:DATE', 'deathPlace:STRING',
                'deathDate:DATE', 'causeOfDeath:STRING', 'burialPlace:STRING', 'occupation:STRING', ':LABEL'
            ])
            for p in self.people.values():
                writer.writerow([
                    p.id, p.given_name, p.surname, p.sex, 'true' if p.is_deceased else 'false',
                    p.birth_place, p.birth_date.isoformat() if p.birth_date else '',
                    p.death_place if p.is_deceased else '', p.death_date.isoformat() if p.death_date else '',
                    p.cause_of_death if p.is_deceased else '', p.burial_place if p.is_deceased else '',
                    p.occupation if p.occupation else '', 'Person'
                ])

        with open(os.path.join(neo4j_dir, 'nodes_family.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id:ID(Family)', 'status:STRING', 'marriageDate:DATE', 'marriagePlace:STRING', ':LABEL'])
            for fam in self.families.values():
                writer.writerow([
                    fam.id, fam.status, fam.marriage_date.isoformat() if fam.marriage_date else '',
                    fam.marriage_place, 'Family'
                ])

        with open(os.path.join(neo4j_dir, 'rels_husband_of.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([':START_ID(Person)', ':END_ID(Family)', ':TYPE'])
            for fam in self.families.values():
                if fam.husband_id:
                    writer.writerow([fam.husband_id, fam.id, 'HUSBAND_OF'])

        with open(os.path.join(neo4j_dir, 'rels_wife_of.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([':START_ID(Person)', ':END_ID(Family)', ':TYPE'])
            for fam in self.families.values():
                if fam.wife_id:
                    writer.writerow([fam.wife_id, fam.id, 'WIFE_OF'])

        with open(os.path.join(neo4j_dir, 'rels_child_of.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([':START_ID(Family)', ':END_ID(Person)', 'relationshipType:STRING', ':TYPE'])
            for fam in self.families.values():
                for child_dict in fam.children:
                    writer.writerow([fam.id, child_dict['id'], child_dict['type'], 'HAS_CHILD'])

        print(f"[{self.target_population}] Neo4j CSV export complete → {neo4j_dir}/")


    # =========================================================================
    # QUERY UPDATE UTILITIES
    # =========================================================================
    def _update_scenario_files(
        self,
        lca_p1_id: int,
        lca_p2_id: int,
        ancestor_id: Optional[int],
        descendant_id: Optional[int],
        surname: Optional[str],
        year_start: Optional[int],
        year_end: Optional[int],
        candidate           # Person | None
    ):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(self.output_dir)))

        if self.target_population == 1000:
            size = "1k"
            new_f_id, new_m_id, new_sib_id, new_fam_id = 2001, 2002, 2003, 2001
        elif self.target_population == 10000:
            size = "10k"
            new_f_id, new_m_id, new_sib_id, new_fam_id = 20001, 20002, 20003, 20001
        else:
            size = "100k"
            new_f_id, new_m_id, new_sib_id, new_fam_id = 200001, 200002, 200003, 200001

        pg_base  = os.path.join(project_root, "query_performance_benchmark", "scenarios", "postgres_scenarios")
        n4j_base = os.path.join(project_root, "query_performance_benchmark", "scenarios", "neo4j_scenarios")

        def rw(path, transform):
            if not os.path.exists(path):
                print(f"  [WARN] Query file not found, skipping: {path}")
                return
            with open(path, 'r', encoding='utf-8') as fh:
                old = fh.read()
            new = transform(old)
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(new)

        def inject_rec(txt: str, text: str, is_cypher: bool) -> str:
            prefix = "//" if is_cypher else "--"
            marker = f"{prefix} RECOMMENDED PARAMETERS:"
            
            # Remove existing injected parameter block if any
            txt = re.sub(r'\n*' + re.escape(marker) + r'[^\n]*\n+', '\n\n', txt)
            
            # Inject new parameter block right before the first major keyword
            def repl(m):
                return f"\n\n{marker} {text}\n\n{m.group(1)}"
            txt = re.sub(r'\n(WITH\s|SELECT\s|MATCH\s|UPDATE\s|DELETE\s|INSERT\s|CREATE\s)', repl, txt, count=1)
            return txt

        # ── SCENARIO 01: LCA
        def upd_lca_sql(txt):
            txt = re.sub(r'(anc_a\s*\([^)]+\)\s*AS\s*\(\s*\n\s*SELECT\s+)\d+(\s*,\s*0\s*,\s*ARRAY\s*\[)\d+(\])', rf'\g<1>{lca_p1_id}\g<2>{lca_p1_id}\g<3>', txt)
            txt = re.sub(r'(anc_b\s*\([^)]+\)\s*AS\s*\(\s*\n\s*SELECT\s+)\d+(\s*,\s*0\s*,\s*ARRAY\s*\[)\d+(\])', rf'\g<1>{lca_p2_id}\g<2>{lca_p2_id}\g<3>', txt)
            return inject_rec(txt, f"Person A = {lca_p1_id}, Person B = {lca_p2_id}", False)

        def upd_lca_cypher(txt):
            txt = re.sub(r'(WHERE\s+startNode\.id\s+IN\s+\[)\d+\s*,\s*\d+(\])', rf'\g<1>{lca_p1_id}, {lca_p2_id}\g<2>', txt)
            txt = re.sub(r'(sId\s*=\s*)\d+(.*?AS\s+distA)', rf'\g<1>{lca_p1_id}\g<2>', txt)
            txt = re.sub(r'(sId\s*=\s*)\d+(.*?AS\s+distB)', rf'\g<1>{lca_p2_id}\g<2>', txt)
            return inject_rec(txt, f"Person A = {lca_p1_id}, Person B = {lca_p2_id}", True)

        rw(os.path.join(pg_base,  "scenario_01_lca", f"scenario_01_lca_{size}.sql"),    upd_lca_sql)
        rw(os.path.join(n4j_base, "scenario_01_lca", f"scenario_01_lca_{size}.cypher"), upd_lca_cypher)

        # ── SCENARIO 02: SURNAME FILTER
        if surname and year_start is not None and year_end is not None:
            def upd_s02_sql(txt):
                txt = re.sub(r"(WHERE\s+p\.surname\s*=\s*')[^']+(')", rf"\g<1>{surname}\g<2>", txt)
                txt = re.sub(r'(BETWEEN\s+)\d+(\s+AND\s+)\d+', rf'\g<1>{year_start}\g<2>{year_end}', txt)
                return inject_rec(txt, f"Surname = '{surname}', Birth Year Range = {year_start}-{year_end}", False)

            def upd_s02_cypher(txt):
                txt = re.sub(r'(WHERE\s+n\.birthDate\.year\s*>=\s*)\d+(\s+and\s+n\.birthDate\.year\s*<=\s*)\d+', rf'\g<1>{year_start}\g<2>{year_end}', txt, flags=re.IGNORECASE)
                txt = re.sub(r"(AND\s+n\.surname\s*=\s*')[^']+(')", rf"\g<1>{surname}\g<2>", txt)
                return inject_rec(txt, f"Surname = '{surname}', Birth Year Range = {year_start}-{year_end}", True)

            rw(os.path.join(pg_base,  "scenario_02_surname_filter", f"scenario_02_surname_filter_{size}.sql"),    upd_s02_sql)
            rw(os.path.join(n4j_base, "scenario_02_surname_filter", f"scenario_02_surname_filter_{size}.cypher"), upd_s02_cypher)

        # ── SCENARIO 04: ANCESTORS
        if ancestor_id is not None:
            def upd_s04_sql(txt):
                txt = re.sub(r'(SELECT\s+)\d+(\s+AS\s+person_id\s*,\s*0\s+AS\s+depth)', rf'\g<1>{ancestor_id}\g<2>', txt)
                txt = re.sub(r'(WHERE\s+person_id\s*<>\s*)\d+', rf'\g<1>{ancestor_id}', txt)
                return inject_rec(txt, f"Person ID = {ancestor_id}", False)

            def upd_s04_cypher(txt):
                txt = re.sub(r'(MATCH\s+\(start:Person\s+\{id:\s*)\d+(\})', rf'\g<1>{ancestor_id}\g<2>', txt)
                return inject_rec(txt, f"Person ID = {ancestor_id}", True)

            rw(os.path.join(pg_base,  "scenario_04_ancestors", f"scenario_04_ancestors_{size}.sql"),    upd_s04_sql)
            rw(os.path.join(n4j_base, "scenario_04_ancestors", f"scenario_04_ancestors_{size}.cypher"), upd_s04_cypher)

        # ── SCENARIO 05: DESCENDANTS
        if descendant_id is not None:
            def upd_s05_sql(txt):
                txt = re.sub(r'(SELECT\s+)\d+(\s*,\s*0\s*,\s*NULL::int\s*,\s*ARRAY\s*\[)\d+(\])', rf'\g<1>{descendant_id}\g<2>{descendant_id}\g<3>', txt)
                txt = re.sub(r'(WHERE\s+person_id\s*<>\s*)\d+', rf'\g<1>{descendant_id}', txt)
                return inject_rec(txt, f"Person ID = {descendant_id}", False)

            def upd_s05_cypher(txt):
                txt = re.sub(r'(MATCH\s+\(start:Person\s+\{id:\s*)\d+(\})', rf'\g<1>{descendant_id}\g<2>', txt)
                return inject_rec(txt, f"Person ID = {descendant_id}", True)

            rw(os.path.join(pg_base,  "scenario_05_descendants", f"scenario_05_descendants_{size}.sql"),    upd_s05_sql)
            rw(os.path.join(n4j_base, "scenario_05_descendants", f"scenario_05_descendants_{size}.cypher"), upd_s05_cypher)


    def run_analytics(self):
        config = SCENARIOS.get(self.target_population, {'min_lca_path': 8, 'max_lca_path': 99, 'ancestors_depth': 5})
        target_lca_min = config['min_lca_path']
        target_lca_max = config.get('max_lca_path', 999)
        target_ancestors_depth = config['ancestors_depth']

        target_descendants_depth = config.get('descendants_depth', 3 if self.target_population <= 1000
            else (6 if self.target_population <= 10000 else 10))

        target_label = str(target_lca_min) if target_lca_min == target_lca_max else f"{target_lca_min}-{target_lca_max}"

        def is_biological_child(p_id):
            p = self.people.get(p_id)
            if not p or not p.parents_family_id: return False
            fam = self.families.get(p.parents_family_id)
            if not fam: return False
            return any(c['id'] == p_id and c['type'] == 'BIOLOGICAL' for c in fam.children)

        def get_bio_parents(child_id):
            p = self.people.get(child_id)
            if p and p.parents_family_id:
                fam = self.families.get(p.parents_family_id)
                if fam:
                    for c in fam.children:
                        if c['id'] == child_id and c['type'] == 'BIOLOGICAL':
                            return (fam.husband_id or 'NULL', fam.wife_id or 'NULL')
            return ('NULL', 'NULL')

        depths = {}
        max_depth = 0
        total_depth_leafs = 0
        leaf_count = 0
        
        bio_children_map = defaultdict(list)
        for fam in self.families.values():
            for child_dict in fam.children:
                if child_dict['type'] == 'BIOLOGICAL':
                    if fam.husband_id: bio_children_map[fam.husband_id].append(child_dict['id'])
                    if fam.wife_id: bio_children_map[fam.wife_id].append(child_dict['id'])

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
            
            if len(bio_children_map[p_id]) == 0:
                leaf_count += 1
                total_depth_leafs += d

        total_people = len(self.people)
        males = sum(1 for p in self.people.values() if p.sex == 'M')
        females = total_people - males
        
        married_people = sum(1 for p in self.people.values() if p.marriages_count > 0)
        marriage_rate = (married_people / total_people) * 100
        
        dead_people = [p for p in self.people.values() if p.is_deceased]
        avg_lifespan = sum(p.lifespan for p in dead_people) / max(1, len(dead_people))
        
        families_with_children = [fam for fam in self.families.values() if fam.children]
        max_children = max((len(f.children) for f in families_with_children), default=0)
        avg_children_per_family = sum(len(f.children) for f in families_with_children) / max(1, len(families_with_children))
        divorces_count = sum(1 for fam in self.families.values() if fam.status == 'DIVORCED')
        
        children_count_distribution = Counter(len(f.children) for f in families_with_children)
        
        biological_children = set()
        for fam in self.families.values():
            for c in fam.children:
                if c['type'] == 'BIOLOGICAL':
                    biological_children.add(c['id'])
                    
        config_setup = SCENARIOS.get(self.target_population, SCENARIOS[1000])            
        founders = config_setup['initial_pairs'] * 2
        orphans = total_people - len(biological_children) - founders

        # ---- 1. SUMMARY.TXT (Population Growth & Enhanced Topology) ----
        summary_filepath = os.path.join(self.output_dir, 'summary.txt')
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            f.write("=== POPULATION AND GRAPH TOPOLOGY REPORT ===\n")
            f.write(f"Target population: {self.target_population}\n")
            f.write(f"Total people generated: {len(self.people)}\n")
            f.write(f"People alive at end of simulation ({self.current_year}): {len(self.living_people_ids)}\n")
            f.write(f"Total families: {len(self.families)}\n\n")

            f.write("--- POPULATION GROWTH OVER TIME ---\n")
            for log in self.history_log:
                f.write(log + "\n")
            f.write("\n")

            f.write("--- GRAPH TOPOLOGY & DEMOGRAPHICS ---\n")
            f.write(f"Max graph depth (oldest root to youngest descendant): {max_depth} generations\n")
            f.write(f"Average depth of leaf nodes (endpoints): {total_depth_leafs / max(1, leaf_count):.2f} generations\n")
            f.write(f"Sex ratio: {males} Males / {females} Females\n")
            f.write(f"Average lifespan (deceased individuals): {avg_lifespan:.1f} years\n")
            f.write(f"Marriage rate: {marriage_rate:.1f}% of total population\n")
            f.write(f"Total divorces: {divorces_count}\n")
            f.write(f"Families with children: {len(families_with_children)}\n")
            f.write(f"Average children per fertile family: {avg_children_per_family:.2f}\n")
            f.write(f"Largest family generated: {max_children} children\n")
            f.write("Family distribution (children per family):\n")
            for i in range(1, max_children + 1):
                f.write(f"  {i} child(ren): {children_count_distribution.get(i, 0)} families\n")
            f.write(f"Orphans (adopted/foster without biological links): {orphans} individuals\n\n")


        # ---- Scenario Directory Setup ----
        scenarios_dir = os.path.join(self.output_dir, 'expected_results')
        os.makedirs(scenarios_dir, exist_ok=True)

        def write_scenario_file(filename, info_text, headers=None, rows=None):
            filepath = os.path.join(scenarios_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(info_text + "\n")
                if headers and rows is not None:
                    f.write(f"\nExpected rows: {len(rows)}\n\n")
                    col_widths = [len(str(h)) for h in headers]
                    for row in rows:
                        for i, val in enumerate(row):
                            col_widths[i] = max(col_widths[i], len(str(val)))
                    
                    header_str = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
                    f.write(header_str + "\n")
                    f.write("-" * len(header_str) + "\n")
                    for row in rows:
                        f.write(" | ".join(str(val).ljust(w) for val, w in zip(row, col_widths)) + "\n")

        # Base pool for heavy BFS searches
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

        # ---------------- SCENARIO 01: LCA ----------------
        regions = {0: [], 1: [], 2: [], 3: [], 4: []}
        for p_id in youngest_ids:
            regions[self.people[p_id].region_id].append(p_id)

        bfs_limit = (target_lca_max // 2) + 10

        def get_ancestors_biological(p_id, limit):
            ancestors_paths = {p_id: 0}
            queue = [(p_id, 0)]
            while queue:
                curr_id, dist = queue.pop(0)
                if dist >= limit: continue
                if not is_biological_child(curr_id): continue
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
            if len(available_regions) < 2: break

            r1, r2 = random.sample(available_regions, 2)
            p1_id  = random.choice(regions[r1])
            p2_id  = random.choice(regions[r2])

            if not is_too_closely_related(p1_id, p2_id, self.people, self.families):
                anc1 = get_ancestors_biological(p1_id, bfs_limit)
                anc2 = get_ancestors_biological(p2_id, bfs_limit)

                common = set(anc1.keys()).intersection(set(anc2.keys()))
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
                            'total_dist': max_distance
                        }

                        if target_lca_min <= max_distance <= target_lca_max:
                            sys.stdout.write(f"\r[{self.target_population}] LCA search: found target {max_distance} at iteration {i + 1}!{' '*20}\n")
                            sys.stdout.flush()
                            break
        else:
            if best_pair_info:
                sys.stdout.write(f"\r[{self.target_population}] LCA search: {iterations}/{iterations} | best found: {max_distance} (target: {target_label}) — using best available  \n")
            else:
                sys.stdout.write(f"\r[{self.target_population}] LCA search: {iterations}/{iterations} | NO PAIR FOUND (target: {target_label})                              \n")
            sys.stdout.flush()

        info_01 = "--- SCENARIO 01: LOWEST COMMON ANCESTOR (LCA) ---\n"
        info_01 += "Biological relationships only.\n"
        info_01 += f"Target LCA path length required: {target_label}\n"
        info_01 += "Constraint: Person A and Person B are not closely related AND\n"
        info_01 += "            biological distance to LCA > 3 for both sides.\n"

        if best_pair_info and (target_lca_min <= best_pair_info['total_dist'] <= target_lca_max):
            info_01 += f"\nRecommended Person A (ID: {best_pair_info['p1']})\n"
            info_01 += f"Recommended Person B (ID: {best_pair_info['p2']})\n"
            
            headers_01 = ['lca_id', 'given_name', 'surname', 'sex', 'birth_date', 'birth_place', 'death_date', 'death_place', 'path_length_from_a', 'path_length_from_b', 'total_dist']
            rows_01 = []
            for lca_id, d_a, d_b in sorted(best_pair_info['lcas'], key=lambda x: x[0]):
                p = self.people[lca_id]
                rows_01.append((lca_id, p.given_name, p.surname, p.sex, p.birth_date.isoformat(), p.birth_place, p.death_date.isoformat() if p.death_date else 'NULL', p.death_place or 'NULL', d_a, d_b, d_a + d_b))
            
            write_scenario_file('scenario_01_lca.txt', info_01, headers_01, rows_01)
        else:
            print(f"[WARNING] LCA target {target_label} NOT MET for {self.target_population} dataset. Please change SEED in config.py!")
            write_scenario_file('scenario_01_lca.txt', info_01 + "\nNo suitable LCA pairs found. Please alter SEED.")


        # ---------------- SCENARIO 04: ANCESTORS ----------------
        best_ancestor_count = 0
        best_ancestor_person_id = None
        sample_for_ancestors = youngest_ids[:200]

        for p_id in sample_for_ancestors:
            distinct_ancestors = set()
            visited = {p_id}
            queue   = [(p_id, 0)]
            while queue:
                curr, d = queue.pop(0)
                if d >= target_ancestors_depth: continue
                if not is_biological_child(curr): continue
                fam = self.families[self.people[curr].parents_family_id]
                for parent_id in (fam.husband_id, fam.wife_id):
                    if parent_id and parent_id not in visited:
                        visited.add(parent_id)
                        distinct_ancestors.add(parent_id)
                        queue.append((parent_id, d + 1))
            count = len(distinct_ancestors)
            if count > best_ancestor_count:
                best_ancestor_count = count
                best_ancestor_person_id = p_id

        theoretical_max = sum(2 ** i for i in range(1, target_ancestors_depth + 1))
        
        info_04 = "--- SCENARIO 04: ANCESTOR RETRIEVAL ---\n"
        info_04 += "Biological relationships only.\n"
        info_04 += f"Objective: Find person with most distinct biological ancestors up to {target_ancestors_depth} generations back.\n"
        info_04 += f"Theoretical max (Perfect Tree): {theoretical_max}\n"
        info_04 += f"Distinct biological ancestors found: {best_ancestor_count}\n"
        if target_ancestors_depth > 10:
            info_04 += "(Note: High pedigree collapse is biologically expected here.)\n"
        
        if best_ancestor_person_id:
            info_04 += f"\nRecommended Person ID: {best_ancestor_person_id}\n"
            generation_map = {}
            queue = [(best_ancestor_person_id, 0)]
            while queue:
                curr, gen = queue.pop(0)
                if curr not in generation_map:
                    generation_map[curr] = gen
                    if gen < target_ancestors_depth and is_biological_child(curr):
                        fam = self.families[self.people[curr].parents_family_id]
                        if fam.husband_id: queue.append((fam.husband_id, gen + 1))
                        if fam.wife_id: queue.append((fam.wife_id, gen + 1))
            
            if best_ancestor_person_id in generation_map:
                del generation_map[best_ancestor_person_id]
            
            headers_04 = ['ancestor_id', 'generation', 'given_name', 'surname', 'sex', 'birth_date', 'birth_place', 'death_date', 'death_place', 'burial_place', 'cause_of_death', 'father_id', 'mother_id']
            rows_04 = []
            for a_id, gen in generation_map.items():
                p = self.people[a_id]
                f_id, m_id = get_bio_parents(a_id)
                rows_04.append((a_id, gen, p.given_name, p.surname, p.sex, p.birth_date.isoformat(), p.birth_place, p.death_date.isoformat() if p.death_date else 'NULL', p.death_place or 'NULL', p.burial_place or 'NULL', p.cause_of_death or 'NULL', f_id, m_id))
            
            rows_04.sort(key=lambda x: (x[1], x[0]))
            write_scenario_file('scenario_04_ancestors.txt', info_04, headers_04, rows_04)
        else:
            print(f"[WARNING] Scenario 04 (Ancestors) failed for {self.target_population}. Change SEED.")
            write_scenario_file('scenario_04_ancestors.txt', info_04 + "\nNo suitable ancestors found.")

        # ---------------- SCENARIO 05: DESCENDANTS ----------------
        best_descendant_count = 0
        best_descendant_person_id = None
        all_ids = list(self.people.keys())
        sample_for_descendants = random.sample(all_ids, min(500, len(all_ids)))

        for p_id in sample_for_descendants:
            distinct_descendants = set()
            visited = {p_id}
            queue = [(p_id, 0)]
            while queue:
                curr, d = queue.pop(0)
                if d >= target_descendants_depth: continue
                for child_id in bio_children_map.get(curr, []):
                    if child_id not in visited:
                        visited.add(child_id)
                        distinct_descendants.add(child_id)
                        queue.append((child_id, d + 1))
            count = len(distinct_descendants)
            if count > best_descendant_count:
                best_descendant_count = count
                best_descendant_person_id = p_id

        info_05 = "--- SCENARIO 05: DESCENDANT RETRIEVAL ---\n"
        info_05 += "Biological relationships only.\n"
        info_05 += f"Objective: Find person with most distinct biological descendants up to {target_descendants_depth} generations forward.\n"
        info_05 += f"Distinct biological descendants found: {best_descendant_count}\n"
        
        if best_descendant_person_id:
            info_05 += f"\nRecommended Person ID: {best_descendant_person_id}\n"
            generation_map = {}
            queue = [(best_descendant_person_id, 0)]
            while queue:
                curr, gen = queue.pop(0)
                if curr not in generation_map:
                    generation_map[curr] = gen
                    if gen < target_descendants_depth:
                        for child_id in bio_children_map.get(curr, []):
                            queue.append((child_id, gen + 1))
            
            if best_descendant_person_id in generation_map:
                del generation_map[best_descendant_person_id]
                
            headers_05 = ['descendant_id', 'generation', 'given_name', 'surname', 'sex', 'birth_date', 'birth_place', 'death_date', 'death_place', 'burial_place', 'cause_of_death', 'father_id', 'mother_id']
            rows_05 = []
            for d_id, gen in generation_map.items():
                p = self.people[d_id]
                f_id, m_id = get_bio_parents(d_id)
                rows_05.append((d_id, gen, p.given_name, p.surname, p.sex, p.birth_date.isoformat(), p.birth_place, p.death_date.isoformat() if p.death_date else 'NULL', p.death_place or 'NULL', p.burial_place or 'NULL', p.cause_of_death or 'NULL', f_id, m_id))
            
            rows_05.sort(key=lambda x: (x[1], x[0]))
            write_scenario_file('scenario_05_descendants.txt', info_05, headers_05, rows_05)
        else:
            print(f"[WARNING] Scenario 05 (Descendants) failed for {self.target_population}. Change SEED.")
            write_scenario_file('scenario_05_descendants.txt', info_05 + "\nNo suitable descendants found.")

        # ---------------- SCENARIO 02: SURNAME FILTER ----------------
        surname_counts = Counter(p.surname for p in self.people.values())
        top_surnames   = [s for s, _ in surname_counts.most_common(5)]
        best_surname   = None
        best_year_start = None
        best_count      = 0
        target_min = max(5, len(self.people) // 20)
        target_max = max(20, len(self.people) // 8)

        for surname in top_surnames:
            birth_years = sorted(p.birth_year for p in self.people.values() if p.surname == surname)
            if len(birth_years) < 2: continue
            for start in range(birth_years[0], birth_years[-1] - 49):
                cnt = sum(1 for y in birth_years if start <= y < start + 50)
                if target_min <= cnt <= target_max:
                    if best_surname is None or abs(cnt - target_min) < abs(best_count - target_min):
                        best_surname = surname
                        best_year_start = start
                        best_count = cnt

        if not best_surname:
            best_surname = top_surnames[0] if top_surnames else 'Nowak'
            all_years = sorted(p.birth_year for p in self.people.values() if p.surname == best_surname)
            best_year_start = all_years[len(all_years) // 4] if all_years else self.start_year

        info_02 = f"--- SCENARIO 02: SURNAME FILTER ---\nRecommended surname: {best_surname}\nRecommended birth year range: {best_year_start}-{best_year_start + 49}\n"
        headers_02 = ['person_id', 'given_name', 'surname', 'sex', 'birth_date', 'birth_place', 'death_date', 'death_place']
        rows_02 = []
        for p in self.people.values():
            if p.surname == best_surname and best_year_start <= p.birth_year < best_year_start + 50:
                rows_02.append((p.id, p.given_name, p.surname, p.sex, p.birth_date.isoformat(), p.birth_place, p.death_date.isoformat() if p.death_date else 'NULL', p.death_place or 'NULL'))
        rows_02.sort(key=lambda x: x[4]) # order by birth_date
        write_scenario_file('scenario_02_surname_filter.txt', info_02, headers_02, rows_02)


        # ---------------- SCENARIO 03: BIRTHS BY CITY ----------------
        births_by_city_quarter = defaultdict(lambda: defaultdict(int))
        for p in self.people.values():
            quarter = (p.birth_year // 25) * 25
            births_by_city_quarter[p.birth_place][quarter] += 1

        info_03 = "--- SCENARIO 03: BIRTHS PER CITY PER QUARTER-CENTURY ---\nRetrieves aggregates for all cities.\n"
        headers_03 = ['city', 'quarter_century_start', 'birth_count']
        rows_03 = []
        for city, q_dict in births_by_city_quarter.items():
            for q, count in q_dict.items():
                rows_03.append((city, q, count))
        rows_03.sort(key=lambda x: (x[0], x[1]))
        write_scenario_file('scenario_03_births_by_city.txt', info_03, headers_03, rows_03)

        # ---------------- SCENARIO 06: YOUNGEST PARENT ----------------
        min_days = float('inf')
        youngest_pairs = []
        for fam in self.families.values():
            for child_dict in fam.children:
                if child_dict['type'] == 'BIOLOGICAL':
                    c = self.people.get(child_dict['id'])
                    if not c or not c.birth_date: continue
                    for parent_id in (fam.husband_id, fam.wife_id):
                        p = self.people.get(parent_id)
                        if p and p.birth_date:
                            diff = (c.birth_date - p.birth_date).days
                            if diff >= 0:
                                if diff < min_days:
                                    min_days = diff
                                    youngest_pairs = [(p, c, diff)]
                                elif diff == min_days:
                                    youngest_pairs.append((p, c, diff))

        info_06 = "--- SCENARIO 06: YOUNGEST PARENT ---\n"
        info_06 += "Biological relationships only.\n"
        info_06 += "The youngest parent is determined by the exact age difference in days between the parent's birth and the child's birth.\n"
        headers_06 = ['parent_id', 'given_name', 'surname', 'sex', 'birth_date', 'birth_place', 'age_at_first_child', 'age_difference_in_days', 'child_id', 'child_birth_date', 'child_birth_place']
        rows_06 = []
        for p, c, diff in youngest_pairs:
            age_years = diff // 365
            rows_06.append((p.id, p.given_name, p.surname, p.sex, p.birth_date.isoformat(), p.birth_place, age_years, diff, c.id, c.birth_date.isoformat(), c.birth_place))
        rows_06.sort(key=lambda x: (x[0], x[8]))
        write_scenario_file('scenario_06_youngest_parent.txt', info_06, headers_06, rows_06)

        # ---------------- SCENARIO 07: PLACE NAME UPDATE ----------------
        info_07 = (
            "--- SCENARIO 07: PLACE NAME UPDATE ---\n"
            "Updates occurrences of historical German city names to their modern Polish equivalents.\n"
            "The update strictly replaces full field values, not substrings.\n"
            "Targeted fields:\n"
            "  - people.birth_place\n"
            "  - people.death_place\n"
            "  - families.marriage_place\n\n"
            "Replacements to be executed:\n"
            "  Posen -> Poznań\n"
            "  Danzig -> Gdańsk\n"
            "  Breslau -> Wrocław\n"
            "  Stettin -> Szczecin\n"
            "  Bromberg -> Bydgoszcz\n"
            "  Thorn -> Toruń\n"
        )
        write_scenario_file('scenario_07_place_name_update.txt', info_07)

        # ---------------- SCENARIO 08 & 09: INSERT/DELETE ----------------
        candidate = None
        for p in self.people.values():
            if not p.parents_family_id: continue
            fam = self.families.get(p.parents_family_id)
            if not fam: continue
            my_entry = next((c for c in fam.children if c['id'] == p.id), None)
            if my_entry and my_entry['type'] == 'ADOPTED':
                candidate = p
                break

        info_08_09 = "--- SCENARIO 08 & 09: INSERT / DELETE TEST CANDIDATE ---\n"
        info_08_09 += "Benchmark: Insert two biological parents and one sibling for an existing adopted person, then delete them.\n"
        
        if candidate:
            if self.target_population == 1000:
                f_id, m_id, sib_id, fam_id = 2001, 2002, 2003, 2001
            elif self.target_population == 10000:
                f_id, m_id, sib_id, fam_id = 20001, 20002, 20003, 20001
            else:
                f_id, m_id, sib_id, fam_id = 200001, 200002, 200003, 200001

            cy = candidate.birth_year
            f_bdate   = f"{cy - 30:04d}-06-15"
            f_ddate   = f"{cy - 30 + 65:04d}-11-02"
            m_bdate   = f"{cy - 27:04d}-03-22"
            m_ddate   = f"{cy - 27 + 70:04d}-01-10"
            mar_date  = f"{cy - 8:04d}-05-10"
            sib_bdate = f"{cy + 3:04d}-09-01"
            sib_ddate = f"{cy + 3 + 30:04d}-04-12"

            info_08_09 += f"\nTarget Person (Adopted child anchor):\n"
            info_08_09 += f"  - ID: {candidate.id}\n"
            info_08_09 += f"  - Name: {candidate.given_name} {candidate.surname}\n"
            info_08_09 += f"  - Birth year: {candidate.birth_year}\n"
            info_08_09 += f"  - Adopting Family ID: {candidate.parents_family_id}\n"
            info_08_09 += "This person has no biological parents in the dataset, making it safe to INSERT new ones.\n\n"
            
            info_08_09 += "[RECORDS TO BE INSERTED / DELETED]\n"
            info_08_09 += "Person entities to insert (Columns: id, given_name, surname, sex, is_deceased, birth_date, birth_place, death_date, death_place, cause_of_death, burial_place, occupation):\n"
            info_08_09 += f"  1. Father (ID {f_id}): 'Jan', 'Kowalski', 'M', true, '{f_bdate}', 'Kraków', '{f_ddate}', 'Kraków', 'Old age', 'Cemetery in Kraków', 'Farmer'\n"
            info_08_09 += f"  2. Mother (ID {m_id}): 'Anna', 'Kowalska', 'F', true, '{m_bdate}', 'Kraków', '{m_ddate}', 'Kraków', 'Fever', 'Cemetery in Kraków', 'Weaver'\n"
            info_08_09 += f"  3. Sibling (ID {sib_id}): 'Piotr', 'Kowalski', 'M', true, '{sib_bdate}', 'Kraków', '{sib_ddate}', 'Kraków', 'Accident', 'Cemetery in Kraków', 'Blacksmith'\n\n"
            
            info_08_09 += "Family entity to insert (Columns: id, status, marriage_date, marriage_place, husband_id, wife_id):\n"
            info_08_09 += f"  1. Marriage (ID {fam_id}): 'MARRIED', '{mar_date}', 'Kraków', {f_id}, {m_id}\n\n"
            
            info_08_09 += "Relationships to establish:\n"
            info_08_09 += f"  - Father (ID {f_id}) is husband of Family (ID {fam_id})\n"
            info_08_09 += f"  - Mother (ID {m_id}) is wife of Family (ID {fam_id})\n"
            info_08_09 += f"  - Biological parent-child link between Family (ID {fam_id}) and the anchor child (ID {candidate.id})\n"
            info_08_09 += f"  - Biological parent-child link between Family (ID {fam_id}) and the new sibling (ID {sib_id})\n"
        else:
            info_08_09 += "\nNo suitable adopted person without biological parents found in dataset.\n"
        
        write_scenario_file('scenario_08_09_insert_delete.txt', info_08_09)

        print(f"[{self.target_population}] Summary and scenario reports saved to '{self.output_dir}'.")

        self._update_scenario_files(
            lca_p1_id=best_pair_info['p1'] if best_pair_info else None,
            lca_p2_id=best_pair_info['p2'] if best_pair_info else None,
            ancestor_id=best_ancestor_person_id,
            descendant_id=best_descendant_person_id,
            surname=best_surname,
            year_start=best_year_start,
            candidate=candidate
        )


    # =========================================================================
    # QUERY UPDATE UTILITIES
    # =========================================================================
    def _update_scenario_files(
        self,
        lca_p1_id: Optional[int],
        lca_p2_id: Optional[int],
        ancestor_id: Optional[int],
        descendant_id: Optional[int],
        surname: Optional[str],
        year_start: Optional[int],
        candidate           # Person | None
    ):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(self.output_dir)))

        if self.target_population == 1000:
            size = "1k"
            new_f_id, new_m_id, new_sib_id, new_fam_id = 2001, 2002, 2003, 2001
        elif self.target_population == 10000:
            size = "10k"
            new_f_id, new_m_id, new_sib_id, new_fam_id = 20001, 20002, 20003, 20001
        else:
            size = "100k"
            new_f_id, new_m_id, new_sib_id, new_fam_id = 200001, 200002, 200003, 200001

        pg_base  = os.path.join(project_root, "query_performance_benchmark", "scenarios", "postgres_scenarios")
        n4j_base = os.path.join(project_root, "query_performance_benchmark", "scenarios", "neo4j_scenarios")

        def rw(path, transform):
            if not os.path.exists(path):
                print(f"  [WARN] Query file not found, skipping: {path}")
                return
            with open(path, 'r', encoding='utf-8') as fh:
                old = fh.read()
            new = transform(old)
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(new)

        def inject_rec(txt: str, text: str, is_cypher: bool) -> str:
            prefix = "//" if is_cypher else "--"
            marker = f"{prefix} RECOMMENDED PARAMETERS:"
            txt = re.sub(r'\n*' + re.escape(marker) + r'[^\n]*\n+', '\n\n', txt)
            def repl(m): return f"\n\n{marker} {text}\n\n{m.group(1)}"
            txt = re.sub(r'\n(WITH\s|SELECT\s|MATCH\s|UPDATE\s|DELETE\s|INSERT\s|CREATE\s)', repl, txt, count=1)
            return txt

        # ── SCENARIO 01: LCA
        if lca_p1_id and lca_p2_id:
            def upd_lca_sql(txt):
                txt = re.sub(r'(anc_a\s*\([^)]+\)\s*AS\s*\(\s*\n\s*SELECT\s+)\d+(\s*,\s*0\s*,\s*ARRAY\s*\[)\d+(\])', rf'\g<1>{lca_p1_id}\g<2>{lca_p1_id}\g<3>', txt)
                txt = re.sub(r'(anc_b\s*\([^)]+\)\s*AS\s*\(\s*\n\s*SELECT\s+)\d+(\s*,\s*0\s*,\s*ARRAY\s*\[)\d+(\])', rf'\g<1>{lca_p2_id}\g<2>{lca_p2_id}\g<3>', txt)
                return inject_rec(txt, f"Person A = {lca_p1_id}, Person B = {lca_p2_id}", False)

            def upd_lca_cypher(txt):
                txt = re.sub(r'(WHERE\s+startNode\.id\s+IN\s+\[)\d+\s*,\s*\d+(\])', rf'\g<1>{lca_p1_id}, {lca_p2_id}\g<2>', txt)
                txt = re.sub(r'(sId\s*=\s*)\d+(.*?AS\s+distA)', rf'\g<1>{lca_p1_id}\g<2>', txt)
                txt = re.sub(r'(sId\s*=\s*)\d+(.*?AS\s+distB)', rf'\g<1>{lca_p2_id}\g<2>', txt)
                return inject_rec(txt, f"Person A = {lca_p1_id}, Person B = {lca_p2_id}", True)

            rw(os.path.join(pg_base,  "scenario_01_lca", f"scenario_01_lca_{size}.sql"),    upd_lca_sql)
            rw(os.path.join(n4j_base, "scenario_01_lca", f"scenario_01_lca_{size}.cypher"), upd_lca_cypher)

        # ── SCENARIO 02: SURNAME FILTER
        if surname and year_start is not None:
            def upd_s02_sql(txt):
                txt = re.sub(r"(WHERE\s+p\.surname\s*=\s*')[^']+(')", rf"\g<1>{surname}\g<2>", txt)
                txt = re.sub(r'(BETWEEN\s+)\d+(\s+AND\s+)\d+', rf'\g<1>{year_start}\g<2>{year_start + 49}', txt)
                return inject_rec(txt, f"Surname = '{surname}', Birth Year Range = {year_start}-{year_start + 49}", False)

            def upd_s02_cypher(txt):
                txt = re.sub(r'(WHERE\s+n\.birthDate\.year\s*>=\s*)\d+(\s+and\s+n\.birthDate\.year\s*<=\s*)\d+', rf'\g<1>{year_start}\g<2>{year_start + 49}', txt, flags=re.IGNORECASE)
                txt = re.sub(r"(AND\s+n\.surname\s*=\s*')[^']+(')", rf"\g<1>{surname}\g<2>", txt)
                return inject_rec(txt, f"Surname = '{surname}', Birth Year Range = {year_start}-{year_start + 49}", True)

            rw(os.path.join(pg_base,  "scenario_02_surname_filter", f"scenario_02_surname_filter_{size}.sql"),    upd_s02_sql)
            rw(os.path.join(n4j_base, "scenario_02_surname_filter", f"scenario_02_surname_filter_{size}.cypher"), upd_s02_cypher)

        # ── SCENARIO 04: ANCESTORS
        if ancestor_id is not None:
            def upd_s04_sql(txt):
                txt = re.sub(r'(SELECT\s+)\d+(\s+AS\s+person_id\s*,\s*0\s+AS\s+depth)', rf'\g<1>{ancestor_id}\g<2>', txt)
                txt = re.sub(r'(WHERE\s+person_id\s*<>\s*)\d+', rf'\g<1>{ancestor_id}', txt)
                return inject_rec(txt, f"Person ID = {ancestor_id}", False)

            def upd_s04_cypher(txt):
                txt = re.sub(r'(MATCH\s+\(start:Person\s+\{id:\s*)\d+(\})', rf'\g<1>{ancestor_id}\g<2>', txt)
                return inject_rec(txt, f"Person ID = {ancestor_id}", True)

            rw(os.path.join(pg_base,  "scenario_04_ancestors", f"scenario_04_ancestors_{size}.sql"),    upd_s04_sql)
            rw(os.path.join(n4j_base, "scenario_04_ancestors", f"scenario_04_ancestors_{size}.cypher"), upd_s04_cypher)

        # ── SCENARIO 05: DESCENDANTS
        if descendant_id is not None:
            def upd_s05_sql(txt):
                txt = re.sub(r'(SELECT\s+)\d+(\s*,\s*0\s*,\s*NULL::int\s*,\s*ARRAY\s*\[)\d+(\])', rf'\g<1>{descendant_id}\g<2>{descendant_id}\g<3>', txt)
                txt = re.sub(r'(WHERE\s+person_id\s*<>\s*)\d+', rf'\g<1>{descendant_id}', txt)
                return inject_rec(txt, f"Person ID = {descendant_id}", False)

            def upd_s05_cypher(txt):
                txt = re.sub(r'(MATCH\s+\(start:Person\s+\{id:\s*)\d+(\})', rf'\g<1>{descendant_id}\g<2>', txt)
                return inject_rec(txt, f"Person ID = {descendant_id}", True)

            rw(os.path.join(pg_base,  "scenario_05_descendants", f"scenario_05_descendants_{size}.sql"),    upd_s05_sql)
            rw(os.path.join(n4j_base, "scenario_05_descendants", f"scenario_05_descendants_{size}.cypher"), upd_s05_cypher)

        # ── SCENARIO 08 & 09: INSERT/DELETE
        if candidate is not None:
            cy = candidate.birth_year
            f_by      = cy - 30
            m_by      = cy - 27
            mar_y     = cy - 8
            sib_by    = cy + 3
            f_dy      = f_by + 65
            m_dy      = m_by + 70
            sib_dy    = sib_by + 30

            def fy(y: int) -> str:
                return f"{y:04d}"

            def upd_s08_sql(txt):
                txt = re.sub(
                    rf"(\({new_f_id}\s*,\s*'Jan'\s*,\s*'Kowalski'\s*,\s*'M'\s*,\s*true\s*,\s*')\d{{4}}-06-15('\s*,\s*'Kraków'\s*,\s*')\d{{4}}-11-02(')",
                    rf"\g<1>{fy(f_by)}-06-15\g<2>{fy(f_dy)}-11-02\g<3>", txt)
                txt = re.sub(
                    rf"(\({new_m_id}\s*,\s*'Anna'\s*,\s*'Kowalska'\s*,\s*'F'\s*,\s*true\s*,\s*')\d{{4}}-03-22('\s*,\s*'Kraków'\s*,\s*')\d{{4}}-01-10(')",
                    rf"\g<1>{fy(m_by)}-03-22\g<2>{fy(m_dy)}-01-10\g<3>", txt)
                txt = re.sub(
                    rf"(\({new_fam_id}\s*,\s*'MARRIED'\s*,\s*')\d{{4}}-05-10(')",
                    rf"\g<1>{fy(mar_y)}-05-10\g<2>", txt)
                txt = re.sub(
                    rf"(-- ANCHOR\s*INSERT INTO family_children\s*\(family_id,\s*child_id,\s*relationship_type\)\s*VALUES\s*\({new_fam_id},\s*)\d+(\s*,\s*'BIOLOGICAL'\s*\))",
                    rf"\g<1>{candidate.id}\g<2>", txt)
                txt = re.sub(
                    rf"(\({new_sib_id}\s*,\s*'Piotr'\s*,\s*'Kowalski'\s*,\s*'M'\s*,\s*true\s*,\s*')\d{{4}}-09-01('\s*,\s*'Kraków'\s*,\s*')\d{{4}}-04-12(')",
                    rf"\g<1>{fy(sib_by)}-09-01\g<2>{fy(sib_dy)}-04-12\g<3>", txt)
                
                return inject_rec(txt, f"Adopted Anchor Person ID = {candidate.id}", False)

            def upd_s08_cypher(txt):
                txt = re.sub(
                    rf"(id:\s*{new_f_id}\s*,\s*givenName:\s*'Jan'.*?birthDate:\s*date\(')\d{{4}}-06-15('.*?deathDate:\s*date\(')\d{{4}}-11-02(')",
                    rf"\g<1>{fy(f_by)}-06-15\g<2>{fy(f_dy)}-11-02\g<3>", txt)
                txt = re.sub(
                    rf"(id:\s*{new_m_id}\s*,\s*givenName:\s*'Anna'.*?birthDate:\s*date\(')\d{{4}}-03-22('.*?deathDate:\s*date\(')\d{{4}}-01-10(')",
                    rf"\g<1>{fy(m_by)}-03-22\g<2>{fy(m_dy)}-01-10\g<3>", txt)
                txt = re.sub(
                    rf"(id:\s*{new_fam_id}\s*,.*?marriageDate:\s*date\(')\d{{4}}-05-10(')",
                    rf"\g<1>{fy(mar_y)}-05-10\g<2>", txt)
                txt = re.sub(
                    rf"(MATCH\s*\(f:Family\s*\{{id:\s*{new_fam_id}\}}\)\s*,\s*\(adopted:Person\s*\{{id:\s*)(?:\d+|<ANCHOR_ID>)(\}})",
                    rf"\g<1>{candidate.id}\g<2>", txt)
                txt = re.sub(
                    rf"(id:\s*{new_sib_id}\s*,\s*givenName:\s*'Piotr'.*?birthDate:\s*date\(')\d{{4}}-09-01('.*?deathDate:\s*date\(')\d{{4}}-04-12(')",
                    rf"\g<1>{fy(sib_by)}-09-01\g<2>{fy(sib_dy)}-04-12\g<3>", txt)
                
                return inject_rec(txt, f"Adopted Anchor Person ID = {candidate.id}", True)

            rw(os.path.join(pg_base,  "scenario_08_insert", f"scenario_08_insert_{size}.sql"),    upd_s08_sql)
            rw(os.path.join(n4j_base, "scenario_08_insert", f"scenario_08_insert_{size}.cypher"), upd_s08_cypher)

        print(f"[{self.target_population}] Scenario query files updated automatically.")