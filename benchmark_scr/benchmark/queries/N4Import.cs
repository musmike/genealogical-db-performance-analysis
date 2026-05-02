using benchmark_scr.monitoring;
using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    public class N4Import {
        private Neo4jDriver driver = null!;
        private QueryRepo repo = null!;
        private readonly string path;
        private DatabaseValidator validator = null!;
        private string _env = null!;

        public N4Import() {
            path = Configg.basePath;
        }

        [GlobalSetup]
        public void Setup() {
            var env = Environment.GetEnvironmentVariable("DATASET");
            _env = env;

            if(string.IsNullOrWhiteSpace(env))
                throw new Exception("DATASET env var is missing");

            Console.WriteLine($"RAW DATASET: {env}");

            var dataset = Enum.Parse<Dataset>(env, ignoreCase: true);
            validator = new DatabaseValidator(dataset);

            repo = new QueryRepo(path, dataset);
            
            EnvManager.PrepareNeo4j();
            
            driver = new Neo4jDriver("bolt://localhost:7687", "neo4j", "password");
        }
        
        [IterationSetup]
        public void IterationSetup() {
            BashRunner.RunAsync("bash", true, repo.Neo4jDropDbScript)
                .GetAwaiter().GetResult();
        }

        [Benchmark]
        public async Task Import() {
            await BashRunner.RunAsync("bash", true, repo.Neo4jImportScript);
        }

        [GlobalCleanup]
        public async Task Cleanup() {
            BashRunner.RunAsync("bash", true, repo.Neo4jCreateDbScript)
                .GetAwaiter().GetResult();
            driver.ExecuteWriteCypherAsync(repo.Neo4jCreateIndexesCypher)
                .GetAwaiter().GetResult();
            DiskSizeCollector.ExportNeo4j(_env, driver);
            await validator.ValidateNeo4jAsync();
        }
    }
}
