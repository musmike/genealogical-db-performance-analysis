using Neo4j.Driver;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

static class Neo4jRunner {
    private static IDriver? _driver;
    private static readonly object _lock = new();

    private static IDriver Driver {
        get {
            if (_driver == null)
                CreateDriver();

            return _driver!;
        }
    }

    private static void CreateDriver() {
        _driver = GraphDatabase.Driver(
            "bolt://localhost:7687",
            AuthTokens.Basic("neo4j", "password"));
    }

    public static void ResetConnection() {
        lock (_lock) {
            try {
                _driver?.Dispose();
            }
            catch { }

            _driver = null;
        }
    }
    public static async Task ExecuteAsync(string query) {
        await using var session = Driver.AsyncSession();
        var cursor = await session.RunAsync(query);
        while(await cursor.FetchAsync()) { }
    }
    public static void Execute(string cypher) {
        ExecuteAsync(cypher).GetAwaiter().GetResult();
    }
}
