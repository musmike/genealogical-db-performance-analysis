import sys, os, time, csv, random, shutil
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
    MY_MAX_DROP_PCT = 4.0
    MY_MIN_DROP_ABS = 5

    if not yearly_data: return False, "No data to analyze"
    years, pops, max_drop_found = [], [], 0.0

    prev_alive = None
    for y, p in yearly_data:
        years.append(y);
        pops.append(p)
        if prev_alive is not None and p < prev_alive:
            drop_count = prev_alive - p
            drop_pct = (drop_count / prev_alive) * 100.0
            if drop_pct > max_drop_found: max_drop_found = drop_pct

            if target_pop == 1000:
                bad_drop = (drop_pct > MY_MAX_DROP_PCT) or (drop_count >= MY_MIN_DROP_ABS)
            else:
                bad_drop = (drop_pct > MY_MAX_DROP_PCT) and (drop_count >= MY_MIN_DROP_ABS)

            if bad_drop:
                return False, f"Drop {drop_pct:.1f}%"

        prev_alive = p

    if len(years) < 20: return False, "Simulation too short"

    strictness_threshold = 0.8
    y0, p0 = years[0], pops[0]
    yn, pn = years[-1], pops[-1]
    checkpoints = [0.2, 0.4, 0.6, 0.8]
    for frac in checkpoints:
        idx = int(len(years) * frac)
        y_i, p_i = years[idx], pops[idx]
        p_linear = p0 + (pn - p0) * ((y_i - y0) / (yn - y0))
        if p_i > p_linear * strictness_threshold:
            return False, f"Incorrect shape at {int(frac * 100)}% checkpoint"
    return True, f"OK (max drop {max_drop_found:.1f}%)"


def find_params_for_target(target_pop, depth_min, depth_max, base_seed, hyper_rng, max_attempts=40):
    for attempt in range(max_attempts):
        if target_pop == 1000:
            pairs = hyper_rng.randint(10, 40)
            children = round(hyper_rng.uniform(3.5, 4.0), 2)
            imm = 1
        elif target_pop == 10000:
            pairs = hyper_rng.randint(70, 110)
            children = round(hyper_rng.uniform(2.9, 3.5), 2)
            imm = 1
        else:
            pairs = hyper_rng.randint(115, 125)
            children = round(hyper_rng.uniform(2.85, 2.95), 2)
            imm = 1

        config.SCENARIOS[target_pop].update({'initial_pairs': pairs, 'avg_children': children, 'immigrants': imm})
        engine.SEED = base_seed
        with HiddenPrints():
            sim = engine.SimulationEngine(target_population=target_pop, output_dir=None)
            sim.run()

        if len(sim.people) < target_pop:
            print(f"\r[{target_pop}] Attempt {attempt + 1:02d}/{max_attempts} | Population collapse!{' ' * 40}", end="",
                  flush=True)
            continue

        depth = calculate_max_depth(sim.people, sim.families)

        is_shaped, shape_msg = is_shaped_correctly(
            sim.yearly_data,
            target_pop
        )

        target_str = f"<{depth_min}, {depth_max}>"
        print(
            f"\r[{target_pop}] Attempt {attempt + 1:02d}/{max_attempts} | Depth {depth:02d} (target: {target_str}) | Shape: {shape_msg:30s}",
            end="", flush=True)

        if depth_min <= depth <= depth_max and is_shaped:
            print(f"\n  ✓ FOUND FOR {target_pop}! (Depth: {depth})")
            return True, pairs, children, imm, depth

    print(f"\n  x NOT FOUND FOR {target_pop} for this seed.")
    return False, None, None, None, None


def run_hyper_search():
    if os.path.exists("temp"):
        shutil.rmtree("temp")

    print("===================================================================")
    print("SEED & PARAMETER SEARCH")
    print("===================================================================\n")

    hyper_rng = random.Random()
    start_time = time.time()

    while True:
        base_seed = hyper_rng.randint(1000, 999999)
        print(f"\n--- 🎲 TESTING SEED: {base_seed} ---")

        success_1k, p1, c1, i1, d1 = find_params_for_target(1000, 10, 10, base_seed, hyper_rng, max_attempts=300)
        if not success_1k: continue

        success_10k, p10, c10, i10, d10 = find_params_for_target(10000, 19, 21, base_seed, hyper_rng, max_attempts=80)
        if not success_10k: continue

        success_100k, p100, c100, i100, d100 = find_params_for_target(100000, 48, 52, base_seed, hyper_rng,
                                                                      max_attempts=40)
        if not success_100k: continue

        elapsed = time.time() - start_time

        print("\n" + "★" * 75)
        print(f"🏆 MAJOR SUCCESS! Ideal configuration found after {elapsed:.1f} seconds!")
        print(f"   Resulting depths: 1K = {d1} | 10K = {d10} | 100K = {d100}")
        print("Copy and paste the following code into config.py (replace the existing SCENARIOS and SEED section):\n")

        print(f"SEED = {base_seed}\n")
        print("SCENARIOS = {")
        print("   1000: {")
        print("       'min_lca_path': 8, 'max_lca_path': 8, 'ancestors_depth': 5, 'descendants_depth': 3,")
        print(f"       'start_year': 1800, 'initial_pairs': {p1}, 'avg_children': {c1}, 'immigrants': {i1}")
        print("   },")
        print("   10000: {")
        print("       'min_lca_path': 12, 'max_lca_path': 12, 'ancestors_depth': 10, 'descendants_depth': 6,")
        print(f"       'start_year': 1500, 'initial_pairs': {p10}, 'avg_children': {c10}, 'immigrants': {i10}")
        print("   },")
        print("   100000: {")
        print("       'min_lca_path': 16, 'max_lca_path': 16, 'ancestors_depth': 15, 'descendants_depth': 10,")
        print(f"       'start_year': 800, 'initial_pairs': {p100}, 'avg_children': {c100}, 'immigrants': {i100}")
        print("   }")
        print("}")
        print("★" * 75)

        break


if __name__ == '__main__':
    run_hyper_search()