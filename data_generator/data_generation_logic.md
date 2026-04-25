# Data Generation — Design & Logic

This document describes the design decisions, algorithms, and configuration
behind the synthetic genealogical dataset generator used for the benchmark.

---

## Overview

The generator produces three independent, deterministic synthetic genealogies
targeting population sizes of 1 000, 10 000, and 100 000 individuals.
All runs use a fixed random seed (`SEED = 748376` in `config.py`) to guarantee
full reproducibility.

Each simulation produces two families of CSV files optimised for bulk import:
- **PostgreSQL** — normalised relational tables (`people`, `families`, `family_children`)
- **Neo4j** — node and relationship files compatible with `neo4j-admin import`

After export, an analytics pass verifies graph topology and writes pre-validated
test parameters for each benchmark scenario.

---

## Parameter Search (`parameter_search.py`)

To achieve specific demographic outcomes (e.g., exponential population growth without stagnation and exact generational depths), a dedicated script `parameter_search.py` is included. 

Running this script performs a Monte Carlo simulation over thousands of combinations of random seeds, initial pairs, and fertility rates. It evaluates:
1. **Growth Shape:** Rejects scenarios with sudden population drops (>4%) or extended stagnation periods.
2. **Graph Depth:** Ensures the maximum tree depth matches constraints.
3. **LCA Target:** Verifies that at least one pair of individuals satisfies the required Lowest Common Ancestor distance.
4. **Ancestor Discovery (Scenario 04):** Validates the degree of pedigree collapse by ensuring the simulation yields a sufficient number of distinct biological ancestors (e.g., >800 for 10 generations, and >8000 for 15 generations).

When an optimal configuration is found, the script outputs the exact Python code to paste into `config.py`.

---

## Configuration (`config.py`)

Per-scale parameters are defined in the `SCENARIOS` dictionary:

| Parameter | 1 k  | 10 k | 100 k |
|---|------|------|-------|
| `start_year` | 1650 | 1400 | 700   |
| `initial_pairs` | 19   | 63   | 77    |
| `avg_children` | 7.1  | 4.99 | 4.53  |
| `ancestors_depth` | 5    | 10   | 20    |
| `descendants_depth` | 5    | 10   | 17    |
| `lca_path_search_depth` | 8    | 12   | 21    |
| `lca_path_expected_depth` | 8    | 12   | 16    |
| `immigrants_per_year` | 1    | 2    | 4     |

Reference data (names, surnames, places, occupations, causes of death) are
Polish-language historical lists drawn from `config.py`.
Place names intentionally mix modern Polish and historical German variants
(e.g. *Posen*, *Danzig*) to support the place-name update scenario (Scenario 07).
Approximately 17% of occupations and ~15% of causes of death are `None`,
simulating realistic record sparsity.

---

## Simulation Engine (`engine.py`)

The simulation advances year-by-year from `start_year` until the target
population count is reached or exceeded.

### Founding generation & Immigration
`initial_pairs` married couples are created at `start_year`. 
Between simulation years 20 and 30, a small number of `immigrants_per_year` are 
injected to bridge generation gaps and prevent early population collapse.

### Annual cycle
Each simulated year executes the following steps in order:

1. **Births** — couples with remaining planned children produce a child
   if the mother's age and the child's scheduled birth year align and the father was alive.
2. **Marriage formation** — eligible singles (above marriage age, not too
   closely related, and excluding the 3% assigned to celibacy) are paired.
   Each new couple draws a planned child count.
3. **Divorces** — a very small fraction (0.05%) of marriages are dissolved.
4. **Deaths** — every living person is checked against their
   pre-assigned lifespan. Those who reach it are marked deceased.
5. **Population check** — if the running total meets the target, a
   `TargetReachedException` stops the loop cleanly.

A safety limit of `start_year + 3000` years prevents infinite loops caused
by bad seeds or misconfiguration.

---

## Demographics (`demographics.py`)

### Family size — Poisson distribution
```python
# PMF: P(k) = (λ^k · e^-λ) / k!   with λ = avg_children
weights = [(avg**k * exp(-avg)) / factorial(k) for k in range(14)]
count = random.choices(range(14), weights=weights)[0]
```
Poisson naturally models discrete count events and produces realistic tails
for both childless couples and unusually large families. Subsequent marriages 
have a reduced `avg_children` multiplier (0.6).

### Marriage age & Fertility — Gaussian with bounds
- Women: `gauss(μ=22, σ=3.5)`, clamped to [16, 50]. Fertility ends around age 41 (±4).
- Men: `gauss(μ=25, σ=4.0)`, clamped to [18, 65]. Fertility ends around age 52 (±6).

### Lifespan — Multi-modal distribution
- **0–1 years (Infant mortality):** 18%
- **1–5 years (Child mortality):** 12%
- **6–35 years (Young adult / Triangular distribution):** 8%
- **36–99 years (Adult / Weibull distribution):** 62% (centered ~56 years)

### Consanguinity guard
Before a marriage is formed, `is_too_closely_related()` blocks the union if:
- the candidates are the same individual,
- one is a direct lineal ancestor of the other (BFS up to 7 generations), or
- the sum of their distances to any common ancestor is ≤ 6
  (i.e. closer than second cousins once removed).

This BFS ancestor lookup traverses up to 5 generations and memoises
distances to shared ancestors.

### Surname feminisation
The three most common Polish adjectival suffixes are inflected automatically:
`-ski → -ska`, `-cki → -cka`, `-dzki → -dzka`.

---

## Data Model & Export (`exporter.py`)

### Relational / PostgreSQL format
- `people.csv` — person entities (`is_deceased` encoded as `0`/`1`).
- `families.csv` — family units (status: `MARRIED` 90%, `PARTNERS` 6%, `OTHER` 4%).
- `family_children.csv` — many-to-many parent–child relationship (types: `BIOLOGICAL` 96%, `ADOPTED` 3%, `FOSTER` 1%).

### Graph / Neo4j format
Files annotated with Neo4j bulk import headers (e.g. `birthDate:DATE`):
- Nodes: `nodes_person.csv`, `nodes_family.csv`
- Relationships: `rels_husband_of.csv`, `rels_wife_of.csv`, `rels_child_of.csv`

---

## Post-simulation Analytics (`analytics.py`)

After export, the analytics engine:
1. **Computes Demographics:** Calculates generational depths and standard demographic metrics (e.g., sex ratios, marriage rates, average lifespan, fertility rates).
2. **Generates Visualizations:** Produces four key diagnostic charts saved directly to the dataset directory:
   - `population_growth.png` — Tracks living population over simulation years.
   - `population_pyramid.png` — Standard demographic age-sex distribution of living individuals.
   - `tree_width_generations.png` — A spindle diagram visualizing the raw width of the genealogical tree (number of individuals generated per generation).
   - `network_topology.png` — A full pedigree network graph displaying nodes and edges layered strictly by generational depth.
3. **Automates Test Scenarios & Generates Expected Results:** Discovers exact entity IDs matching strict benchmark constraints (e.g., precise LCA paths, deepest lineages, optimal surnames for filtering) and dynamically patches the target SQL/Cypher benchmark scripts. Additionally, it populates the `expected_results/` directory with detailed reports indicating exactly what records and row counts the database queries should return, ensuring easy validation of benchmark correctness.