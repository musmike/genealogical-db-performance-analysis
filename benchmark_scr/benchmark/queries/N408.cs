using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace benchmark_scr.benchmark.queries {
    public class N408 {
        private Neo4jDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;

        public N408() {
            path = Configg.basePath;
        }
        [GlobalSetup]
        public void GlobalSetup() {
            var env = Environment.GetEnvironmentVariable("DATASET");

            if(string.IsNullOrWhiteSpace(env))
                throw new Exception("DATASET env var is missing");

            Console.WriteLine($"RAW DATASET: {env}");

            var dataset = Enum.Parse<Dataset>(env, ignoreCase: true);

            repo = new QueryRepo(path, dataset);
            driver = new Neo4jDriver("bolt://localhost:7687", "neo4j", "password");
            monitor = new MemoryMonitor(env, nameof(N408));
            monitor.Start();
        }
        [IterationSetup]
        public void IterationSetup() {
            monitor.NextIteration();
        }
        [Benchmark]
        public void _N408() {
            driver.ExecuteWriteScriptAsync(repo.NeoScenario8)
                .GetAwaiter()
                .GetResult();
        }
        [IterationCleanup]
        public void _N408Cleanup() {
            driver.ExecuteWriteScriptAsync(repo.NeoScenario9)
                .GetAwaiter() .GetResult();
            MemoryMonitor.StabilizeAsync().GetAwaiter().GetResult();
        }
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Export();
        }
    }
}
