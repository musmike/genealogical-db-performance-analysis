using System.Diagnostics;
using Neo4j.Driver;

namespace benchmark_scr.monitoring {
    internal enum BenchmarkPhase {
        GlobalSetup = 0,
        IterationSetup = 1,
        Measurement = 2,
        IterationCleanup = 3,
        GlobalCleanup = 4
    }
    
    internal class MemoryMonitor : IDisposable {
        private struct HeapSample {
            public long Value;
            public long Timestamp;
            public int Iteration;
            public int Phase;
        }

        private readonly string _postgresPath;
        private readonly string _n4jPath;
        
        private readonly long[] _pgBuffer = new long[200_000];
        private readonly long[] _n4jBuffer = new long[200_000];
        private readonly long[] _timestamps = new long[200_000];
        private readonly int[] _iterationBuffer = new int[200_000];
        private readonly int[] _phaseBuffer = new int[200_000];
        private int _index;
        private readonly object _lock = new();
        
        private readonly HeapSample[] _heapSamples = new HeapSample[1000];
        private int _heapIndex;

        private int _currentIteration;
        private int _currentPhase;
        private Timer? _timer;
        private IDriver _neo4jDriver = null!;
        
        private readonly bool _isNeo4j;
        private readonly string _dataset;
        private readonly string _benchmarkName;
        
        private readonly byte[] _pgByteBuffer = new byte[64];
        private readonly byte[] _n4jByteBuffer = new byte[64];
        private FileStream? _pgMemStream;
        private FileStream? _n4jMemStream;

        public MemoryMonitor(string dataset, string benchmarkName) {
            _dataset = dataset;
            _benchmarkName = benchmarkName;
            _isNeo4j = benchmarkName.StartsWith("N4");

            _postgresPath = GetCgroupPath("postgres_db");
            _n4jPath = GetCgroupPath("neo4j_db");
        }

        public void NextIteration() {
            Interlocked.Increment(ref _currentIteration);
        }
        
        public void SetPhase(BenchmarkPhase phase) {
            Volatile.Write(ref _currentPhase, (int)phase); 
        }

        public void Start() {
            _pgMemStream = OpenCgroupFile(_postgresPath);
            _n4jMemStream = OpenCgroupFile(_n4jPath);
            
            if (_isNeo4j) {
                _neo4jDriver = GraphDatabase.Driver(
                    "bolt://localhost:7687", AuthTokens.Basic("neo4j", "password")
                );
            }

            _timer = new Timer(_ => Sample(), null, 0, 30);
        }

        private FileStream? OpenCgroupFile(string cgroupPath) {
            var file = Path.Combine(cgroupPath, "memory.current");
            if (File.Exists(file)) {
                return new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
            }
            return null;
        }

        private void Sample() {
            lock (_lock) {
                if (_index >= _pgBuffer.Length) return;

                _pgBuffer[_index] = ReadMem(_pgMemStream, _pgByteBuffer);
                _n4jBuffer[_index] = ReadMem(_n4jMemStream, _n4jByteBuffer);
                _timestamps[_index] = DateTime.UtcNow.Ticks;
                _iterationBuffer[_index] = Volatile.Read(ref _currentIteration);
                _phaseBuffer[_index] = Volatile.Read(ref _currentPhase);

                _index++;
            }
        }
        
        private async Task<long> ReadNeo4jHeapAsync() {
            await using var session = _neo4jDriver.AsyncSession(o => o.WithDatabase("benchmarkdb"));
            var result = await session.RunAsync(@"
            CALL dbms.queryJmx('java.lang:type=Memory')
            YIELD attributes
            RETURN attributes['HeapMemoryUsage'].value.properties.used AS used
        ");
            var record = await result.SingleAsync();
            return record["used"].As<long>();
        }
        
        public void RecordNeo4jHeap() {
            if (!_isNeo4j || _neo4jDriver == null) return;
            try {
                long heap = ReadNeo4jHeapAsync().GetAwaiter().GetResult();
                long timestamp = DateTime.UtcNow.Ticks;
                int iteration = Volatile.Read(ref _currentIteration);
                int phase = Volatile.Read(ref _currentPhase);
                
                int idx = Interlocked.Increment(ref _heapIndex) - 1;
                
                if (idx >= _heapSamples.Length) return;
                
                _heapSamples[idx] = new HeapSample {
                    Value = heap,
                    Timestamp = timestamp,
                    Iteration = iteration,
                    Phase = phase
                };
            }
            catch { }
        }
        
        private static long ReadMem(FileStream? fs, byte[] buffer) {
            if (fs == null) return 0;
            try {
                fs.Position = 0; 
                int bytesRead = fs.Read(buffer, 0, buffer.Length);
                if (System.Buffers.Text.Utf8Parser.TryParse(buffer.AsSpan(0, bytesRead), out long value, out _)) {
                    return value;
                }
            }
            catch {}
            return 0;
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

        public static void Stabilize() {
            Thread.Sleep(2000);
        }

        public void Export() {
            var dirPath = Path.Combine(Configg.repoRoot, "results", _dataset, "memory");
            Directory.CreateDirectory(dirPath);
            
            var memPath = Path.Combine(dirPath, $"memory_{_benchmarkName}.csv");
            using (var w = new StreamWriter(memPath)) {
                w.WriteLine("iteration,timestamp,phase,postgres_bytes,neo4j_bytes");
                for (int i = 0; i < _index; i++) {
                    string phaseName = ((BenchmarkPhase)_phaseBuffer[i]).ToString();
                    w.WriteLine($"{_iterationBuffer[i]},{_timestamps[i]},{phaseName},{_pgBuffer[i]},{_n4jBuffer[i]}");
                }
            }
            
            if (_isNeo4j && _heapIndex > 0) {
                var heapPath = Path.Combine(dirPath, $"heap_{_benchmarkName}.csv");
                using (var w = new StreamWriter(heapPath)) {
                    w.WriteLine("iteration,timestamp,phase,neo4j_heap_bytes");
                    
                    int count = Math.Min(_heapIndex, _heapSamples.Length);
                    for (int i = 0; i < count; i++) {
                        var s = _heapSamples[i];
                        string phaseName = ((BenchmarkPhase)s.Phase).ToString();
                        w.WriteLine($"{s.Iteration},{s.Timestamp},{phaseName},{s.Value}");
                    }
                }
            }
        }

        public void Dispose() {
            _timer?.Dispose();
            _pgMemStream?.Dispose();
            _n4jMemStream?.Dispose();
            if (_isNeo4j) _neo4jDriver.Dispose();
        }
    }
}