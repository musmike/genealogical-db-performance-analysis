using System.Diagnostics;

namespace benchmark_scr.monitoring {
    internal class MemoryMonitor : IDisposable {
        private readonly string _postgresPath;
        private readonly string _n4jPath;

        private readonly long[] _pgBuffer;
        private readonly long[] _n4jBuffer;
        private readonly long[] _timestamps;
        private readonly int[] _iterationBuffer;

        private int _index;
        private readonly Lock _lock = new();
        private int _currentIteration;

        private Timer? _timer;

        private readonly string _dataset;
        private readonly string _benchmarkName;
        private readonly string _basePath;

        public MemoryMonitor(string dataset, string benchmarkName) {
            _dataset = dataset;
            _benchmarkName = benchmarkName;

            _basePath = Environment.GetEnvironmentVariable("BASE_PATH")
                ?? throw new Exception("BASE_PATH not set");

            _postgresPath = GetCgroupPath("postgres_db");
            _n4jPath = GetCgroupPath("neo4j_db");

            _pgBuffer = new long[200_000];
            _n4jBuffer = new long[200_000];
            _timestamps = new long[200_000];
            _iterationBuffer = new int[200_000];

            _index = 0;
            _currentIteration = 0;
        }

        public void NextIteration() {
            Interlocked.Increment(ref _currentIteration);
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

        public void Start() {
            _timer = new Timer(_ => Sample(), null, 0, 30);
        }

        private void Sample() {
            lock (_lock) {
                if (_index >= _pgBuffer.Length) return;
                _pgBuffer[_index] = ReadMem(_postgresPath);
                _n4jBuffer[_index] = ReadMem(_n4jPath);
                _timestamps[_index] = DateTime.UtcNow.Ticks;
                _iterationBuffer[_index] = _currentIteration;
                _index++;
            }
        }

        private static long ReadMem(string cgroup) {
            var file = Path.Combine(cgroup, "memory.current");

            if(!File.Exists(file))
                return 0;

            return long.Parse(File.ReadAllText(file));
        }

        public static async Task StabilizeAsync() {
            await Task.Delay(2000);
        }

        public void Export() {
            var path = Path.Combine(
                Configg.repoRoot,
                "results",
                _dataset,
                "memory",
                $"memory_{_benchmarkName}.csv");

            Directory.CreateDirectory(Path.GetDirectoryName(path)!);

            using var w = new StreamWriter(path);

            w.WriteLine("iteration,timestamp,postgres_bytes,neo4j_bytes");

            for(int i = 0; i < _index; i++) {
                w.WriteLine($"{_iterationBuffer[i]},{_timestamps[i]},{_pgBuffer[i]},{_n4jBuffer[i]}");
            }
        }

        public void Dispose() {
            _timer?.Dispose();
        }
    }
}
