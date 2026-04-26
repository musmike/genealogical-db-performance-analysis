using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    [MemoryDiagnoser]
    public class PsImport {
        private PostgresDriver driver;
        private QueryRepo repo;
        private readonly string path;

        public PsImport() {
            path = Configg.basePath;
        }

        [GlobalSetup]
        public void Setup() {
            var env = Environment.GetEnvironmentVariable("DATASET");

            if(string.IsNullOrWhiteSpace(env))
                throw new Exception("DATASET env var is missing");

            Console.WriteLine($"RAW DATASET: {env}");

            var dataset = Enum.Parse<Dataset>(env, ignoreCase: true);

            repo = new QueryRepo(path, dataset);
            driver = new PostgresDriver(
                "Host=localhost;Port=5432;Username=user;Password=password;Database=benchmark_db");

            driver.Open();
        }

        [Benchmark]
        public void Import() {
            driver.ExecuteNonQuery(repo.PgDDL);
            driver.ExecuteNonQuery(repo.PgData);
        }

        [GlobalCleanup]
        public void Cleanup() {
            driver.ExecuteNonQuery(repo.PgIndexes);
        }
    }
}
