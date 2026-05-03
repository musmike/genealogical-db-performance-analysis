using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class Ps07 {
        private PostgresDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path;
        private MemoryMonitor monitor = null!;
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
            
            EnvManager.PreparePostgres();
            
            driver = new PostgresDriver(
                "Host=localhost;Port=5432;Username=user;Password=password;Database=benchmarkdb");

            driver.Open();
            monitor = new MemoryMonitor(env, nameof(Ps07));
            monitor.SetPhase(BenchmarkPhase.GlobalSetup);
            monitor.Start();
            
            expectedCount = repo.ExpectedCounts.GetValueOrDefault("Pg07", -1);
            
            if (expectedCount == -1) {
                throw new InvalidOperationException(
                    "Expected count for Pg07 is missing in configuration."
                );
            }
            
            driver.ExecuteNonQuery("ALTER TABLE people SET (autovacuum_enabled = false);");
            driver.ExecuteNonQuery("ALTER TABLE families SET (autovacuum_enabled = false);");
            driver.ExecuteNonQuery("ALTER TABLE family_children SET (autovacuum_enabled = false);");
        }
        
        [IterationSetup]
        public void IterationSetup() {
            monitor.NextIteration();
            monitor.SetPhase(BenchmarkPhase.IterationSetup);
            
            driver.ExecuteNonQuery("VACUUM (ANALYZE) people;");
            driver.ExecuteNonQuery("VACUUM (ANALYZE) families;");
            driver.ExecuteNonQuery("VACUUM (ANALYZE) family_children;");
            
            monitor.SetPhase(BenchmarkPhase.Measurement);
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
            monitor.SetPhase(BenchmarkPhase.IterationCleanup);
            
            driver.ExecuteNonQuery(repo.PgReverse7);
            
            driver.ExecuteNonQuery("VACUUM (ANALYZE) people;");
            driver.ExecuteNonQuery("VACUUM (ANALYZE) families;");
            driver.ExecuteNonQuery("VACUUM (ANALYZE) family_children;");
            
            MemoryMonitor.Stabilize();
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.SetPhase(BenchmarkPhase.GlobalCleanup);
            
            monitor.Dispose();
            monitor.Export();
            
            driver.ExecuteNonQuery("ALTER TABLE people SET (autovacuum_enabled = true);");
            driver.ExecuteNonQuery("ALTER TABLE families SET (autovacuum_enabled = true);");
            driver.ExecuteNonQuery("ALTER TABLE family_children SET (autovacuum_enabled = true);");
            
            driver.Dispose();
        }
    }
}
