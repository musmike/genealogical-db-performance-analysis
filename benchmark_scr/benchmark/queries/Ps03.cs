using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace benchmark_scr.benchmark.queries {
    public class Ps03 {
        private PostgresDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;

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
            driver = new PostgresDriver(
                "Host=localhost;Port=5432;Username=user;Password=password;Database=benchmark_db");

            driver.Open();
            monitor = new MemoryMonitor(env, nameof(Ps03));
            monitor.Start();
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
        public void _Ps03() {
            driver.ExecuteNonQuery(repo.PgScenario3);
        }
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Export();
        }
    }

}
