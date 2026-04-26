using benchmark_scr.benchmark.readmodels;
using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class Ps06 {
        private PostgresDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;
        private YoungestParentScratch scratch;

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
            driver = new PostgresDriver(
                "Host=localhost;Port=5432;Username=user;Password=password;Database=benchmark_db");

            driver.Open();
            monitor = new MemoryMonitor(env, nameof(Ps06));
            monitor.Start();
            
            scratch = new YoungestParentScratch();
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
            return await driver.ExecuteConsumingAsync(repo.PgScenario6, 
                scratch, (r, s) => {
                s.ParentId         = r.GetInt32(0);
                s.GivenName        = r.GetString(1);
                s.Surname          = r.GetString(2);
                s.Sex              = r.GetString(3);
                s.BirthDate        = r.IsDBNull(4) ? null : r.GetFieldValue<DateOnly>(4);
                s.BirthPlace       = r.IsDBNull(5) ? null : r.GetString(5);
                s.AgeAtFirstChild  = r.GetInt32(6);
                s.AgeDiffDays      = r.GetInt32(7);
                s.ChildId          = r.GetInt32(8);
                s.ChildBirthDate   = r.IsDBNull(9)  ? null : r.GetFieldValue<DateOnly>(9);
                s.ChildBirthPlace  = r.IsDBNull(10) ? null : r.GetString(10);
            });
        }
        
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Export();
        }
    }
}
