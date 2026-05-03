using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class Ps03 {
        private PostgresDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path;
        private MemoryMonitor monitor = null!;
        private BirthStatScratch scratch = null!;
        private int expectedCount;
        
        public Ps03() {
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
            monitor = new MemoryMonitor(env, nameof(Ps03));
            monitor.SetPhase(BenchmarkPhase.GlobalSetup);
            monitor.Start();
            
            scratch = new BirthStatScratch();
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Pg03", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Pg03 is missing in configuration."
                );
            }
        }
        
        [IterationSetup]
        public void IterationSetup() {
            monitor.NextIteration();
            monitor.SetPhase(BenchmarkPhase.IterationSetup);
            
            monitor.SetPhase(BenchmarkPhase.Measurement);
        }
        
        [IterationCleanup]
        public void IterationCleanup() {
            monitor.SetPhase(BenchmarkPhase.IterationCleanup);
            
            MemoryMonitor.Stabilize();
        }
        
        [Benchmark]
        public async Task<int> _Ps03() {
            int rowsCount = await driver.ExecuteConsumingAsync(repo.PgScenario3, scratch, PostgresMappers.MapSc03);
            
            if (rowsCount != expectedCount) {
                throw new InvalidOperationException(
                    $"Unexpected number of rows returned ({rowsCount}). Expected {expectedCount}."
                );
            }
            
            return rowsCount;
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.SetPhase(BenchmarkPhase.GlobalCleanup);
            
            monitor.Dispose();
            monitor.Export();
            driver.Dispose();
        }
    }

}
