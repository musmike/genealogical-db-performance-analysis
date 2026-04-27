using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;
using Neo4j.Driver;

namespace benchmark_scr.benchmark.queries {
    public class N402 {
        private Neo4jDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;
        private PersonScratch scratch;
        private int expectedCount;

        public N402() {
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
            monitor = new MemoryMonitor(env, nameof(N402));
            monitor.Start();
            
            scratch = new PersonScratch();
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Neo02", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Neo02 is missing in configuration."
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
        public async Task<int> _N402()
        {
            int rowsCount = await driver.ExecuteReadConsumingAsync(repo.NeoScenario2, 
                scratch, (r, s) =>
            {
                s.PersonId = r["person_id"].As<int>();
                s.GivenName = r["given_name"].As<string>();
                s.Surname = r["surname"].As<string>();
                s.Sex = r["sex"].As<string>();
                s.BirthDate = Neo4jDriver.ToDateOnly(r["birth_date"]);
                s.BirthPlace = r["birth_place"].As<string?>();
                s.DeathDate = Neo4jDriver.ToDateOnly(r["death_date"]);
                s.DeathPlace = r["death_place"].As<string?>();
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
