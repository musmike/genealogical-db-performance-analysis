using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

static class SampleWriter {
    public static void Write(IReadOnlyList<(long ts, long mem)> samples,
        DbType db,
        Dataset ds) {
        string file = $"{db}_{ds}_ram.csv";
        using var sw = new StreamWriter(file, false, Encoding.UTF8);
        sw.WriteLine("timestamp_ticks,memory_bytes");
        for(int i = 0; i < samples.Count; i++) {
            sw.Write(samples[i].ts);
            sw.Write(',');
            sw.Write(samples[i].mem);
            sw.WriteLine();
        }
    }
}