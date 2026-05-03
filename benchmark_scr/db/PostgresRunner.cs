using Npgsql;

public class PostgresDriver : IDisposable {
    private readonly string _connectionString;
    private NpgsqlConnection _connection = null!;

    public PostgresDriver(string connectionString) {
        _connectionString = connectionString;
    }

    public void Open() {
        _connection = new NpgsqlConnection(_connectionString);
        _connection.Open();
    }

    public void Close() {
        _connection?.Close();
    }

    public void Dispose() => Close();
    
    
    public void ExecuteNonQuery(string sql) {
        using var cmd = new NpgsqlCommand(sql, _connection);
        cmd.ExecuteNonQuery();
    }
    
    public T ExecuteScalar<T>(string sql) {
        using var cmd = new NpgsqlCommand(sql, _connection);
        return (T)cmd.ExecuteScalar()!;
    }
    
    public async Task<int> ExecuteConsumingAsync<T>(string sql, T scratch, Action<NpgsqlDataReader, T> map) {
    
        await using var cmd = new NpgsqlCommand(sql, _connection);
        await using var reader = await cmd.ExecuteReaderAsync();
        int count = 0;
        while (await reader.ReadAsync()) {
            map(reader, scratch);
            count++;
        }
        return count;
    }
    
    public async Task<int> ExecuteNonQueryAsync(string sql) {
        await using var cmd = new NpgsqlCommand(sql, _connection);
        return await cmd.ExecuteNonQueryAsync();
    }
}