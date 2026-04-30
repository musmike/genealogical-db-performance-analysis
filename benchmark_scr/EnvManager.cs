namespace benchmark_scr {
    internal static class EnvManager {

        public static void PreparePostgres() {
            Console.WriteLine("\n[EnvManager] Ensuring neo4j_db is stopped...");
            BashRunner.RunAsync("docker", "stop", "neo4j_db").GetAwaiter().GetResult();

            Console.WriteLine("[EnvManager] Ensuring postgres_db is running...");
            BashRunner.RunAsync("docker", "start", "postgres_db").GetAwaiter().GetResult();
            
            // Console.WriteLine("[EnvManager] Restarting postgres_db...");
            // BashRunner.RunAsync("docker", "restart", "postgres_db").GetAwaiter().GetResult();

            // Console.WriteLine("[EnvManager] Syncing disk buffers and dropping OS page cache...");
            // BashRunner.RunAsync("sudo", "sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches").GetAwaiter().GetResult();

            Console.WriteLine("[EnvManager] Waiting for PostgreSQL to become ready...");
            WaitForPostgres().GetAwaiter().GetResult();
            
            Thread.Sleep(2000); // Give the database some time to fully stabilize background processes
            Console.WriteLine("[EnvManager] PostgreSQL environment ready.\n");
        }

        public static void PrepareNeo4j() {
            Console.WriteLine("\n[EnvManager] Ensuring postgres_db is stopped...");
            BashRunner.RunAsync("docker", "stop", "postgres_db").GetAwaiter().GetResult();
            
            Console.WriteLine("[EnvManager] Ensuring neo4j_db is running...");
            BashRunner.RunAsync("docker", "start", "neo4j_db").GetAwaiter().GetResult();

            // Console.WriteLine("[EnvManager] Restarting neo4j_db...");
            // BashRunner.RunAsync("docker", "restart", "neo4j_db").GetAwaiter().GetResult();
            //
            // Console.WriteLine("[EnvManager] Syncing disk buffers and dropping OS page cache...");
            // BashRunner.RunAsync("sudo", "sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches").GetAwaiter().GetResult();

            Console.WriteLine("[EnvManager] Waiting for Neo4j to become ready (this may take several seconds)...");
            WaitForNeo4j().GetAwaiter().GetResult();
            
            Thread.Sleep(2000); // Give the database some time to fully stabilize background processes
            Console.WriteLine("[EnvManager] Neo4j environment ready.\n");
        }

        private static async Task WaitForPostgres() {
            while (true) {
                var code = await BashRunner.RunAsync(
                    "docker", "exec", "postgres_db", "pg_isready", "-U", "user"
                );

                if (code == 0) return;

                await Task.Delay(1000);
            }
        }

        private static async Task WaitForNeo4j() {
            while (true) {
                var code = await BashRunner.RunAsync(
                    "docker", "exec", "neo4j_db",
                    "cypher-shell", "-u", "neo4j", "-p", "password", "RETURN 1;"
                );

                if (code == 0) return;

                await Task.Delay(2000);
            }
        }
    }
}