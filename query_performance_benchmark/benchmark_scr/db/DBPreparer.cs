using benchmark_scr.benchmark;
using BenchmarkDotNet.Running;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;

namespace benchmark_scr.db {
    internal static class DBPreparer {
        

        public static void PrepareAndBenchmark(DbType db, Dataset ds) {
            Console.WriteLine($"[PREPARER] Running import benchmark: {db}/{ds}");
            //ImportBench.Configure(db, ds);
            //var config = new CustomImportConfig()
            //    .WithArtifactsPath($"artifacts/{db}_{ds}");
            //WaitForNeo4j();
            //BenchmarkRunner.Run<ImportBench>(config);

            WaitForNeo4j();
            RunImport(db, ds);
            WaitForNeo4j();
            RunIndexScripts(db);

        }


        public static void RunImport(DbType db, Dataset ds) {
            if (db == DbType.PostgreSQL) {
                Console.WriteLine("Importing for PostgreSQL!");
                string file = ds switch {
                    Dataset._1k => "02_data_import_1k.sql",
                    Dataset._10k => "02_data_import_10k.sql",
                    Dataset._100k => "02_data_import_100k.sql",
                    _ => throw new ArgumentOutOfRangeException()
                };
                RunShell("bash", $"-c \"cat db_setup/postgresql/01_creating_tables.sql | docker exec -i postgres_db psql -U user -d benchmark_db\"");
                RunShell("bash", $"-c \"cat db_setup/postgresql/{file} | docker exec -i postgres_db psql -U user -d benchmark_db\"");

                //RunShell("docker", $"exec postgres_db psql -U user -d benchmark_db -f db_setup/postgresql/01_creating_tables.sql");
                //RunShell("docker", $"exec postgres_db psql -U user -d benchmark_db -f db_setup/postgresql/{file}");
            }
            else {
                Console.WriteLine("Importing for Neo4j!");
                string file = ds switch {
                    Dataset._1k => "01_data_import_1k.sh",
                    Dataset._10k => "01_data_import_10k.sh",
                    Dataset._100k => "01_data_import_100k.sh",
                    _ => throw new ArgumentOutOfRangeException()
                };
                RunShell("bash", $"scripts/neo4j/{file}");
            }
        }

        private static void RunIndexScripts(DbType db) {
            if (db == DbType.PostgreSQL) {
                RunShell("bash", $"-c \"cat db_setup/postgresq/l03_creating_indexes.sql | docker exec -i postgres_db psql -U user -d benchmark_db\"");
                //RunShell("docker", "exec postgres_db psql -U user -d benchmark_db -f db_setup/postgresql/03_creating_indexes.sql");
            }
            else {
                WaitForNeo4j();
                Neo4jRunner.ResetConnection();
                RunShell("bash", "-c \"cat db_setup/neo4j/02_creating_indexes.cypher | docker exec -i neo4j_db cypher-shell -u neo4j -p password\"");
            }
        }

        private static void RunShell(string file, string args) {
            var psi = new ProcessStartInfo {
                FileName = file,
                Arguments = args,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false
            };

            using var p = Process.Start(psi)!;
            string stdout = p.StandardOutput.ReadToEnd();
            string stderr = p.StandardError.ReadToEnd();
            p.WaitForExit();

            if (p.ExitCode != 0)
                throw new Exception(
            $"Command failed:\n{file} {args}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}");
        }
        static void WaitForNeo4j() {
            var start = DateTime.UtcNow;

            while ((DateTime.UtcNow - start).TotalSeconds < 60) {
                try {
                    using var client = new TcpClient("localhost", 7687);
                    return;
                }
                catch {
                    Thread.Sleep(500);
                }
            }

            throw new Exception("Neo4j did not start in time");
        }
    }
}
