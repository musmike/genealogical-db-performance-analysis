using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace benchmark_scr.monitoring {
    internal class MemoryMonitor {
        private readonly string _path;
        private readonly List<(long ts, long mem)> _samples = new(20000);
        private bool _running;
        private Thread? _thread;

        public IReadOnlyList<(long ts, long mem)> Samples => _samples;

        public MemoryMonitor(string cid) {
            _path = ResolvePath(cid);
        }

        private static string ResolvePath(string id) {
            Console.WriteLine($"Resolving memory handler for id: docker-{id}");
            string v2 = $"/sys/fs/cgroup/system.slice/docker-{id}/memory.current";
            if(File.Exists(v2)) return v2;

            return $"/sys/fs/cgroup/memory/docker/{id}/memory.usage_in_bytes";
        }

        public void Start() {
            _running = true;
            _thread = new Thread(() => {
                var buffer = new byte[32];
                using var fs = new FileStream(_path, FileMode.Open, FileAccess.Read, FileShare.Read);
                var sw = Stopwatch.StartNew();
                while (_running) {
                    fs.Position = 0;
                    int len = fs.Read(buffer, 0, buffer.Length);
                    long value = 0;
                    for(int i = 0; i < len; i++) {
                        byte b = buffer[i];
                        if (b < '0' || b > '9') break;
                        value = value * 10 + (b- '0');
                    }
                    _samples.Add((sw.ElapsedTicks, value));
                    Thread.Sleep(Config.sampleHz);
                }
            });
            _thread.IsBackground = true;
            _thread.Start();
        }
        public void Stop() {
            _running = false;
            _thread?.Join();
        }
    }
}
