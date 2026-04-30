using benchmark_scr.benchmark.queries;
using BenchmarkDotNet.Configs;
using BenchmarkDotNet.Diagnosers;
using BenchmarkDotNet.Exporters.Csv;
using BenchmarkDotNet.Jobs;
using BenchmarkDotNet.Loggers;
using BenchmarkDotNet.Running;


var datasetArg = args.FirstOrDefault();

var dataset = datasetArg switch {
    "1k" => Dataset.small,
    "10k" => Dataset.medium,
    "100k" => Dataset.large,
    _ => throw new ArgumentException("Invalid dataset")
};

Environment.SetEnvironmentVariable("DATASET", dataset.ToString());
Environment.SetEnvironmentVariable("BASE_PATH", AppContext.BaseDirectory);

Console.WriteLine("Loading queries...");

BenchmarkRunner.Run<PsImport>(PostgresImportConfig(dataset));
Console.WriteLine("+\n+\n+\n+\n+\n+\n+\n+\n+\n");
BenchmarkRunner.Run<Ps01>(PostgresConfig(dataset));
BenchmarkRunner.Run<Ps02>(PostgresConfig(dataset));
BenchmarkRunner.Run<Ps03>(PostgresConfig(dataset));
BenchmarkRunner.Run<Ps04>(PostgresConfig(dataset));
BenchmarkRunner.Run<Ps05>(PostgresConfig(dataset));
BenchmarkRunner.Run<Ps06>(PostgresConfig(dataset));
BenchmarkRunner.Run<Ps07>(PostgresConfig(dataset));
BenchmarkRunner.Run<Ps08>(PostgresConfig(dataset));
BenchmarkRunner.Run<Ps09>(PostgresConfig(dataset));
Console.WriteLine("+\n+\n+\n+\n+\n+\n+\n+\n+\n");
BenchmarkRunner.Run<N4Import>(Neo4jImportConfig(dataset));
Console.WriteLine("+\n+\n+\n+\n+\n+\n+\n+\n+\n");
BenchmarkRunner.Run<N401>(Neo4jConfig(dataset));
BenchmarkRunner.Run<N402>(Neo4jConfig(dataset));
BenchmarkRunner.Run<N403>(Neo4jConfig(dataset));
BenchmarkRunner.Run<N404>(Neo4jConfig(dataset));
BenchmarkRunner.Run<N405>(Neo4jConfig(dataset));
BenchmarkRunner.Run<N406>(Neo4jConfig(dataset));
BenchmarkRunner.Run<N407>(Neo4jConfig(dataset));
BenchmarkRunner.Run<N408>(Neo4jConfig(dataset));
BenchmarkRunner.Run<N409>(Neo4jConfig(dataset));



static IConfig PostgresConfig(Dataset dataset) {
    return DefaultConfig.Instance
        .AddJob(Job.Default
            .WithId($"pg-{dataset}")
            .WithWarmupCount(5)
            .WithIterationCount(20))
        .AddLogger(ConsoleLogger.Default)
        .AddDiagnoser(MemoryDiagnoser.Default)
        .AddExporter(CsvMeasurementsExporter.Default)
        .WithOptions(ConfigOptions.Default)
        .WithArtifactsPath(Path.Combine(Configg.repoRoot, "results", dataset.ToString(), "postgres"));
}

static IConfig Neo4jConfig(Dataset dataset) {
    return DefaultConfig.Instance
        .AddDiagnoser(MemoryDiagnoser.Default)
        .AddJob(Job.Default
            .WithId($"neo4j-{dataset}")
            .WithWarmupCount(5)
            .WithIterationCount(20))
        .AddExporter(CsvMeasurementsExporter.Default)
        .WithArtifactsPath(Path.Combine(Configg.repoRoot, "results", dataset.ToString(), "neo4j")) 
        .AddLogger(ConsoleLogger.Default);
}

static IConfig PostgresImportConfig(Dataset dataset) {
    return DefaultConfig.Instance
        .AddJob(Job.Default
            .WithId($"pg-{dataset}-import")
            .WithWarmupCount(2).
            WithIterationCount(10))
        .AddLogger(ConsoleLogger.Default)
        .AddDiagnoser(MemoryDiagnoser.Default)
        .AddExporter(CsvMeasurementsExporter.Default)
        .WithOptions(ConfigOptions.Default)
        .WithArtifactsPath(Path.Combine(Configg.repoRoot, "results", dataset.ToString(), "postgres"));
}

static IConfig Neo4jImportConfig(Dataset dataset) {
    return DefaultConfig.Instance
        .AddDiagnoser(MemoryDiagnoser.Default)
        .AddJob(Job.Default
            .WithId($"neo4j-{dataset}-import")
            .WithWarmupCount(2)
            .WithIterationCount(10))
        .AddExporter(CsvMeasurementsExporter.Default)
        .WithArtifactsPath(Path.Combine(Configg.repoRoot, "results", dataset.ToString(), "neo4j")) 
        .AddLogger(ConsoleLogger.Default);
}


enum Dataset {
    small,
    medium,
    large
}


public static class Configg {
    public static string basePath = AppContext.BaseDirectory;
    public static string repoRoot = Environment.GetEnvironmentVariable("REPO_ROOT") ?? Directory.GetCurrentDirectory(); 
}

