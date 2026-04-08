import os
from engine import SimulationEngine

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_base = os.path.join(base_dir, "output")

    engine_1k = SimulationEngine(target_population=1000, output_dir=os.path.join(output_base, "1k"))
    engine_1k.run()

    engine_10k = SimulationEngine(target_population=10000, output_dir=os.path.join(output_base, "10k"))
    engine_10k.run()

    engine_100k = SimulationEngine(target_population=100000, output_dir=os.path.join(output_base, "100k"))
    engine_100k.run()