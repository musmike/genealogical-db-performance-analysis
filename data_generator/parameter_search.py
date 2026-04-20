import sys, os, time, random, shutil
import exporter, analytics, engine, config


class DummyExporter:
    def __init__(self, *args, **kwargs): pass

    def export_to_postgres_csv(self): pass

    def export_to_neo4j_csv(self): pass


class DummyAnalytics:
    def __init__(self, *args, **kwargs): pass

    def run(self): pass


exporter.DataExporter = DummyExporter
analytics.AnalyticsEngine = DummyAnalytics


class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


def calculate_max_depth(people, families):
    def is_biological_child(p_id):
        p = people.get(p_id)
        if not p or not p.parents_family_id: return False
        fam = families.get(p.parents_family_id)
        if not fam: return False
        return any(c['id'] == p_id and c['type'] == 'BIOLOGICAL' for c in fam.children)

    depths, max_depth = {}, 0
    for p_id in sorted(people.keys()):
        p = people[p_id]
        if is_biological_child(p_id):
            fam = families[p.parents_family_id]
            d = max(depths.get(fam.husband_id, 0), depths.get(fam.wife_id, 0)) + 1
        else:
            d = 1
        depths[p_id] = d
        if d > max_depth: max_depth = d
    return max_depth


def is_shaped_correctly(yearly_data, target_pop):
    # Parameters for shape checking
    MAX_DROP_PCT = 4.0
    MAX_DROP_ABS = 5

    if target_pop == 1000:
        STAGNATION_WINDOW = 20
        MAX_DROP_ABS = 3
    elif target_pop == 10000:
        STAGNATION_WINDOW = 30
    else:
        STAGNATION_WINDOW = 50

    if not yearly_data: return False, "No data to analyze"
    years, pops, max_drop_found = [], [], 0.0

    prev_alive = None
    for y, p in yearly_data:
        years.append(y)
        pops.append(p)

        if len(pops) > STAGNATION_WINDOW:
            if pops[-1] <= pops[-1 - STAGNATION_WINDOW]:
                return False, f"Stagnation over {STAGNATION_WINDOW} years"

        if prev_alive is not None and p < prev_alive:
            drop_count = prev_alive - p
            drop_pct = (drop_count / prev_alive) * 100.0
            if drop_pct > max_drop_found: max_drop_found = drop_pct

            if target_pop == 1000:
                bad_drop = drop_count > MAX_DROP_ABS
            else:
                bad_drop = (drop_pct > MAX_DROP_PCT) and (drop_count > MAX_DROP_ABS)

            if bad_drop:
                return False, f"Drop {drop_pct:.1f}%, -{drop_count} people"

        prev_alive = p

    if len(years) < 20: return False, "Simulation too short"

    y0, p0 = years[0], pops[0]
    yn, pn = years[-1], pops[-1]
    checkpoints = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45,
                   0.50, 0.55, 0.60, 0.65, 0.70, 0.75,
                   0.80, 0.85, 0.90, 0.95]
    for frac in checkpoints:
        idx = int(len(years) * frac)
        y_i, p_i = years[idx], pops[idx]
        t = (y_i - y0) / (yn - y0)
        if target_pop == 1000: exp = 1.3
        else: exp = 1.5
        p_ref = p0 + (pn - p0) * (t ** exp)
        if p_i > p_ref:
            return False, f"Incorrect shape at {int(frac * 100)}% checkpoint"
    return True, f"OK (max drop {max_drop_found:.1f}%)"


