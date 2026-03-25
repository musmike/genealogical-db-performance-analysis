using benchmark_scr.db;
using benchmark_scr.monitoring;
using BenchmarkDotNet.Running;
using System.Data.Common;
using System.Diagnostics;
using System.Text;

if(args.Length > 0 && args[0] == Config.slaveArg) {
    SlaveRun(args);
}
else {
    MasterRun();
}

static void MasterRun() {
    Console.WriteLine("[MASTER] Starting orchestrator...");

    for (int ds = 0; ds < 3; ds++) {
        var dataset = (Dataset)ds;

        Console.WriteLine($"[MASTER] Preparing dataset: {dataset}");

        for (int db = 0; db < 2; db++) {
            var dbType = (DbType)db;

            DBPreparer.PrepareAndBenchmark(dbType, dataset);

            Console.WriteLine($"[MASTER] Running: {dataset} / {dbType}");

            var psi = new ProcessStartInfo {
                FileName = Process.GetCurrentProcess().MainModule!.FileName,
                Arguments = $"{Config.slaveArg} {(int)dbType} {(int)dataset}",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
            };

            var slave = Process.Start(psi)!;

            // Drain output asynchronously (prevents deadlocks)
            _ = Task.Run(() => Drain(slave.StandardOutput));
            _ = Task.Run(() => Drain(slave.StandardError));

            // ================= MEMORY MONITOR =================
            var containerId = Config.ContainerId(dbType);
            //var monitor = new MemoryMonitor(containerId);

            //monitor.Start();

            var sw = Stopwatch.StartNew();

            slave.WaitForExit();

            sw.Stop();

            //monitor.Stop();

            Console.WriteLine($"[MASTER] Finished {dataset}/{dbType} in {sw.Elapsed}");

            // ================= SAVE =================
            //SampleWriter.Write(
            //    monitor.Samples,
            //    dbType,
            //    dataset);
        }
    }

    Console.WriteLine("[MASTER] All benchmarks completed.");
}



static void SlaveRun(string[] args) {
    var db = (DbType)int.Parse(args[1]);
    var ds = (Dataset)int.Parse(args[2]);

    Console.WriteLine($"[SLAVE] Config: {db} / {ds}");

    QueryStore.Load();

    DBBench.Configure(db, ds);
    var config = new CustomBenchConfig().WithArtifactsPath($"artifacts_main/{ds}_{db}");
    Console.WriteLine("[SLAVE] Running benchmarks...");

    BenchmarkRunner.Run<DBBench>(config);
}




static void Drain(StreamReader reader) {
    string? line;
    while ((line = reader.ReadLine()) != null) { }
}
