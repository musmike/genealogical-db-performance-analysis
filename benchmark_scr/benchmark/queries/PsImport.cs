using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class PsImport {
        private PostgresDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path;
        private DatabaseValidator validator = null!;
        private string env = null!;

        public PsImport() {
            path = Configg.basePath;
        }

        [GlobalSetup]
        public void Setup() {
            env = Environment.GetEnvironmentVariable("DATASET")!;

            if (string.IsNullOrWhiteSpace(env))
                throw new Exception("DATASET env var is missing");

            Console.WriteLine($"RAW DATASET: {env}");

            var dataset = Enum.Parse<Dataset>(env, ignoreCase: true);
            validator = new DatabaseValidator(dataset);

            repo = new QueryRepo(path, dataset);
            
            EnvManager.PreparePostgres();
            
            driver = new PostgresDriver(
                "Host=localhost;Port=5432;Username=user;Password=password;Database=benchmarkdb");
        }
        
        [IterationSetup]
        public void IterationSetup() {
            BashRunner.RunAsync("bash", true, repo.PgDropAndCreateDbScript)
                .GetAwaiter().GetResult();
        }

        [Benchmark]
        public async Task Import() {
            await BashRunner.RunAsync("bash", true, repo.PgImportScript);
        }

        [GlobalCleanup]
        public async Task Cleanup() {
            driver.Open();
            driver.ExecuteNonQuery(repo.PgCreateIndexesSql);
            DiskSizeCollector.ExportPostgres(env, driver);
            await validator.ValidatePostgresAsync(driver);
            driver.Dispose();
        }
    }
}
