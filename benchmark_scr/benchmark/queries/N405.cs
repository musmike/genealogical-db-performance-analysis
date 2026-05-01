using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;
using Neo4j.Driver;

namespace benchmark_scr.benchmark.queries {
    public class N405 {
        private Neo4jDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path;
        private MemoryMonitor monitor = null!;
        private RelativeScratch scratch = null!;
        private int expectedCount;

        public N405() {
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
            monitor = new MemoryMonitor(env, nameof(N405));
            monitor.Start();
            
            scratch = new RelativeScratch();
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Neo05", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Neo05 is missing in configuration."
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
        public async Task<int> _N405()
        {
            int rowsCount = await driver.ExecuteReadConsumingAsync(repo.NeoScenario5,
                scratch, (r, s) =>
            {
                s.RelativeId   = r[0].As<int>();
                s.Generation   = r[1].As<int>();
                s.GivenName    = r[2].As<string?>();
                s.Surname      = r[3].As<string?>();
                s.Sex          = r[4].As<string>();
                s.BirthDate    = r[5] is LocalDate bd ? new DateOnly(bd.Year, bd.Month, bd.Day) : null;
                s.BirthPlace   = r[6].As<string?>();
                s.DeathDate    = r[7] is LocalDate dd ? new DateOnly(dd.Year, dd.Month, dd.Day) : null;
                s.DeathPlace   = r[8].As<string?>();
                s.BurialPlace  = r[9].As<string?>();
                s.CauseOfDeath = r[10].As<string?>();
                s.FatherId     = r[11].As<int?>();
                s.MotherId     = r[12].As<int?>();
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
            monitor.Dispose();
            monitor.Export();
        }
    }
}
