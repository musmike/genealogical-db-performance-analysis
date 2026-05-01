using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class Ps06 {
        private PostgresDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path;
        private MemoryMonitor monitor = null!;
        private YoungestParentScratch scratch = null!;
        private int expectedCount;

        public Ps06() {
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
            monitor = new MemoryMonitor(env, nameof(Ps06));
            monitor.Start();
            
            scratch = new YoungestParentScratch();
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Pg06", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Pg06 is missing in configuration."
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
        public async Task<int> _Ps06() {
            int rowsCount = await driver.ExecuteConsumingAsync(repo.PgScenario6, 
                scratch, (r, s) => {
                    s.ParentId         = r.GetInt32(0);
                    s.GivenName        = r.IsDBNull(1) ? null : r.GetString(1);
                    s.Surname          = r.IsDBNull(2) ? null : r.GetString(2);
                    s.Sex              = r.GetString(3);
                    s.BirthDate        = r.IsDBNull(4) ? null : r.GetFieldValue<DateOnly>(4);
                    s.BirthPlace       = r.IsDBNull(5) ? null : r.GetString(5);
                    s.AgeAtFirstChild  = r.GetInt32(6);
                    s.AgeDiffDays      = r.GetInt32(7);
                    s.ChildId          = r.GetInt32(8);
                    s.ChildBirthDate   = r.IsDBNull(9)  ? null : r.GetFieldValue<DateOnly>(9);
                    s.ChildBirthPlace  = r.IsDBNull(10) ? null : r.GetString(10);
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
