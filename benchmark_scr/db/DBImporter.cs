using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace benchmark_scr.db {
    internal class DBImporter {
        private readonly PostgresImport _pg;
        private readonly Neo4jImport _neo;

        public DBImporter(PostgresImport pg, Neo4jImport neo) {
            _pg = pg;
            _neo = neo;
        }

        public async Task ImportPostgresAsync(
            string ddl,
            string datasetSql,
            string finalSql) {
            _pg.ImportAsync(ddl, datasetSql, finalSql);
        }

        public async Task ImportNeo4jAsync(
            string datasetScript,
            string universalScript,
            string cypher) {
            await _neo.ImportAsync(datasetScript, universalScript, cypher);
        }
    }
}
