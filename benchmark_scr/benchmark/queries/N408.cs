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
        private List<string> statements = null!;

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
            monitor.Start();
            
            statements = Neo4jDriver.SplitCypherStatements(repo.NeoScenario8);
            
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
        }
        
        [Benchmark]
        public async Task<int> _N408() {
            int objsCount = await driver.ExecuteWriteStatementsAsync(statements);
            
            if (objsCount != expectedAffected) {
                throw new InvalidOperationException(
                    $"Unexpected number of objects affected ({objsCount}). Expected {expectedAffected}."
                );
            }
            
            return objsCount;
        }
        
        [IterationCleanup]
        public void _N408Cleanup() {
            MemoryMonitor.StabilizeAsync().GetAwaiter().GetResult();
            driver.ExecuteWriteCypherAsync(repo.NeoScenario9)
                .GetAwaiter().GetResult();
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Dispose();
            monitor.Export();
        }
    }
}
