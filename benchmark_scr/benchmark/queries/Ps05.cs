using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class Ps05 {
        private PostgresDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path;
        private MemoryMonitor monitor = null!;
        private RelativeScratch scratch = null!;
        private int expectedCount;

        public Ps05() {
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
            
            EnvManager.PreparePostgres();
            
            driver = new PostgresDriver(
                "Host=localhost;Port=5432;Username=user;Password=password;Database=benchmarkdb");

            driver.Open();
            monitor = new MemoryMonitor(env, nameof(Ps05));
            monitor.Start();
            
            scratch = new RelativeScratch();
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Pg05", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Pg05 is missing in configuration."
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
        public async Task<int> _Ps05() {
            int rowsCount = await driver.ExecuteConsumingAsync(repo.PgScenario5, 
                scratch, (r, s) => {
                    s.RelativeId   = r.GetInt32(0);
                    s.Generation   = r.GetInt32(1);
                    s.GivenName    = r.IsDBNull(2) ? null : r.GetString(2);
                    s.Surname      = r.IsDBNull(3) ? null : r.GetString(3);
                    s.Sex          = r.GetString(4);
                    s.BirthDate    = r.IsDBNull(5)  ? null : r.GetFieldValue<DateOnly>(5);
                    s.BirthPlace   = r.IsDBNull(6)  ? null : r.GetString(6);
                    s.DeathDate    = r.IsDBNull(7)  ? null : r.GetFieldValue<DateOnly>(7);
                    s.DeathPlace   = r.IsDBNull(8)  ? null : r.GetString(8);
                    s.BurialPlace  = r.IsDBNull(9)  ? null : r.GetString(9);
                    s.CauseOfDeath = r.IsDBNull(10) ? null : r.GetString(10);
                    s.FatherId     = r.IsDBNull(11) ? null : r.GetInt32(11);
                    s.MotherId     = r.IsDBNull(12) ? null : r.GetInt32(12);
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
