using Npgsql;
using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

static class PostgresRunner {
    private static readonly NpgsqlConnection _conn;
    static PostgresRunner() {
        _conn = new NpgsqlConnection(
            "Host=localhost;Port=5432;Username=user;Password=password;Database=benchmark_db");
        _conn.Open();
    }

    public static void Execute(string query) {
        if (_conn.State != ConnectionState.Open)
            _conn.Open();
        using var cmd = new NpgsqlCommand(query, _conn);
        using var reader = cmd.ExecuteReader();

        while (reader.Read()) { }
    }
}
