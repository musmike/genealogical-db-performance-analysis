using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class Ps07 {
        private PostgresDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;
        private int expectedCount;

        public Ps07() {
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
            monitor = new MemoryMonitor(env, nameof(Ps07));
            monitor.Start();
            
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Pg07", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Pg07 is missing in configuration."
                );
            }
        }
        
        [IterationSetup]
        public void IterationSetup() {
            monitor.NextIteration();
        }
        
        [Benchmark]
        public async Task<int> _Ps07() {
            int rowsCount = await driver.ExecuteNonQueryAsync(repo.PgScenario7);
            
            if (rowsCount != expectedCount) {
                throw new InvalidOperationException(
                    $"Unexpected number of rows returned ({rowsCount}). Expected {expectedCount}."
                );
            }
            
            return rowsCount;
        }

        [IterationCleanup]
        public void _Ps07Cleanup() {
            driver.ExecuteNonQuery(repo.PgReverse7);
            MemoryMonitor.StabilizeAsync().GetAwaiter().GetResult();
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Export();
        }
    }
}
