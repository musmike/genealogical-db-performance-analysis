using benchmark_scr.db;
using BenchmarkDotNet.Attributes;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;


[MemoryDiagnoser]
public class DBBench {
    [Params(0,1,2,3,4,5,6,7,8)]
    public int queryIndex;

    private DbType _db;
    //private readonly Dataset _dataset;
    private  string[] _queries = null!;

    //private string _query => _queries[queryIndex];

    [GlobalSetup]
    public void Setup() {
        var db = (DbType)int.Parse(Environment.GetEnvironmentVariable("DB")!);
        var ds = (Dataset)int.Parse(Environment.GetEnvironmentVariable("DATASET")!);

        _db = db;
        _queries = QueryStore.GetSet(db, ds);
    }

    [Benchmark]
    public void Execute() {
        var q = _queries[queryIndex];
        if (_db == DbType.PostgreSQL)
            PostgresRunner.Execute(q);
        else
            Neo4jRunner.Execute(q);

    }


    //private static string[] ResolveQueryArray(DbType db, Dataset ds) {
    //    if (db == DbType.PostgreSQL) {
    //        return ds switch {
    //            Dataset._1k => QueryStore.psqqueries1k,
    //            Dataset._10k => QueryStore.psqqueries10k,
    //            Dataset._100k => QueryStore.psqqueries100k,
    //            _ => throw new ArgumentOutOfRangeException()
    //        };
    //    }
    //    else {
    //        return ds switch {
    //            Dataset._1k => QueryStore.n4jqueries1k,
    //            Dataset._10k => QueryStore.n4jqueries10k,
    //            Dataset._100k => QueryStore.n4jqueries100k,
    //            _ => throw new ArgumentOutOfRangeException()
    //        };
    //    }
    //}
}