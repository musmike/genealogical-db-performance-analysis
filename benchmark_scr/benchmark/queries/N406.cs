using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class N406 {
        private Neo4jDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path = null!;
        private MemoryMonitor monitor = null!;
        private YoungestParentScratch scratch = null!;
        private int expectedCount;
        private List<string> statements = null!;

        public N406() {
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
            monitor = new MemoryMonitor(env, nameof(N406));
                        
            monitor.Start();
            monitor.RecordNeo4jHeap();
            
            statements = Neo4jDriver.SplitCypherStatements(repo.NeoScenario6);

            scratch = new YoungestParentScratch();
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Neo06", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Neo06 is missing in configuration."
                );
            }
        }
        
        [IterationSetup]
        public void IterationSetup() {
            monitor.NextIteration();
        }
        
        [IterationCleanup]
        public void IterationCleanup() {
            monitor.RecordNeo4jHeap();
            MemoryMonitor.Stabilize();
        }
        
        [Benchmark]
        public async Task<int> _N406()
        {
            int rowsCount = await driver.ExecuteReadStatementsConsumingAsync(statements, scratch, Neo4jMappers.MapSc06);
            
            if (rowsCount != expectedCount) {
                throw new InvalidOperationException(
                    $"Unexpected number of rows returned ({rowsCount}). Expected {expectedCount}."
                );
            }
            
            return rowsCount;
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.RecordNeo4jHeap();
            monitor.Dispose();
            monitor.Export();
            driver.DisposeAsync().GetAwaiter().GetResult();
        }
    }
}
