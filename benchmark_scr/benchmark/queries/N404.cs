using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class N404 {
        private Neo4jDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path;
        private MemoryMonitor monitor = null!;
        private RelativeScratch scratch = null!;
        private int expectedCount;
        private List<string> sc4_statements = null!;

        public N404() {
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
            monitor = new MemoryMonitor(env, nameof(N404));
                        
            monitor.SetPhase(BenchmarkPhase.GlobalSetup);
            monitor.Start();
            monitor.RecordNeo4jHeap();
            
            sc4_statements = Neo4jDriver.SplitCypherStatements(repo.NeoScenario4);

            scratch = new RelativeScratch();
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Neo04", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Neo04 is missing in configuration."
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
        
        [IterationCleanup]
        public void IterationCleanup() {
            monitor.SetPhase(BenchmarkPhase.IterationCleanup);
            
            monitor.RecordNeo4jHeap();
            MemoryMonitor.Stabilize();
        }
        
        [Benchmark]
        public async Task<int> _N404()
        {
            int rowsCount = await driver.ExecuteReadStatementsConsumingAsync(sc4_statements, scratch, Neo4jMappers.MapRelative);
            
            if (rowsCount != expectedCount) {
                throw new InvalidOperationException(
                    $"Unexpected number of rows returned ({rowsCount}). Expected {expectedCount}."
                );
            }
            
            return rowsCount;
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
