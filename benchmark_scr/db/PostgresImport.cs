using Npgsql;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace benchmark_scr.db {
    internal class PostgresImport {
        private PostgresDriver _driver;

        public PostgresImport(string connectionString) {
            _driver = new PostgresDriver(connectionString);
            _driver.Open();
        }

        public void ImportAsync(string ddl, string datasetSql, string finalSql) {
            _driver.Open();

            ExecuteAsync(ddl);
            ExecuteAsync(datasetSql);
            ExecuteAsync(finalSql);
        }

        private void ExecuteAsync(string sql) {
            _driver.ExecuteNonQuery(sql); 
        }
    }
}
