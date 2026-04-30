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
                "Host=localhost;Port=5432;Username=user;Password=password;Database=benchmarkdb");
        }
        
        [IterationSetup]
        public void IterationSetup() {
            BashRunner.RunAsync(repo.PgDropAndCreateDbScript)
                .GetAwaiter().GetResult();
        }

        [Benchmark]
        public async Task Import() {
            await BashRunner.RunAsync(repo.PgImportScript);
        }

        [GlobalCleanup]
        public void Cleanup() {
            driver.Open();
            driver.ExecuteNonQuery(repo.PgCreateIndexesSql);
            driver.ExecuteNonQuery("VACUUM (ANALYZE) people;");
            driver.ExecuteNonQuery("VACUUM (ANALYZE) families;");
            driver.ExecuteNonQuery("VACUUM (ANALYZE) family_children;");
        }
    }
}
