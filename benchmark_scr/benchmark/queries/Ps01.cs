using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    [MemoryDiagnoser]
    public class Ps01 {
        private PostgresDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;
        private LcaScratch scratch;

        public Ps01() {
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
            monitor = new MemoryMonitor(env, nameof(Ps01));
            monitor.Start();
            
            scratch = new LcaScratch();
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
        public async Task<int> _Ps01() {
            return await driver.ExecuteConsumingAsync(repo.PgScenario1, 
                scratch, (r, s) => {
                s.LcaId     = r.GetInt32(0);
                s.GivenName = r.GetString(1);
                s.Surname   = r.GetString(2);
                s.Sex       = r.GetString(3);
                s.BirthDate = r.IsDBNull(4) ? null : r.GetFieldValue<DateOnly>(4);
                s.BirthPlace = r.IsDBNull(5) ? null : r.GetString(5);
                s.DeathDate = r.IsDBNull(6) ? null : r.GetFieldValue<DateOnly>(6);
                s.DeathPlace = r.IsDBNull(7) ? null : r.GetString(7);
                s.PathFromA = r.GetInt32(8);
                s.PathFromB = r.GetInt32(9);
                s.TotalDist = r.GetInt32(10);
            });
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Export();
        }
    }
}
