"""
Entry point for the genealogical simulation.

Three separate simulation runs are executed sequentially, each targeting
a different population size and start year. Results are written
to dedicated output directories.
"""

from engine import SimulationEngine

if __name__ == "__main__":
    # Small-scale simulation: 1,000 individuals starting from the year 1800 (~10 generations)
    engine_1k = SimulationEngine(start_year=1800, end_year=2026, target_population=1000, output_dir="output/1k")
    engine_1k.run()

    # Medium-scale simulation: 10,000 individuals starting from the year 1600 (~20 generations)
    engine_10k = SimulationEngine(start_year=1600, end_year=2026, target_population=10000, output_dir="output/10k")
    engine_10k.run()

    # Large-scale simulation: 100,000 individuals starting from the year 900 (~50 generations)
    engine_100k = SimulationEngine(start_year=900, end_year=2026, target_population=100000, output_dir="output/100k")
    engine_100k.run()
