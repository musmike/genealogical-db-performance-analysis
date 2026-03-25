using BenchmarkDotNet.Configs;
using BenchmarkDotNet.Jobs;
using BenchmarkDotNet.Exporters;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using BenchmarkDotNet.Exporters.Csv;

static class Config {
    public const int sampleHz = 50;
    public const string slaveArg = "--slave";
    public const string postgresqlContainerName = "postgres_db";
    public const string n4jContainerName = "neo4j_db";
    public static readonly string postgresqlContainerId = GetContainerId(postgresqlContainerName);
    public static readonly string n4jContainerId = GetContainerId(n4jContainerName);
    public static string ContainerId(DbType db) => db == DbType.PostgreSQL ? postgresqlContainerId : n4jContainerId;

    static string GetContainerId(string name) {
        var psi = new ProcessStartInfo {
            FileName = "docker",
            Arguments = $"inspect -f \"{{{{.Id}}}}\" {name}";
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false
        };

        using var proc = Process.Start(psi)!;

        string output = proc.StandardOutput.ReadToEnd();
        proc.WaitForExit();

        if(proc.ExitCode != 0 || string.IsNullOrWhiteSpace(output))
            throw new Exception($"Failed to resolve container ID for {name}");

        return output.Trim();
    }
}

public enum DbType :byte {
    PostgreSQL = 0,
    Neo4j = 1
}

public enum Dataset:byte {
    _1k = 0,
    _10k = 1,
    _100k = 2
}

public enum QueryId:byte {
    Q1 = 0,
    Q2,
    Q3,
    Q4,
    Q5,
    Q6,
    Q7,
    Q8,
    Q9
}

public class CustomBenchConfig: ManualConfig {
    public CustomBenchConfig() {
        AddJob(
            Job.Default.WithWarmupCount(5)
            .WithIterationCount(20)
            );
        Options = ConfigOptions.DisableOptimizationsValidator;

        AddExporter(CsvExporter.Default);
    }
}

public class CustomImportConfig : ManualConfig {
    public CustomImportConfig() {
        AddJob(
            Job.Default.WithWarmupCount(1)
            .WithIterationCount(10));
        Options = ConfigOptions.DisableOptimizationsValidator;
        AddExporter(CsvExporter.Default);
    }
}