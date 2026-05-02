using Neo4j.Driver;
using System.Diagnostics;

namespace benchmark_scr.monitoring {

internal class MemoryMonitor : IDisposable {
    private readonly string _postgresPath;
    private readonly string _n4jPath;

    private readonly long[] _pgBuffer;
    private readonly long[] _n4jBuffer;
    private readonly long[] _neo4jHeapBuffer;
    private readonly long[] _timestamps;
    private readonly int[] _iterationBuffer;

    private int _index;
    private readonly object _lock = new();

    private int _currentIteration;

    private Timer? _timer;
    private Timer? _jmxTimer;

    private IAsyncSession? _jmxSession;
    private IDriver? _jmxDriver;
    private long _neo4jHeapCache;

    private readonly string _dataset;
    private readonly string _benchmarkName;

    public MemoryMonitor(string dataset, string benchmarkName) {
        _dataset = dataset;
        _benchmarkName = benchmarkName;

        _postgresPath = GetCgroupPath("postgres_db");
        _n4jPath = GetCgroupPath("neo4j_db");

        _pgBuffer = new long[200_000];
        _n4jBuffer = new long[200_000];
        _neo4jHeapBuffer = new long[200_000];
        _timestamps = new long[200_000];
        _iterationBuffer = new int[200_000];
    }

    public void NextIteration() {
        Interlocked.Increment(ref _currentIteration);
    }

    public void Start() {
        _jmxDriver = GraphDatabase.Driver(
            "bolt://localhost:7687",
            AuthTokens.Basic("neo4j", "password")
        );
        _jmxSession = _jmxDriver.AsyncSession(o => o.WithDatabase("benchmarkdb"));

        _timer = new Timer(_ => Sample(), null, 0, 30);
        _jmxTimer = new Timer(async _ => await SampleJmxAsync(), null, 0, 500);
    }

    private void Sample() {
        lock (_lock) {
            if (_index >= _pgBuffer.Length) return;

            _pgBuffer[_index] = ReadMem(_postgresPath);
            _n4jBuffer[_index] = ReadMem(_n4jPath);

            _neo4jHeapBuffer[_index] = Interlocked.Read(ref _neo4jHeapCache);

            _timestamps[_index] = DateTime.UtcNow.Ticks;
            _iterationBuffer[_index] = _currentIteration;

            _index++;
        }
    }

    private async Task<long> ReadNeo4jHeapAsync() {
        var result = await _jmxSession!.RunAsync(@"
            CALL dbms.queryJmx('java.lang:type=Memory')
            YIELD attributes
            RETURN attributes['HeapMemoryUsage'].value.properties.used AS used
        ");
        var record = await result.SingleAsync();
        return record["used"].As<long>();
    }

    private async Task SampleJmxAsync() {
        try {
            var value = await ReadNeo4jHeapAsync();
            Interlocked.Exchange(ref _neo4jHeapCache, value);
        }
        catch {
            // ignore sampling errors
        }
    }

    private static long ReadMem(string cgroup) {
        var file = Path.Combine(cgroup, "memory.current");

        if (!File.Exists(file))
            return 0;

        return long.Parse(File.ReadAllText(file));
    }

    private static string GetContainerId(string containerName) {
        var psi = new ProcessStartInfo {
            FileName = "bash",
            Arguments = $"-c \"docker inspect -f '{{{{.Id}}}}' {containerName}\"",
            RedirectStandardOutput = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        using var process = Process.Start(psi)!;
        var output = process.StandardOutput.ReadToEnd().Trim();
        process.WaitForExit();

        return output;
    }

    private static string GetCgroupPath(string containerName) {
        var id = GetContainerId(containerName);
        return $"/sys/fs/cgroup/system.slice/docker-{id}.scope";
    }

    public static async Task StabilizeAsync() {
        await Task.Delay(1000);
    }

    public void Export() {
        var path = Path.Combine(
            Configg.repoRoot,
            "results",
            _dataset,
            "memory",
            $"memory_{_benchmarkName}.csv"
        );

        Directory.CreateDirectory(Path.GetDirectoryName(path)!);

        using var w = new StreamWriter(path);

        w.WriteLine("iteration,timestamp,postgres_bytes,neo4j_bytes,neo4j_heap");

        for (int i = 0; i < _index; i++) {
            w.WriteLine(
                $"{_iterationBuffer[i]}," +
                $"{_timestamps[i]}," +
                $"{_pgBuffer[i]}," +
                $"{_n4jBuffer[i]}," +
                $"{_neo4jHeapBuffer[i]}"
            );
        }
    }

    public void Dispose() {
        _timer?.Dispose();
        _jmxTimer?.Dispose();
        _jmxSession?.CloseAsync().GetAwaiter().GetResult();
        _jmxDriver?.DisposeAsync().GetAwaiter().GetResult();
    }
}

}