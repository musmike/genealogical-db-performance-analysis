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
        private int expectedCount;

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
            MemoryMonitor.StabilizeAsync().GetAwaiter().GetResult();
        }
        
        [Benchmark]
        public async Task<int> _N406()
        {
            int rowsCount = await driver.ExecuteReadConsumingAsync(repo.NeoScenario6, 
                scratch, (r, s) =>
            {
                s.ParentId         = r[0].As<int>();
                s.GivenName        = r[1].As<string?>();
                s.Surname          = r[2].As<string?>();
                s.Sex              = r[3].As<string>();
                s.BirthDate        = r[4] is LocalDate bd ? new DateOnly(bd.Year, bd.Month, bd.Day) : null;
                s.BirthPlace       = r[5].As<string?>();
                s.AgeAtFirstChild  = r[6].As<int>();
                s.AgeDiffDays      = r[7].As<int>();
                s.ChildId          = r[8].As<int>();
                s.ChildBirthDate   = r[9] is LocalDate cbd ? new DateOnly(cbd.Year, cbd.Month, cbd.Day) : null;
                s.ChildBirthPlace  = r[10].As<string?>();
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
