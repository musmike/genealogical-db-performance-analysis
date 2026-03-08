"""
Core simulation engine for the genealogical population generator.

SimulationEngine drives year-by-year population dynamics: it initializes a
founding generation, then iterates forward in time processing deaths, divorces,
births, and marriages until the target population size is reached. On completion
it exports all records to CSV files and runs a graph-analytics report covering
LCA path lengths and ancestor-retrieval metrics.
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
                p.death_cause = random.choice(CAUSES_OF_DEATH)
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

    def export_to_csv(self):
        """
        Write all simulation records to three CSV files in the output directory.

        Files produced:
        - people.csv:          One row per individual with biographical attributes.
        - families.csv:        One row per family unit with marriage metadata.
        - family_children.csv: One row per parent-child link with relationship type.
        """
        with open(f'{self.output_dir}/people.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(
                ['id', 'given_name', 'surname', 'sex', 'is_deceased', 'birth_place', 'birth_date', 'death_place',
                 'death_date', 'death_cause', 'burial_place', 'occupation'])
            for p in self.people.values():
                writer.writerow([
                    p.id, p.given_name, p.surname, p.sex, 1 if p.is_deceased else 0,
                    p.birth_place, p.birth_date.isoformat() if p.birth_date else '',
                    p.death_place if p.is_deceased else '',
                    p.death_date.isoformat() if p.death_date else '',
                    p.death_cause if p.is_deceased else '',
                    p.burial_place if p.is_deceased else '',
                    p.occupation
                ])

        with open(f'{self.output_dir}/families.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'status', 'marriage_date', 'marriage_place', 'husband_id', 'wife_id'])
            for fam in self.families.values():
                writer.writerow([
                    fam.id, fam.status, fam.marriage_date.isoformat() if fam.marriage_date else '',
                    fam.marriage_place, fam.husband_id, fam.wife_id
                ])

        with open(f'{self.output_dir}/family_children.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['family_id', 'child_id', 'relationship_type'])
            for fam in self.families.values():
                for child_dict in fam.children:
                    writer.writerow([fam.id, child_dict['id'], child_dict['type']])

    def run_analytics(self):
        """
        Compute and write a graph-analytics report for the completed simulation.

        The report covers three areas:

        1. Population growth log — snapshots recorded during the simulation run.

        2. Graph topology — the maximum generational depth of the family tree,
           measured as the longest path from any root individual (no parents) to
           any descendant.

        3. LCA (Lowest Common Ancestor) search — a randomized search over pairs
           of young individuals from different regions to find a pair whose shortest
           path through a common ancestor matches the configured target length.
           The search respects a kinship exclusion constraint: neither individual
           may be closely related to the other, and each must be at least 4 steps
           away from the LCA.

        4. Ancestor retrieval scenario — identifies the individual among a sample
           of the youngest persons who has the greatest number of distinct ancestors
           within the configured depth limit, providing a benchmark query target.

        Results are written to analytics.txt in the output directory.
        """
        config = SCENARIOS.get(self.target_population, {'min_lca_path': 8, 'max_lca_path': 99, 'ancestors_depth': 5})
        target_lca_min = config['min_lca_path']
        target_lca_max = config.get('max_lca_path', 999)
        target_ancestors_depth = config['ancestors_depth']

        if target_lca_min == target_lca_max:
            target_label = str(target_lca_min)
        else:
            target_label = f"{target_lca_min}-{target_lca_max}"

        filepath = os.path.join(self.output_dir, 'analytics.txt')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=== GRAPH AND LCA ANALYSIS REPORT ===\n")
            f.write(f"Target population: {self.target_population}\n")
            f.write(f"Total people generated: {len(self.people)}\n")
            f.write(f"People alive at end of simulation ({self.current_year}): {len(self.living_people_ids)}\n")
            f.write(f"Total families: {len(self.families)}\n\n")

            f.write("--- POPULATION GROWTH OVER TIME ---\n")
            for log in self.history_log:
                f.write(log + "\n")
            f.write("\n")

            # Compute generational depth for every individual via a single forward pass
            # over IDs in insertion order (parents always have lower IDs than children).
            depths = {}
            max_depth = 0
            for p_id in sorted(self.people.keys()):
                p = self.people[p_id]
                if p.parents_family_id:
                    fam = self.families[p.parents_family_id]
                    d_husband = depths.get(fam.husband_id, 0) if fam.husband_id else 0
                    d_wife = depths.get(fam.wife_id, 0) if fam.wife_id else 0
                    d = max(d_husband, d_wife) + 1
                else:
                    d = 1
                depths[p_id] = d
                if d > max_depth:
                    max_depth = d

            f.write("--- GRAPH TOPOLOGY ---\n")
            f.write(f"Max graph depth (from oldest ancestor to youngest descendant): {max_depth} generations.\n\n")

            # Restrict LCA search to a manageable sample of the youngest individuals
            # to keep runtime proportional to population size.
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

            # Bucket sampled individuals by region to enforce cross-region pair selection.
            regions = {0: [], 1: [], 2: [], 3: [], 4: []}
            for p_id in youngest_ids:
                regions[self.people[p_id].region_id].append(p_id)

            # Limit BFS depth to slightly beyond half the maximum target path length
            # to avoid exploring ancestry far beyond what the target requires.
            bfs_limit = (target_lca_max // 2) + 10

            def get_ancestors_with_paths_limited(p_id, limit):
                """
                Return a dict mapping ancestor IDs to their BFS distance from p_id.
                Traversal is capped at 'limit' steps to bound computation time.
                """
                ancestors_paths = {p_id: 0}
                queue = [(p_id, 0)]
                while queue:
                    curr_id, dist = queue.pop(0)
                    if dist >= limit:
                        continue
                    p = self.people[curr_id]
                    if p.parents_family_id:
                        fam = self.families[p.parents_family_id]
                        for parent_id in (fam.husband_id, fam.wife_id):
                            if parent_id and parent_id not in ancestors_paths:
                                ancestors_paths[parent_id] = dist + 1
                                queue.append((parent_id, dist + 1))
                return ancestors_paths

            max_distance = 0
            best_pair_info = None
            iterations = 1500

            for i in range(iterations):
                msg = f"\r[{self.target_population}] LCA search: {i + 1}/{iterations} | best so far: {max_distance} (target: {target_label})    "
                sys.stdout.write(msg)
                sys.stdout.flush()

                available_regions = [r for r in regions if regions[r]]
                if len(available_regions) < 2:
                    break

                # Sample one individual from each of two distinct regions.
                r1, r2 = random.sample(available_regions, 2)
                p1_id = random.choice(regions[r1])
                p2_id = random.choice(regions[r2])

                if not is_too_closely_related(p1_id, p2_id, self.people, self.families):
                    anc1 = get_ancestors_with_paths_limited(p1_id, bfs_limit)
                    anc2 = get_ancestors_with_paths_limited(p2_id, bfs_limit)

                    common = set(anc1.keys()).intersection(set(anc2.keys()))
                    # Require both individuals to be at least 4 steps from any candidate LCA
                    # to ensure a non-trivial path through the ancestor graph.
                    valid_lcas_for_check = [x for x in common if anc1[x] > 3 and anc2[x] > 3]

                    if valid_lcas_for_check:
                        min_total_dist = min(anc1[x] + anc2[x] for x in valid_lcas_for_check)

                        if min_total_dist > max_distance and min_total_dist <= target_lca_max:
                            max_distance = min_total_dist
                            lcas_at_min_dist = [x for x in valid_lcas_for_check if
                                                anc1[x] + anc2[x] == min_total_dist]
                            lca_details = [(x, anc1[x], anc2[x]) for x in lcas_at_min_dist]

                            best_pair_info = {
                                'p1': p1_id,
                                'p2': p2_id,
                                'lcas': lca_details,
                                'dist1': lca_details[0][1],
                                'dist2': lca_details[0][2],
                                'total_dist': max_distance
                            }

                            # Early exit once a pair satisfying the configured target range is found.
                            if target_lca_min <= max_distance <= target_lca_max:
                                sys.stdout.write(f"\n")
                                sys.stdout.flush()
                                f.write(
                                    f"(Target value of {target_label} reached at iteration {i + 1}. Stopping search early.)\n"
                                )
                                break
            else:
                sys.stdout.write("\n")
                sys.stdout.flush()

            f.write("--- LOWEST COMMON ANCESTOR (LCA) SEARCH ---\n")
            f.write(f"Target LCA path length required: {target_label}\n")
            f.write("Constraint: Person A and Person B are not closely related AND distance to LCA > 3 for both sides.\n")

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
                f.write("No common ancestors found satisfying the strict criteria (>3 distance for both, within target).\n\n")

            f.write("--- ANCESTOR RETRIEVAL SCENARIO ---\n")
            f.write(f"Objective: Find person with most distinct ancestors up to {target_ancestors_depth} generations back.\n")

            best_ancestor_count = 0
            best_person_id = None
            # Use only the 200 youngest individuals to keep the search tractable.
            sample_for_ancestors = youngest_ids[:200]

            for p_id in sample_for_ancestors:
                distinct_ancestors = set()
                queue = [(p_id, 0)]
                while queue:
                    curr, d = queue.pop(0)
                    if d >= target_ancestors_depth:
                        continue
                    curr_p = self.people[curr]
                    if curr_p.parents_family_id:
                        fam = self.families[curr_p.parents_family_id]
                        if fam.husband_id:
                            distinct_ancestors.add(fam.husband_id)
                            queue.append((fam.husband_id, d + 1))
                        if fam.wife_id:
                            distinct_ancestors.add(fam.wife_id)
                            queue.append((fam.wife_id, d + 1))

                count = len(distinct_ancestors)
                if count > best_ancestor_count:
                    best_ancestor_count = count
                    best_person_id = p_id

            if best_person_id:
                f.write(f"Recommended Person ID: {best_person_id}\n")
                f.write(f"Distinct ancestors found (Depth <= {target_ancestors_depth}): {best_ancestor_count}\n")
                theoretical_max = sum([2 ** i for i in range(1, target_ancestors_depth + 1)])
                f.write(f"Theoretical max (Perfect Tree): {theoretical_max}\n")
                if target_ancestors_depth > 10:
                    f.write("(Note: High pedigree collapse is biologically expected here.)\n")
            else:
                f.write("Could not find any ancestors for the sampled group.\n")

        print(f"[{self.target_population}] Analytics report saved to '{filepath}'.")

    def run(self):
        """
        Execute the full simulation lifecycle for this engine instance.

        Initializes the founding population, then advances year by year,
        processing deaths, divorces, births, and marriages in that order.
        The loop terminates when the target population count is reached,
        the living population goes extinct, or a 2000-year safety cap is hit.
        On completion, CSV export and analytics are triggered automatically.
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

        self.export_to_csv()
        self.run_analytics()