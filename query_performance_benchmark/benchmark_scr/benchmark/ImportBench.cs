using benchmark_scr.db;
using BenchmarkDotNet.Attributes;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace benchmark_scr.benchmark {
    [SimpleJob(
        warmupCount: 1,
        iterationCount: 10)]
    [Config(typeof(CustomImportConfig))]
    public class ImportBench {
        private static DbType _db;
        private static Dataset _ds;

        public static void Configure(DbType db, Dataset ds) {
            _db = db;
            _ds = ds;
        }

        [Benchmark]
        public void Import() {
            DBPreparer.RunImport(_db, _ds);
        }
    }
}
