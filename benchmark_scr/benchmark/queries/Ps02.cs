using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class Ps02 {
        private PostgresDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;
        private PersonScratch scratch;
        private int expectedCount;

        public Ps02() {
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
            driver = new PostgresDriver(
                "Host=localhost;Port=5432;Username=user;Password=password;Database=benchmark_db");

            driver.Open();
            monitor = new MemoryMonitor(env, nameof(Ps02));
            monitor.Start();
            
            scratch = new PersonScratch();
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Pg02", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Pg02 is missing in configuration."
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
        public async Task<int> _Ps02() {
            int rowsCount = await driver.ExecuteConsumingAsync(repo.PgScenario2, 
                scratch, (r, s) => {
                s.PersonId  = r.GetInt32(0);
                s.GivenName = r.GetString(1);
                s.Surname   = r.GetString(2);
                s.Sex       = r.GetString(3);
                s.BirthDate = r.IsDBNull(4) ? null : r.GetFieldValue<DateOnly>(4);
                s.BirthPlace = r.IsDBNull(5) ? null : r.GetString(5);
                s.DeathDate = r.IsDBNull(6) ? null : r.GetFieldValue<DateOnly>(6);
                s.DeathPlace = r.IsDBNull(7) ? null : r.GetString(7);
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
