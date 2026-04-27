using Neo4j.Driver;
using Npgsql;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

//static class Neo4jRunner {
//        private static readonly IDriver driver;
//        static Neo4jRunner() {
//            driver = GraphDatabase.Driver(
//                "bolt://localhost:7687",
//            AuthTokens.Basic("neo4j", "password"));
//        }
//}

public class Neo4jDriver : IAsyncDisposable {
    private readonly IDriver _driver;

    public Neo4jDriver(string uri, string user, string password) {
        _driver = GraphDatabase.Driver(uri, AuthTokens.Basic(user, password));
    }

    public static DateOnly? ToDateOnly(object? val) {
        if (val is LocalDate ld)
            return new DateOnly(ld.Year, ld.Month, ld.Day);
        return null;
    }
    
    private static List<string> SplitCypherStatements(string cypher) {
        var lines = cypher
            .Split('\n')
            .Select(l => l.Trim())
            .Where(l => !string.IsNullOrWhiteSpace(l))
            .Where(l => !l.StartsWith("//"));

        var joined = string.Join("\n", lines);

        return joined
            .Split(';', StringSplitOptions.RemoveEmptyEntries)
            .Select(s => s.Trim())
            .Where(s => !string.IsNullOrWhiteSpace(s))
            .ToList();
    }

    public async ValueTask DisposeAsync() {
        if(_driver != null)
            await _driver.DisposeAsync();
    }

    // --- IMPORT ---
    public async Task<IResultSummary> ExecuteWriteAsync(string cypher) {
        await using var session = _driver.AsyncSession(o => o.WithDatabase("benchmarkdb"));

        return await session.ExecuteWriteAsync(async tx => {
            var cursor = await tx.RunAsync(cypher);
            return await cursor.ConsumeAsync();
        });
    }

    // --- QUERY ---
    public async Task<(List<IRecord> Records, int RowCount)> ExecuteReadWithCountAsync(string cypher) {
        await using var session = _driver.AsyncSession(o => o.WithDatabase("benchmarkdb"));

        return await session.ExecuteReadAsync(async tx => {
            var cursor = await tx.RunAsync(cypher);

            var results = new List<IRecord>();
            int count = 0;

            while(await cursor.FetchAsync()) {
                results.Add(cursor.Current);
                count++;
            }

            return (results, count);
        });
    }

    public async Task<int> ExecuteReadCountOnlyAsync(string cypher) {
        await using var session = _driver.AsyncSession(o => o.WithDatabase("benchmarkdb"));

        return await session.ExecuteReadAsync(async tx => {
            var cursor = await tx.RunAsync(cypher);

            int count = 0;

            while(await cursor.FetchAsync()) {
                count++;
            }

            return count;
        });
    }

    public async Task<(IResultSummary Summary, int RowsReturned)> ExecuteWriteWithStatsAsync(string cypher) {
        await using var session = _driver.AsyncSession(o => o.WithDatabase("benchmarkdb"));

        return await session.ExecuteWriteAsync(async tx => {
            var cursor = await tx.RunAsync(cypher);

            int rows = 0;

            while(await cursor.FetchAsync())
                rows++;

            var summary = await cursor.ConsumeAsync();

            return (summary, rows);
        });
    }
    
    public async Task<List<IRecord>> ExecuteReadScriptAsync(string cypher) {
        var statements = SplitCypherStatements(cypher);

        await using var session = _driver.AsyncSession(o => o.WithDatabase("benchmarkdb"));

        return await session.ExecuteReadAsync(async tx =>
        {
            var results = new List<IRecord>();

            foreach(var stmt in statements) {
                var cursor = await tx.RunAsync(stmt);

                while(await cursor.FetchAsync())
                    results.Add(cursor.Current);
            }

            return results;
        });
    }
    
    public async Task<int> ExecuteReadScriptCountAsync(string cypher) {
        var statements = SplitCypherStatements(cypher);

        await using var session = _driver.AsyncSession(o => o.WithDatabase("benchmarkdb"));

        return await session.ExecuteReadAsync(async tx =>
        {
            int totalCount = 0;

            foreach(var stmt in statements) {
                var cursor = await tx.RunAsync(stmt);

                while(await cursor.FetchAsync())
                    totalCount++;
            }

            return totalCount;
        });
    }
    
    public async Task<List<IResultSummary>> ExecuteWriteScriptAsync(string cypher) {
        var statements = SplitCypherStatements(cypher);

        await using var session = _driver.AsyncSession(o => o.WithDatabase("benchmarkdb"));

        return await session.ExecuteWriteAsync(async tx =>
        {
            var summaries = new List<IResultSummary>();

            foreach(var stmt in statements) {
                var cursor = await tx.RunAsync(stmt);
                summaries.Add(await cursor.ConsumeAsync());
            }

            return summaries;
        });
    }
    
    public async Task<int> ExecuteReadConsumingAsync<T>(string cypher, T scratch, Action<IRecord, T> map) {
    
        var statements = SplitCypherStatements(cypher);
        await using var session = _driver.AsyncSession(o => o.WithDatabase("benchmarkdb"));

        return await session.ExecuteReadAsync(async tx => {
            int totalCount = 0;
            
            foreach (var stmt in statements) {
                var cursor = await tx.RunAsync(stmt);
                
                while (await cursor.FetchAsync()) {
                    map(cursor.Current, scratch);
                    totalCount++;
                }
            }
            
            return totalCount;
        });
    }
    
    public async Task<int> ExecuteWriteScriptCountAsync(string cypher) {
        var statements = SplitCypherStatements(cypher);
        await using var session = _driver.AsyncSession(o => o.WithDatabase("benchmarkdb"));

        return await session.ExecuteWriteAsync(async tx => {
            int totalAffected = 0;
            foreach (var stmt in statements) {
                var cursor = await tx.RunAsync(stmt);
                var summary = await cursor.ConsumeAsync();
                totalAffected += summary.Counters.NodesCreated
                                 + summary.Counters.NodesDeleted
                                 + summary.Counters.RelationshipsCreated
                                 + summary.Counters.RelationshipsDeleted
                                 + summary.Counters.PropertiesSet;
            }
            return totalAffected;
        });
    }
}