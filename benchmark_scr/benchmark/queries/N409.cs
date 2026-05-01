using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class N409 {
        private Neo4jDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path;
        private MemoryMonitor monitor = null!;
        private int expectedAffected;
        private List<string> statements = null!;

        public N409() {
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
            monitor = new MemoryMonitor(env, nameof(N409));
            monitor.Start();
            
            statements = Neo4jDriver.SplitCypherStatements(repo.NeoScenario9);
            
            expectedAffected = repo.ExpectedCounts.GetValueOrDefault("Neo09", -1);
            
            if (expectedAffected == -1) {
                throw new InvalidOperationException(
                    "Expected count for Neo09 is missing in configuration."
                );
            }
        }

        [Benchmark]
        public async Task<int> _N409() {
            int objsCount = await driver.ExecuteWriteStatementsAsync(statements);
            
            if (objsCount != expectedAffected) {
                throw new InvalidOperationException(
                    $"Unexpected number of objects affected ({objsCount}). Expected {expectedAffected}."
                );
            }
            
            return objsCount;
        }
        
        [IterationSetup]
        public void _N409Setup() {
            driver.ExecuteWriteCypherAsync(repo.NeoScenario8)
                .GetAwaiter().GetResult();
            monitor.NextIteration();
        }
        
        [IterationCleanup]
        public void IterationCleanup() {
            MemoryMonitor.StabilizeAsync().GetAwaiter().GetResult();
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Dispose();
            monitor.Export();
        }
    }
}
