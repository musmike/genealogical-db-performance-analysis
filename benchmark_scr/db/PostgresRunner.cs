using Neo4j.Driver;
using Npgsql;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

//static class PostgresRunner {
//    private static readonly NpgsqlConnection _conn;
//    static PostgresRunner() {
//        _conn = new NpgsqlConnection(
//            "Host=localhost;Port=5432;Username=postgres;Password=postgres;Database=postgres");
//        _conn.Open();
//    }

//    public static void Execute(Dataset ds, QueryId q, bool consume = true) {
//        string sql = QueryStore.Get(DbType.PostgreSQL, ds, q);
//        using var cmd = new NpgsqlCommand(sql, _conn);
//        if(!consume) {
//            cmd.ExecuteNonQuery();
//            return;
//        }

//        using var reader = cmd.ExecuteReader();
//        while(reader.Read()) { 

//        }
//    }
//}
public class PostgresDriver:IDisposable {
    private readonly string _connectionString;
    private NpgsqlConnection _connection;

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

    // --- PREPARED ---
    public NpgsqlCommand Prepare(string sql) {
        var cmd = new NpgsqlCommand(sql, _connection);
        cmd.Prepare();
        return cmd;
    }
}