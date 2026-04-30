using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;
using Neo4j.Driver;

namespace benchmark_scr.benchmark.queries {
    [MemoryDiagnoser]
    public class N401 {
        private Neo4jDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path;
        private MemoryMonitor monitor = null!;
        private LcaScratch scratch = null!;
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
                s.LcaId      = r[0].As<int>();
                s.GivenName  = r[1].As<string?>();
                s.Surname    = r[2].As<string?>();
                s.Sex        = r[3].As<string>();
                s.BirthDate  = r[4] is LocalDate bd ? new DateOnly(bd.Year, bd.Month, bd.Day) : null;
                s.BirthPlace = r[5].As<string?>();
                s.DeathDate  = r[6] is LocalDate dd ? new DateOnly(dd.Year, dd.Month, dd.Day) : null;
                s.DeathPlace = r[7].As<string?>();
                s.PathFromA  = r[8].As<int>();
                s.PathFromB  = r[9].As<int>();
                s.TotalDist  = r[10].As<int>();
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
