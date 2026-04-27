using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;
using Neo4j.Driver;

namespace benchmark_scr.benchmark.queries {
    public class N404 {
        private Neo4jDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;
        private RelativeScratch scratch;
        private int expectedCount;

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
            driver = new Neo4jDriver("bolt://localhost:7687", "neo4j", "password");
            monitor = new MemoryMonitor(env, nameof(N404));
            monitor.Start();

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
        }
        
        [IterationCleanup]
        public void IterationCleanup() {
            MemoryMonitor.StabilizeAsync().GetAwaiter().GetResult();
        }
        
        [Benchmark]
        public async Task<int> _N404()
        {
            int rowsCount = await driver.ExecuteReadConsumingAsync(repo.NeoScenario4, 
                scratch, (r, s) =>
            {
                s.RelativeId = r["ancestor_id"].As<int>();
                s.Generation = r["generation"].As<int>();
                s.GivenName = r["given_name"].As<string>();
                s.Surname = r["surname"].As<string>();
                s.Sex = r["sex"].As<string>();
                s.BirthDate = Neo4jDriver.ToDateOnly(r["birth_date"]);
                s.BirthPlace = r["birth_place"].As<string?>();
                s.DeathDate = Neo4jDriver.ToDateOnly(r["death_date"]);
                s.DeathPlace = r["death_place"].As<string?>();
                s.BurialPlace = r["burial_place"].As<string?>();
                s.CauseOfDeath = r["cause_of_death"].As<string?>();
                s.FatherId = r["father_id"].As<int?>();
                s.MotherId = r["mother_id"].As<int?>();
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