def check_lca_exists(people, families, target_lca):
    """
    Checks if there exists at least one pair of individuals in the youngest 2000
    who have a common ancestor at exactly target_lca generations above them.
    """
    from demographics import is_too_closely_related

    def is_biological_child(p_id):
        p = people.get(p_id)
        if not p or not p.parents_family_id: return False
        fam = families.get(p.parents_family_id)
        if not fam: return False
        return any(c['id'] == p_id and c['type'] == 'BIOLOGICAL' for c in fam.children)

    youngest_ids = sorted([p.id for p in people.values()], key=lambda x: people[x].birth_date, reverse=True)[:2000]

    regions = {r: [] for r in config.PLACES.keys()}
    for p_id in youngest_ids:
        regions[people[p_id].region_id].append(p_id)

    bfs_limit = (target_lca // 2) + 10

    def get_ancestors_biological(p_id, limit):
        ancestors_paths = {p_id: 0}
        queue = [(p_id, 0)]
        while queue:
            curr_id, dist = queue.pop(0)
            if dist >= limit: continue
            if not is_biological_child(curr_id): continue
            fam = people[curr_id].parents_family_id
            if fam and fam in families:
                for parent_id in (families[fam].husband_id, families[fam].wife_id):
                    if parent_id and parent_id not in ancestors_paths:
                        ancestors_paths[parent_id] = dist + 1
                        queue.append((parent_id, dist + 1))
        return ancestors_paths

    available_regions = [r for r in regions if regions[r]]
    if len(available_regions) < 2: return False

    for _ in range(1500):
        r1, r2 = random.sample(available_regions, 2)
        p1_id = random.choice(regions[r1])
        p2_id = random.choice(regions[r2])

        if not is_too_closely_related(p1_id, p2_id, people, families):
            anc1 = get_ancestors_biological(p1_id, bfs_limit)
            anc2 = get_ancestors_biological(p2_id, bfs_limit)
            common = set(anc1.keys()).intersection(set(anc2.keys()))
            valid_lcas = [x for x in common if anc1[x] > 3 and anc2[x] > 3]

            if valid_lcas:
                if min(anc1[x] + anc2[x] for x in valid_lcas) == target_lca:
                    return True
    return False


def check_ancestors_target(people, families, target_pop):
    """
    Checks if there is an individual with enough distinct biological ancestors.
    Depth limits: 1k (5 gen -> max 62), 10k (10 gen -> max 2046), 100k (15 gen -> max 65534).
    """
    if target_pop == 1000:
        target_depth, required_count = 5, 58
    elif target_pop == 10000:
        target_depth, required_count = 10, 700
    else:
        target_depth, required_count = 15, 7000

    youngest_ids = sorted(people.keys(), key=lambda x: people[x].birth_date, reverse=True)[:200]

    best_count = 0
    for p_id in youngest_ids:
        distinct_ancestors = set()
        visited = {p_id}
        queue = [(p_id, 0)]
        while queue:
            curr, d = queue.pop(0)
            if d >= target_depth: continue

            p = people[curr]
            if not p.parents_family_id: continue
            fam = families[p.parents_family_id]

            is_bio = False
            for c in fam.children:
                if c['id'] == curr and c['type'] == 'BIOLOGICAL':
                    is_bio = True
                    break
            if not is_bio: continue

            for parent_id in (fam.husband_id, fam.wife_id):
                if parent_id and parent_id not in visited:
                    visited.add(parent_id)
                    distinct_ancestors.add(parent_id)
                    queue.append((parent_id, d + 1))

        count = len(distinct_ancestors)
        if count > best_count:
            best_count = count
        if best_count > required_count:
            return True, best_count

    return False, best_count

def find_params_for_target(target_pop, depth_min, depth_max, base_seed, rng, max_attempts=40):
    for attempt in range(max_attempts):
        if target_pop == 1000:
            pairs = rng.randint(10, 30)
            children = round(rng.uniform(6.7, 7.8), 2)
            immigrants = int(rng.uniform(0, 2))
        elif target_pop == 10000:
            pairs = rng.randint(60, 110)
            children = round(rng.uniform(4.9, 5.3), 2)
            immigrants = 2
        else:
            pairs = rng.randint(75, 100)
            children = round(rng.uniform(4.5, 4.65), 2)
            immigrants = 4

        target_lca = config.SCENARIOS[target_pop].get('lca_path', config.SCENARIOS[target_pop].get('min_lca_path'))

        config.SCENARIOS[target_pop].update(
            {'initial_pairs': pairs, 'avg_children': children, 'immigrants_per_year': immigrants})
        engine.SEED = base_seed
        with HiddenPrints():
            sim = engine.SimulationEngine(target_population=target_pop, output_dir=None)
            sim.run()

        depth = calculate_max_depth(sim.people, sim.families)
        target_str = f"<{depth_min}, {depth_max}>"

        # 1. Check depth
        if not (depth_min <= depth <= depth_max):
            print(f"\r[{target_pop}] Attempt {attempt + 1:02d}/{max_attempts} | Depth {depth:02d} (target: {target_str}) "
                  f"| Wrong depth, skipping...{' ' * 30}", end="", flush=True)
            continue

        # 2. Check population collapse
        if len(sim.people) < target_pop:
            print(f"\r[{target_pop}] Attempt {attempt + 1:02d}/{max_attempts} | Depth {depth:02d} (target: {target_str}) "
                  f"| Population collapse!{' ' * 40}", end="", flush=True)
            continue

        # 3. Check shape
        is_shaped, shape_msg = is_shaped_correctly(sim.yearly_data, target_pop)
        print(f"\r[{target_pop}] Attempt {attempt + 1:02d}/{max_attempts} | Depth {depth:02d} (target: {target_str}) "
              f"| Shape: {shape_msg:30s}", end="", flush=True)
        
        if not is_shaped:
            continue

        # 4. Check LCA
        print(" -> Verifying LCA...", end="", flush=True)
        if not check_lca_exists(sim.people, sim.families, target_lca):
            print(" LCA failed, retrying...{' ' * 10}", end="", flush=True)
            continue

        # 5. Check ancestors
        print(" OK -> Verifying Ancestors...", end="", flush=True)
        has_ancestors, anc_count = check_ancestors_target(sim.people, sim.families, target_pop)
        if not has_ancestors:
            print(f" Failed (Ancestors: {anc_count}), retrying...{' ' * 10}", end="", flush=True)
            continue

        print(f"\n  ✓ FOUND FOR {target_pop}! (Depth: {depth}, Ancestors: {anc_count})")
        return True, pairs, children, immigrants, depth

    print(f"\n  x NOT FOUND FOR {target_pop} for this seed.")
    return False, None, None, None, None

def run_parameter_search():
    if os.path.exists("temp"):
        shutil.rmtree("temp")

    print("===================================================================")
    print("SEED & PARAMETER SEARCH")
    print("===================================================================\n")

    rng = random.Random()
    start_time = time.time()

    while True:
        base_seed = rng.randint(1000, 999999)
        print(f"\n--- 🎲 TESTING SEED: {base_seed} ---")

        success_1k, p1, c1, i1, d1 = find_params_for_target(1000, 9, 11, base_seed, rng, max_attempts=300)
        if not success_1k: continue

        success_10k, p10, c10, i10, d10 = find_params_for_target(10000, 19, 21, base_seed, rng, max_attempts=500)
        if not success_10k: continue

        success_100k, p100, c100, i100, d100 = find_params_for_target(100000, 48, 52, base_seed, rng, max_attempts=150)
        if not success_100k: continue

        elapsed = time.time() - start_time

        print("\n" + "★" * 75)
        print(f"🏆 MAJOR SUCCESS! Ideal configuration found after {elapsed:.1f} seconds!")
        print(f"   Resulting depths: 1K = {d1} | 10K = {d10} | 100K = {d100}")
        print("Copy and paste the following code into config.py (replace the existing SCENARIOS and SEED section):\n")

        print(f"SEED = {base_seed}\n")
        print("SCENARIOS = {")

        results = {
            1000: (p1, c1, i1),
            10000: (p10, c10, i10),
            100000: (p100, c100, i100)
        }

        keys = list(config.SCENARIOS.keys())

        for i, pop in enumerate(keys):
            base = config.SCENARIOS[pop]

            pairs, children, immigrants = results.get(pop, (base['initial_pairs'], base['avg_children'],
                                                            base.get('immigrants_per_year', 1)))

            print(f"   {pop}: {{")
            print(
                f"       'lca_path': {base['lca_path']}, 'ancestors_depth': {base['ancestors_depth']}, 'descendants_depth': {base['descendants_depth']},")
            print(
                f"       'start_year': {base['start_year']}, 'initial_pairs': {pairs}, 'avg_children': {children}, 'immigrants_per_year': {immigrants}")

            if i < len(keys) - 1:
                print("   },")
            else:
                print("   }")

        print("}")
        print("★" * 75)

        break


if __name__ == '__main__':
    run_parameter_search()