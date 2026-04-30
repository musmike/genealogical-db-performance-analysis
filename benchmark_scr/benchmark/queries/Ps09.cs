using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class Ps09 {
        private PostgresDriver driver = null!;
        private QueryRepo repo = null!;
        private MemoryMonitor monitor = null!;
        private readonly string path;
        private int expectedCount;

        public Ps09() {
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
            monitor = new MemoryMonitor(env, nameof(Ps09));
            monitor.Start();
            
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Pg09", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Pg09 is missing in configuration."
                );
            }
        }
        
        [IterationCleanup]
        public void IterationCleanup() {
            MemoryMonitor.StabilizeAsync().GetAwaiter().GetResult();
        }
        
        [Benchmark]
        public async Task<int> _Ps09() {
            int rowsCount = await driver.ExecuteNonQueryAsync(repo.PgScenario9);
            
            if (rowsCount != expectedCount) {
                throw new InvalidOperationException(
                    $"Unexpected number of rows returned ({rowsCount}). Expected {expectedCount}."
                );
            }
            
            return rowsCount;
        }
        
        [IterationSetup]
        public void _Ps09Setup() {
            driver.ExecuteNonQuery(repo.PgScenario8);
            monitor.NextIteration();
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Export();
        }
    }
}
