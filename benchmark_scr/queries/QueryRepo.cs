using System.Text.Json;

namespace benchmark_scr.queries {
    internal class QueryRepo {
        private static readonly object _lock = new();
        private static readonly Dictionary<Dataset, QueryRepo> _instances = new();
        public static QueryRepo Get(string basePath, Dataset dataset) {
            lock(_lock) {
                if(!_instances.TryGetValue(dataset, out var instance)) {
                    instance = new QueryRepo(basePath, dataset);
                    _instances[dataset] = instance;
                }

                return instance;
            }
        }
        
        private static readonly HashSet<int> UniversalScenarios = new() { 3, 6, 7 };

        private static readonly Dictionary<Dataset, string> DatasetSuffix = new()
        {
            { Dataset.small, "1k" },
            { Dataset.medium, "10k" },
            { Dataset.large, "100k" }
        };
        
        public string PgDropAndCreateDbScript { get; }
        public string PgImportScript { get; }
        public string PgCreateIndexesSql { get; }
        public string Neo4jDropDbScript { get; }
        public string Neo4jImportScript { get; }
        public string Neo4jCreateDbScript { get; }
        public string Neo4jCreateIndexesCypher { get; }
        
        public string PgScenario1 { get; }
        public string PgScenario2 { get; }
        public string PgScenario3 { get; }
        public string PgScenario4 { get; }
        public string PgScenario5 { get; }
        public string PgScenario6 { get; }
        public string PgScenario7 { get; }
        public string PgScenario8 { get; }
        public string PgScenario9 { get; }

        public string NeoScenario1 { get; }
        public string NeoScenario2 { get; }
        public string NeoScenario3 { get; }
        public string NeoScenario4 { get; }
        public string NeoScenario5 { get; }
        public string NeoScenario6 { get; }
        public string NeoScenario7 { get; }
        public string NeoScenario8 { get; }
        public string NeoScenario9 { get; }

        public string PgReverse7 { get; }
        public string NeoReverse7 { get; }
        
        public Dictionary<string, int> ExpectedCounts { get; } 

        public QueryRepo(string basePath, Dataset dataset) {
            var suffix = DatasetSuffix[dataset];

            string countsPath = Path.Combine(AppContext.BaseDirectory, $"scenarios/scenario_validation/expected_data_{suffix}", 
                $"expected_counts_{suffix}.json");
            
            if (File.Exists(countsPath)) {
                string json = File.ReadAllText(countsPath);
                ExpectedCounts = JsonSerializer.Deserialize<Dictionary<string, int>>(json) ?? new Dictionary<string, int>();
            } else {
                ExpectedCounts = new Dictionary<string, int>();
            }
            
            PgDropAndCreateDbScript = Path.Combine(Environment.GetEnvironmentVariable("BASE_PATH")!, "db_setup/postgresql/01_drop_and_create_database.sh");
            PgImportScript = Path.Combine(Environment.GetEnvironmentVariable("BASE_PATH")!, $"db_setup/postgresql/02_import_data_{suffix}.sh");
            PgCreateIndexesSql = Read(basePath, "db_setup/postgresql/03_create_indexes.sql");

            Neo4jDropDbScript = Path.Combine(Environment.GetEnvironmentVariable("BASE_PATH")!, "db_setup/neo4j/01_drop_database.sh");
            Neo4jImportScript = Path.Combine(Environment.GetEnvironmentVariable("BASE_PATH")!, $"db_setup/neo4j/02_import_data_{suffix}.sh");
            Neo4jCreateDbScript = Path.Combine(Environment.GetEnvironmentVariable("BASE_PATH")!, "db_setup/neo4j/03_create_database.sh");
            Neo4jCreateIndexesCypher = Read(basePath, "db_setup/neo4j/04_create_indexes.cypher");
            
            PgScenario1 = LoadScenario(basePath, "postgres_scenarios", 1, suffix, ".sql");
            PgScenario2 = LoadScenario(basePath, "postgres_scenarios", 2, suffix, ".sql");
            PgScenario3 = LoadScenario(basePath, "postgres_scenarios", 3, suffix, ".sql");
            PgScenario4 = LoadScenario(basePath, "postgres_scenarios", 4, suffix, ".sql");
            PgScenario5 = LoadScenario(basePath, "postgres_scenarios", 5, suffix, ".sql");
            PgScenario6 = LoadScenario(basePath, "postgres_scenarios", 6, suffix, ".sql");
            PgScenario7 = LoadScenario(basePath, "postgres_scenarios", 7, suffix, ".sql");
            PgScenario8 = LoadScenario(basePath, "postgres_scenarios", 8, suffix, ".sql");
            PgScenario9 = LoadScenario(basePath, "postgres_scenarios", 9, suffix, ".sql");

            NeoScenario1 = LoadScenario(basePath, "neo4j_scenarios", 1, suffix, ".cypher");
            NeoScenario2 = LoadScenario(basePath, "neo4j_scenarios", 2, suffix, ".cypher");
            NeoScenario3 = LoadScenario(basePath, "neo4j_scenarios", 3, suffix, ".cypher");
            NeoScenario4 = LoadScenario(basePath, "neo4j_scenarios", 4, suffix, ".cypher");
            NeoScenario5 = LoadScenario(basePath, "neo4j_scenarios", 5, suffix, ".cypher");
            NeoScenario6 = LoadScenario(basePath, "neo4j_scenarios", 6, suffix, ".cypher");
            NeoScenario7 = LoadScenario(basePath, "neo4j_scenarios", 7, suffix, ".cypher");
            NeoScenario8 = LoadScenario(basePath, "neo4j_scenarios", 8, suffix, ".cypher");
            NeoScenario9 = LoadScenario(basePath, "neo4j_scenarios", 9, suffix, ".cypher");

            PgReverse7 = LoadScenario(basePath, "postgres_scenarios", 7, suffix, "_reverse.sql");
            NeoReverse7 = LoadScenario(basePath, "neo4j_scenarios", 7, suffix, "_reverse.cypher");
        }

        private static string LoadScenario(string basePath, string db, short scenario, string suffix, string ext) {
            var dir = Path.Combine(AppContext.BaseDirectory, "scenarios", db, $"scenario_0{scenario}");

            string file = UniversalScenarios.Contains(scenario)
                ? $"scenario_0{scenario}{ext}"
                : $"scenario_0{scenario}_{suffix}{ext}";

            return Read(Path.Combine(dir, file));
        }

        private static string Read(string basePath, string relativePath) {
            var full = Path.Combine(AppContext.BaseDirectory, relativePath);

            if(!File.Exists(full))
                throw new FileNotFoundException($"Missing file: {full}");

            return File.ReadAllText(full);
        }

        private static string Read(string fullPath) {
            if(!File.Exists(fullPath))
                throw new FileNotFoundException($"Missing file: {fullPath}");

            return File.ReadAllText(fullPath);
        }
    }
}
