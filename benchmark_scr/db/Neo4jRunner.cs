using Neo4j.Driver;

public class Neo4jDriver : IAsyncDisposable {
    private readonly IDriver _driver;

    public Neo4jDriver(string uri, string user, string password) {
        _driver = GraphDatabase.Driver(uri, AuthTokens.Basic(user, password));
    }
    
    public static List<string> SplitCypherStatements(string cypher) {
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
        if (_driver != null)
            await _driver.DisposeAsync();
    }
    
    public async Task<int> ExecuteReadStatementsConsumingAsync<T>(List<string> statements, T scratch, Action<IRecord, T> map) {
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
    
    public async Task<int> ExecuteWriteStatementsAsync(List<string> statements) {
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
    
    public async Task<int> ExecuteWriteCypherAsync(string cypher) {
        var statements = SplitCypherStatements(cypher);
        return await ExecuteWriteStatementsAsync(statements);
    }
    
    public async Task<int> ExecuteReadCypherConsumingAsync<T>(string cypher, T scratch, Action<IRecord, T> map) {
        var statements = SplitCypherStatements(cypher);
        return await ExecuteReadStatementsConsumingAsync(statements, scratch, map);
    }
}