using benchmark_scr.queries;
using BenchmarkDotNet.Attributes;

namespace benchmark_scr.benchmark.queries {
    [MemoryDiagnoser]
    public class N4Import {
        private Neo4jDriver driver;
        private QueryRepo repo;
        private readonly string path;

        public N4Import() {
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
            driver = new Neo4jDriver("bolt://localhost:7687", "neo4j", "password");
        }

        [Benchmark]
        public void Import() {
            BashRunner.RunAsync(repo.Neo4jImportScript)
                .GetAwaiter().GetResult();

        }

        [GlobalCleanup]
        public void Cleanup() {
            BashRunner.RunAsync(repo.Neo4jDatabaseScript)
                .GetAwaiter().GetResult();
            driver.ExecuteWriteScriptAsync(repo.Neo4jIndexesCypher)
                .GetAwaiter().GetResult();
        }
    }
}
