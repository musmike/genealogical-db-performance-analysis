import os
from engine import SimulationEngine

"""
Entry point for the entire generator. Runs three independent demographic simulations
for different target population sizes — small (1k), medium (10k), and large (100k).
Each simulation writes its results to a separate subdirectory under output/.
"""

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_base = os.path.join(base_dir, "output")

    # Small-scale simulation: 1k individuals
    engine_1k = SimulationEngine(target_population=1000, output_dir=os.path.join(output_base, "1k"))
    engine_1k.run()

    # Medium-scale simulation: 10k individuals
    engine_10k = SimulationEngine(target_population=10000, output_dir=os.path.join(output_base, "10k"))
    engine_10k.run()

    # Large-scale simulation: 100k individuals
    engine_100k = SimulationEngine(target_population=100000, output_dir=os.path.join(output_base, "100k"))
    engine_100k.run()