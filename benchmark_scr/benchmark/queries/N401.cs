using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;
using Neo4j.Driver;

namespace benchmark_scr.benchmark.queries {
    [MemoryDiagnoser]
    public class N401 {
        private Neo4jDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;
        private LcaScratch scratch;
        private int expectedCount;

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

            scratch = new LcaScratch();
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Neo01", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Neo01 is missing in configuration."
                );
            }
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
        public async Task<int> _N401() {
            int rowsCount = await driver.ExecuteReadConsumingAsync(repo.NeoScenario1, scratch, (r, s) => {
                s.LcaId      = r["lca_id"].As<int>();
                s.GivenName  = r["given_name"].As<string?>();
                s.Surname    = r["surname"].As<string?>();
                s.Sex        = r["sex"].As<string>();
                s.BirthDate  = Neo4jDriver.ToDateOnly(r["birth_date"]);
                s.BirthPlace = r["birth_place"].As<string?>();
                s.DeathDate  = Neo4jDriver.ToDateOnly(r["death_date"]);
                s.DeathPlace = r["death_place"].As<string?>();
                s.PathFromA  = r["path_length_from_a"].As<int>();
                s.PathFromB  = r["path_length_from_b"].As<int>();
                s.TotalDist  = r["total_dist"].As<int>();
            });
            
            if (rowsCount != expectedCount) {
                throw new InvalidOperationException(
                    $"Unexpected number of rows returned ({rowsCount}). Expected {expectedCount}."
                );
            }
            
            return rowsCount;
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Export();
        }
    }
}
