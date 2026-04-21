using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace benchmark_scr.benchmark.queries {
    public class Ps08 {
        private PostgresDriver driver;
        private QueryRepo repo;
        private readonly string path;
        private MemoryMonitor monitor;

        public Ps08() {
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
            monitor = new MemoryMonitor(env, nameof(Ps08));
            monitor.Start();
        }
        [IterationSetup]
        public void IterationSetup() {
            monitor.NextIteration();
        }
        [Benchmark]
        public void _Ps08() {
            driver.ExecuteNonQuery(repo.PgScenario8);
        }
        [IterationCleanup]
        public void _Ps08Cleanup() {
            driver.ExecuteNonQuery(repo.PgScenario9);
            MemoryMonitor.StabilizeAsync().GetAwaiter().GetResult();
        }
        [GlobalCleanup]
        public void Cleanup() {
            monitor.Export();
        }
    }
}
