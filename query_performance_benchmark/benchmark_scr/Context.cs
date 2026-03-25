using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

public sealed class Context {
    public DbType Db { get; init; }
    public Dataset Dataset { get; init; }
    public string[] Queries { get; init; } = null!;
}

public static class BenchState {
    public static Context Current = null!;
}