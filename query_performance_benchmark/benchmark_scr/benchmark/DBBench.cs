using benchmark_scr.db;
using BenchmarkDotNet.Attributes;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

[Config(typeof(CustomBenchConfig))]
[MemoryDiagnoser]
public class DBBench {
    [Params(0,1,2,3,4,5,6,7,8)]
    public int queryIndex;

    private static DbType _db;
    private static Dataset _dataset;
    private static string[] _queries = null!;

    private string _query => _queries[queryIndex];

    public static void Configure(DbType db, Dataset ds) {
        _db = db;
        _dataset = ds;
        _queries = ResolveQueryArray(db, ds);

    }

    [Benchmark]
    public void Execute() {
        if (_db == DbType.PostgreSQL)
            PostgresRunner.Execute(_query);
        else
            Neo4jRunner.Execute(_query);
    }


    private static string[] ResolveQueryArray(DbType db, Dataset ds) {
        if (db == DbType.PostgreSQL) {
            return ds switch {
                Dataset._1k => QueryStore.psqqueries1k,
                Dataset._10k => QueryStore.psqqueries10k,
                Dataset._100k => QueryStore.psqqueries100k,
                _ => throw new ArgumentOutOfRangeException()
            };
        }
        else {
            return ds switch {
                Dataset._1k => QueryStore.n4jqueries1k,
                Dataset._10k => QueryStore.n4jqueries10k,
                Dataset._100k => QueryStore.n4jqueries100k,
                _ => throw new ArgumentOutOfRangeException()
            };
        }
    }
}