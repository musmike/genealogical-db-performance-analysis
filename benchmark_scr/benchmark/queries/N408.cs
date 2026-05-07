using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class N408 {
        private Neo4jDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path;
        private MemoryMonitor monitor = null!;
        private int expectedAffected;
        private List<string> sc8_statements = null!;

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
            
            EnvManager.PrepareNeo4j();
            
            driver = new Neo4jDriver("bolt://localhost:7687", "neo4j", "password");
            monitor = new MemoryMonitor(env, nameof(N408));
                        
            monitor.SetPhase(BenchmarkPhase.GlobalSetup);
            monitor.Start();
            monitor.RecordNeo4jHeap();
            
            sc8_statements = Neo4jDriver.SplitCypherStatements(repo.NeoScenario8);
            
            expectedAffected = repo.ExpectedCounts.GetValueOrDefault("Neo08", -1);
            
            if (expectedAffected == -1) {
                throw new InvalidOperationException(
                    "Expected count for Neo08 is missing in configuration."
                );
            }
        }
        
        [IterationSetup]
        public void IterationSetup() {
            monitor.NextIteration();
            monitor.SetPhase(BenchmarkPhase.IterationSetup);

            driver.ExecuteWriteCypherAsync("RETURN 1;")
                .GetAwaiter().GetResult();
            
            monitor.SetPhase(BenchmarkPhase.Measurement);
        }
        
        [Benchmark]
        public async Task<int> _N408() {
            int objsCount = await driver.ExecuteWriteStatementsAsync(sc8_statements);
            
            if (objsCount != expectedAffected) {
                throw new InvalidOperationException(
                    $"Unexpected number of objects affected ({objsCount}). Expected {expectedAffected}."
                );
            }
            
            return objsCount;
        }
        
        [IterationCleanup]
        public void _N408Cleanup() {
            monitor.SetPhase(BenchmarkPhase.IterationCleanup);
            
            monitor.RecordNeo4jHeap(); 
            driver.ExecuteWriteCypherAsync(repo.NeoScenario9)
                .GetAwaiter().GetResult();
            MemoryMonitor.Stabilize();
        }
        
        [GlobalCleanup]
        public async Task Cleanup() {
            monitor.SetPhase(BenchmarkPhase.GlobalCleanup);
            
            monitor.RecordNeo4jHeap();
            monitor.Dispose();
            monitor.Export();
            await driver.DisposeAsync();
        }
    }
}
