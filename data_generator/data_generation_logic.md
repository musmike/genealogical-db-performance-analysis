# Data Generation — Design & Logic

This document describes the design decisions, algorithms, and configuration
behind the synthetic genealogical dataset generator used for the benchmark.

---

## Overview

The generator produces three independent, deterministic synthetic genealogies
targeting population sizes of 1 000, 10 000, and 100 000 individuals.
All runs use a fixed random seed (`SEED = 45656` in `config.py`) to guarantee
full reproducibility.

Each simulation produces two families of CSV files optimised for bulk import:
- **PostgreSQL** — normalised relational tables (`people`, `families`, `family_children`)
- **Neo4j** — node and relationship files compatible with `neo4j-admin import`

After export, an analytics pass verifies graph topology and writes pre-validated
test parameters for each benchmark scenario.

---

## Configuration (`config.py`)

Per-scale parameters are defined in the `SCENARIOS` dictionary:

| Parameter | 1 k | 10 k | 100 k |
|---|---|---|---|
| `start_year` | 1750 | 1500 | 800 |
| `initial_pairs` | 50 | 100 | 90 |
| `avg_children` | 2.7 | 2.7 | 2.7 |
| `ancestors_depth` | 5 | 10 | 15 |
| `descendants_depth` | 3 | 6 | 10 |
| `lca_path_length` | 8 | 12 | 16 |

Reference data (names, surnames, places, occupations, causes of death) are
Polish-language historical lists drawn from `config.py`.
Place names intentionally mix modern Polish and historical German variants
(e.g. *Posen*, *Danzig*) to support the place-name update scenario (Scenario 07).
Approximately 20 % of occupations and ~15 % of causes of death are `None`,
simulating realistic record sparsity.

---

## Simulation Engine (`engine.py`)

The simulation advances year-by-year from `start_year` until the target
population count is reached or exceeded.

### Founding generation
`initial_pairs` married couples are created at `start_year`.
Each couple receives a planned child count drawn from a Poisson distribution
(see [Demographics](#demographics-demographicspy) below).

### Annual cycle
Each simulated year executes the following steps in order:

1. **Age and mortality** — every living person is checked against their
   pre-assigned lifespan. Those who reach it are marked deceased.
2. **Child birth** — couples with remaining planned children produce a child
   if the mother's age and the child's scheduled birth year align.
3. **Marriage formation** — eligible singles (above marriage age, not too
   closely related) are paired. Each new couple draws a planned child count.
4. **Population check** — if the running total meets the target, a
   `TargetReachedException` stops the loop cleanly.

A safety limit of `start_year + 3000` years prevents infinite loops caused
by bad seeds or misconfiguration.

---

## Demographics (`demographics.py`)

### Family size — Poisson distribution
```python
# PMF: P(k) = (λ^k · e^-λ) / k!   with λ = avg_children = 2.7
weights = [(avg**k * exp(-avg)) / factorial(k) for k in range(14)]
count = random.choices(range(14), weights=weights)[0]
```
Poisson naturally models discrete count events and produces realistic tails
for both childless couples and unusually large families.

### Marriage age — Gaussian with rejection sampling
- Women: `gauss(μ=24, σ=3.5)`, clamped to [16, 50]
- Men: `gauss(μ=26, σ=4.0)`, clamped to [18, 65]

### Lifespan — bimodal (infant mortality + adult Gaussian)
- 15 % of individuals die before age 5 (uniform draw in [0, 5]).
- The remaining 85 % follow `gauss(μ=65, σ=15)`, clamped to [6, 100].

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
All other surnames are returned unchanged.

---

## Data Model

### Entities
| Entity | Key fields |
|---|---|
| `Person` | `id`, `given_name`, `surname`, `sex`, `birth_date`, `birth_place`, `death_date`, `death_place`, `cause_of_death`, `burial_place`, `occupation`, `is_deceased` |
| `Family` | `id`, `status`, `marriage_date`, `marriage_place`, `husband_id`, `wife_id`, `children[]` |

### Relationship types
- **`HUSBAND_OF` / `WIFE_OF`** — person → family (spouse role)
- **`HAS_CHILD`** — family → person (with `relationship_type`: `BIOLOGICAL`, `ADOPTED`, or `FOSTER`)

Child types are drawn with weights 96 % / 3 % / 1 % respectively.
Family status is drawn with weights: `MARRIED` 90 %, `PARTNERS` 6 %,
`OTHER` 4 %.

---

## Export (`exporter.py`)

### PostgreSQL format
Three CSV files per scale:
- `people.csv` — one row per person; Boolean `is_deceased` encoded as `0`/`1`.
- `families.csv` — one row per family unit.
- `family_children.csv` — junction table resolving the many-to-many
  parent–child relationship (1NF normalisation).

### Neo4j format
Five CSV files per scale, with type annotations in headers
(e.g. `birthDate:DATE`, `isDeceased:BOOLEAN`) as required by `neo4j-admin import`:
- `nodes_person.csv`, `nodes_family.csv`
- `rels_husband_of.csv`, `rels_wife_of.csv`, `rels_child_of.csv`

Each relationship type is kept in a separate file — a hard requirement
of the Neo4j bulk import tool.

---

## Post-simulation Analytics (`analytics.py`)

After export, `AnalyticsEngine` performs two tasks:

### 1. Graph topology verification
- Computes generational depth for every individual.
- Collects basic demographics: sex ratio, marriage rate, average lifespan,
  average children per family, leaf-node (end-of-lineage) distribution.

### 2. Benchmark scenario seed generation
For each benchmark scenario the engine searches the generated dataset for
input parameters that satisfy the scenario's structural requirements,
then writes them to `scenario_XX_*.txt` files and patches the corresponding
SQL/Cypher query files in the benchmark suite via regex substitution.

| Scenario | Search strategy |
|---|---|
| **01 — LCA** | Monte Carlo (1 500 iterations) over region-partitioned population; finds a pair whose biological LCA path length falls within the target range for the scale. |
| **02 — Surname filter** | Scans top-5 surnames for a 50-year window containing a result count in [n/20, n/8]. |
| **03 — Births per city** | Full aggregation, no search needed. |
| **04 — Ancestor retrieval** | BFS up the pedigree for the 200 youngest individuals; picks the one with the most distinct biological ancestors within the target depth. |
| **05 — Descendant retrieval** | BFS down the pedigree for a random sample of 500; picks the individual with the most distinct biological descendants. |
| **06 — Youngest parent** | Exhaustive scan of all biological parent–child pairs; finds the minimum age difference in days. |
| **07 — Place name update** | Counts rows affected by renaming the six historical German city names to their modern Polish equivalents. |
| **08/09 — Insert / Delete** | Locates an adopted child without biological parents in the dataset to serve as a safe anchor for the insertion test. |

All scenario files include the exact IDs and parameters needed to run the
benchmark queries without any manual adjustments.