using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;
using Neo4j.Driver;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace benchmark_scr.benchmark.queries {
    [MemoryDiagnoser]
    public class N401 {
        private Neo4jDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;

        public N401() {
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
            monitor = new MemoryMonitor(env, nameof(N401));
            monitor.Start();

        }
        [IterationSetup]
        public void IterationSetup() { 
            monitor.NextIteration();
        }
        [IterationCleanup]
        public void IterationCleanup() {
            MemoryMonitor.StabilizeAsync().GetAwaiter().GetResult();
        }
        [Benchmark]
        public void _N401() {
            driver.ExecuteReadScriptCountAsync(repo.NeoScenario1)
                .GetAwaiter()
                .GetResult();
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Export();
        }
    }
}
