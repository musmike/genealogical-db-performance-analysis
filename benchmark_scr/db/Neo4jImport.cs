using Neo4j.Driver;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace benchmark_scr.db {
    internal class Neo4jImport {
        private readonly Neo4jDriver _driver;

        public Neo4jImport(string uri, string user, string password) {
            _driver = new Neo4jDriver(uri, user, password);
        }

        public async Task ImportAsync(
            string datasetScript,
            string universalScript,
            string cypherQuery) {
            

            await BashRunner.RunAsync(datasetScript);
            await BashRunner.RunAsync(universalScript);
            await ExecuteCypherAsync(cypherQuery);
        }

        private async Task ExecuteCypherAsync(string query) {
            await _driver.ExecuteWriteScriptAsync(query);
        }

        public async ValueTask DisposeAsync() {
            await _driver.DisposeAsync();
        }
    }
}
