using Npgsql;

public class PostgresDriver:IDisposable {
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

    // --- IMPORT ---
    public void ExecuteNonQuery(string sql) {
        using var cmd = new NpgsqlCommand(sql, _connection);
        cmd.ExecuteNonQuery();
    }

    // --- QUERY ---
    public int ExecuteScalarInt(string sql) {
        using var cmd = new NpgsqlCommand(sql, _connection);
        return Convert.ToInt32(cmd.ExecuteScalar());
    }

    public void ExecuteReader(string sql, Action<NpgsqlDataReader> handler) {
        using var cmd = new NpgsqlCommand(sql, _connection);
        using var reader = cmd.ExecuteReader();

        while(reader.Read()) {
            handler(reader);
        }
    }
    
    public async Task<int> ExecuteConsumingAsync<T>(
        string sql, T scratch, Action<NpgsqlDataReader, T> map) {
    
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

    // --- PREPARED ---
    public NpgsqlCommand Prepare(string sql) {
        var cmd = new NpgsqlCommand(sql, _connection);
        cmd.Prepare();
        return cmd;
    }
}