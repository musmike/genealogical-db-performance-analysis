using System.Diagnostics;

namespace benchmark_scr.monitoring {
    internal static class DiskSizeCollector {

        public static void ExportPostgres(string dataset, PostgresDriver driver) {
            driver.ExecuteNonQuery("VACUUM (ANALYZE) people;");
            driver.ExecuteNonQuery("VACUUM (ANALYZE) families;");
            driver.ExecuteNonQuery("VACUUM (ANALYZE) family_children;");
            driver.ExecuteNonQuery("ALTER TABLE people SET (autovacuum_enabled = true);");
            driver.ExecuteNonQuery("ALTER TABLE families SET (autovacuum_enabled = true);");
            driver.ExecuteNonQuery("ALTER TABLE family_children SET (autovacuum_enabled = true);");
            driver.ExecuteNonQuery("CHECKPOINT;");
            
            uint oid = driver.ExecuteScalar<uint>("SELECT oid FROM pg_database WHERE datname = 'benchmarkdb';");
            
            var psi = new ProcessStartInfo {
                FileName = "docker",
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            psi.ArgumentList.Add("exec");
            psi.ArgumentList.Add("postgres_db");
            psi.ArgumentList.Add("du");
            psi.ArgumentList.Add("-sb");
            psi.ArgumentList.Add($"/var/lib/postgresql/data/base/{oid}");

            using var process = Process.Start(psi)!;
            var output = process.StandardOutput.ReadToEnd().Trim();
            process.WaitForExit();
            
            long bytes = long.Parse(output.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries)[0]);
            Export(dataset, "postgres", bytes);
        }

        public static void ExportNeo4j(string dataset, Neo4jDriver driver) {
            driver.ExecuteWriteCypherAsync("CALL db.awaitIndexes();")
                .GetAwaiter().GetResult();
            
            var psi = new ProcessStartInfo {
                FileName = "docker",
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            psi.ArgumentList.Add("exec");
            psi.ArgumentList.Add("neo4j_db");
            psi.ArgumentList.Add("du");
            psi.ArgumentList.Add("-sb");
            psi.ArgumentList.Add("/data/databases/benchmarkdb"); 

            using var process = Process.Start(psi)!;
            var output = process.StandardOutput.ReadToEnd().Trim();
            process.WaitForExit();

            long bytes = long.Parse(output.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries)[0]);
            Export(dataset, "neo4j", bytes);
        }

        private static void Export(string dataset, string db, long bytes) {
            var path = Path.Combine(
                Configg.repoRoot, "results", dataset, "disk", $"disk_size_{db}.csv");
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            using var w = new StreamWriter(path);
            w.WriteLine("database,bytes");
            w.WriteLine($"{db},{bytes}");
        }
    }
}