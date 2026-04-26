using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;
using Neo4j.Driver;

namespace benchmark_scr.benchmark.queries {
    public class N406 {
        private Neo4jDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;
        private YoungestParentScratch scratch;

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
            driver = new Neo4jDriver("bolt://localhost:7687", "neo4j", "password");
            monitor = new MemoryMonitor(env, nameof(N406));
            monitor.Start();

            scratch = new YoungestParentScratch();
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
        public async Task<int> _N406()
        {
            return await driver.ExecuteReadConsumingAsync(repo.NeoScenario6, 
                scratch, (r, s) =>
            {
                s.ParentId = r["parent_id"].As<int>();
                s.GivenName = r["given_name"].As<string>();
                s.Surname = r["surname"].As<string>();
                s.Sex = r["sex"].As<string>();
                s.BirthDate = Neo4jDriver.ToDateOnly(r["birth_date"]);
                s.BirthPlace = r["birth_place"].As<string?>();
                s.AgeAtFirstChild = r["age_at_first_child"].As<int>();
                s.AgeDiffDays = r["age_difference_in_days"].As<int>();
                s.ChildId = r["child_id"].As<int>();
                s.ChildBirthDate = Neo4jDriver.ToDateOnly(r["child_birth_date"]);
                s.ChildBirthPlace = r["child_birth_place"].As<string?>();
            });
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Export();
        }
    }
}
