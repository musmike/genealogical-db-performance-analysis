using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

static class QueryStore {
    public static string[] n4jqueries1k = new string[9];
    public static string[] n4jqueries10k = new string[9];
    public static string[] n4jqueries100k = new string[9];
    public static string[] psqqueries1k = new string[9];
    public static string[] psqqueries10k = new string[9];
    public static string[] psqqueries100k = new string[9];

    public static string Get(DbType db, Dataset ds, QueryId q) {
        switch(db) {
            case DbType.PostgreSQL:
                switch(ds) {
                    case Dataset._1k:
                        return psqqueries1k[(int)q];
                    case Dataset._10k:
                        return psqqueries10k[(int)q];
                    case Dataset._100k:
                        return psqqueries100k[(int)q];
                    default:
                        return "";
                }
            case DbType.Neo4j:
                switch(ds) {
                    case Dataset._1k:
                        return n4jqueries1k[(int)q];
                    case Dataset._10k:
                        return n4jqueries10k[(int)q];
                    case Dataset._100k:
                        return n4jqueries100k[(int)q];
                    default:
                        return "";
                }
            default:
                return "";
        }
    }

    public static string[] GetSet(DbType db, Dataset ds) {
        switch (db) {
            case DbType.PostgreSQL:
                switch (ds) {
                    case Dataset._1k:
                        return psqqueries1k;
                    case Dataset._10k:
                        return psqqueries10k;
                    case Dataset._100k:
                        return psqqueries100k;
                    default:
                        return null!;
                }
            case DbType.Neo4j:
                switch (ds) {
                    case Dataset._1k:
                        return n4jqueries1k;
                    case Dataset._10k:
                        return n4jqueries10k;
                    case Dataset._100k:
                        return n4jqueries100k;
                    default:
                        return null!;
                }
            default:
                return null!;
        }
    }

    public static void Load() {
        LoadPostgres();
        LoadN4j();
    }

    public static void LoadPostgres() {
        const string dir = "scenarios/postgres_scenarios";
        psqqueries1k[0] = File.ReadAllText(Path.Combine(dir, "scenario_01_lca", "scenario_01_lca_1k.sql"));
        psqqueries1k[1] = File.ReadAllText(Path.Combine(dir, "scenario_02_surname_filter", "scenario_02_surname_filter_1k.sql"));
        psqqueries1k[2] = File.ReadAllText(Path.Combine(dir, "scenario_03_births_by_city", "scenario_03_births_by_city.sql"));
        psqqueries1k[3] = File.ReadAllText(Path.Combine(dir, "scenario_04_ancestors", "scenario_04_ancestors_1k.sql"));
        psqqueries1k[4] = File.ReadAllText(Path.Combine(dir, "scenario_05_descendants", "scenario_05_descendants_1k.sql"));
        psqqueries1k[5] = File.ReadAllText(Path.Combine(dir, "scenario_06_youngest_parent", "scenario_06_youngest_parent.sql"));
        psqqueries1k[6] = File.ReadAllText(Path.Combine(dir, "scenario_07_place_name_update", "scenario_07_place_name_update.sql"));
        psqqueries1k[7] = File.ReadAllText(Path.Combine(dir, "scenario_08_insert", "scenario_08_insert_1k.sql"));
        psqqueries1k[8] = File.ReadAllText(Path.Combine(dir, "scenario_09_delete", "scenario_09_delete_1k.sql"));
        psqqueries10k[0] = File.ReadAllText(Path.Combine(dir, "scenario_01_lca", "scenario_01_lca_10k.sql"));
        psqqueries10k[1] = File.ReadAllText(Path.Combine(dir, "scenario_02_surname_filter", "scenario_02_surname_filter_10k.sql"));
        psqqueries10k[2] = File.ReadAllText(Path.Combine(dir, "scenario_03_births_by_city", "scenario_03_births_by_city.sql"));
        psqqueries10k[3] = File.ReadAllText(Path.Combine(dir, "scenario_04_ancestors", "scenario_04_ancestors_10k.sql"));
        psqqueries10k[4] = File.ReadAllText(Path.Combine(dir, "scenario_05_descendants", "scenario_05_descendants_10k.sql"));
        psqqueries10k[5] = File.ReadAllText(Path.Combine(dir, "scenario_06_youngest_parent", "scenario_06_youngest_parent.sql"));
        psqqueries10k[6] = File.ReadAllText(Path.Combine(dir, "scenario_07_place_name_update", "scenario_07_place_name_update.sql"));
        psqqueries10k[7] = File.ReadAllText(Path.Combine(dir, "scenario_08_insert", "scenario_08_insert_10k.sql"));
        psqqueries10k[8] = File.ReadAllText(Path.Combine(dir, "scenario_09_delete", "scenario_09_delete_10k.sql"));
        psqqueries100k[0] = File.ReadAllText(Path.Combine(dir, "scenario_01_lca", "scenario_01_lca_100k.sql"));
        psqqueries100k[1] = File.ReadAllText(Path.Combine(dir, "scenario_02_surname_filter", "scenario_02_surname_filter_100k.sql"));
        psqqueries100k[2] = File.ReadAllText(Path.Combine(dir, "scenario_03_births_by_city", "scenario_03_births_by_city.sql"));
        psqqueries100k[3] = File.ReadAllText(Path.Combine(dir, "scenario_04_ancestors", "scenario_04_ancestors_100k.sql"));
        psqqueries100k[4] = File.ReadAllText(Path.Combine(dir, "scenario_05_descendants", "scenario_05_descendants_100k.sql"));
        psqqueries100k[5] = File.ReadAllText(Path.Combine(dir, "scenario_06_youngest_parent", "scenario_06_youngest_parent.sql"));
        psqqueries100k[6] = File.ReadAllText(Path.Combine(dir, "scenario_07_place_name_update", "scenario_07_place_name_update.sql"));
        psqqueries100k[7] = File.ReadAllText(Path.Combine(dir, "scenario_08_insert", "scenario_08_insert_100k.sql"));
        psqqueries100k[8] = File.ReadAllText(Path.Combine(dir, "scenario_09_delete", "scenario_09_delete_100k.sql"));
    }

    public static void LoadN4j() {
        const string dir = "scenarios/neo4j_scenarios";
        n4jqueries1k[0] = File.ReadAllText(Path.Combine(dir, "scenario_01_lca", "scenario_01_lca_1k.cypher"));
        n4jqueries1k[1] = File.ReadAllText(Path.Combine(dir, "scenario_02_surname_filter", "scenario_02_surname_filter_1k.cypher"));
        n4jqueries1k[2] = File.ReadAllText(Path.Combine(dir, "scenario_03_births_by_city", "scenario_03_births_by_city.cypher"));
        n4jqueries1k[3] = File.ReadAllText(Path.Combine(dir, "scenario_04_ancestors", "scenario_04_ancestors_1k.cypher"));
        n4jqueries1k[4] = File.ReadAllText(Path.Combine(dir, "scenario_05_descendants", "scenario_05_descendants_1k.cypher"));
        n4jqueries1k[5] = File.ReadAllText(Path.Combine(dir, "scenario_06_youngest_parent", "scenario_06_youngest_parent.cypher"));
        n4jqueries1k[6] = File.ReadAllText(Path.Combine(dir, "scenario_07_place_name_update", "scenario_07_place_name_update.cypher"));
        n4jqueries1k[7] = File.ReadAllText(Path.Combine(dir, "scenario_08_insert", "scenario_08_insert_1k.cypher"));
        n4jqueries1k[8] = File.ReadAllText(Path.Combine(dir, "scenario_09_delete", "scenario_09_delete_1k.cypher"));
        n4jqueries10k[0] = File.ReadAllText(Path.Combine(dir, "scenario_01_lca", "scenario_01_lca_10k.cypher"));
        n4jqueries10k[1] = File.ReadAllText(Path.Combine(dir, "scenario_02_surname_filter", "scenario_02_surname_filter_10k.cypher"));
        n4jqueries10k[2] = File.ReadAllText(Path.Combine(dir, "scenario_03_births_by_city", "scenario_03_births_by_city.cypher"));
        n4jqueries10k[3] = File.ReadAllText(Path.Combine(dir, "scenario_04_ancestors", "scenario_04_ancestors_10k.cypher"));
        n4jqueries10k[4] = File.ReadAllText(Path.Combine(dir, "scenario_05_descendants", "scenario_05_descendants_10k.cypher"));
        n4jqueries10k[5] = File.ReadAllText(Path.Combine(dir, "scenario_06_youngest_parent", "scenario_06_youngest_parent.cypher"));
        n4jqueries10k[6] = File.ReadAllText(Path.Combine(dir, "scenario_07_place_name_update", "scenario_07_place_name_update.cypher"));
        n4jqueries10k[7] = File.ReadAllText(Path.Combine(dir, "scenario_08_insert", "scenario_08_insert_10k.cypher"));
        n4jqueries10k[8] = File.ReadAllText(Path.Combine(dir, "scenario_09_delete", "scenario_09_delete_10k.cypher"));
        n4jqueries100k[0] = File.ReadAllText(Path.Combine(dir, "scenario_01_lca", "scenario_01_lca_100k.cypher"));
        n4jqueries100k[1] = File.ReadAllText(Path.Combine(dir, "scenario_02_surname_filter", "scenario_02_surname_filter_100k.cypher"));
        n4jqueries100k[2] = File.ReadAllText(Path.Combine(dir, "scenario_03_births_by_city", "scenario_03_births_by_city.cypher"));
        n4jqueries100k[3] = File.ReadAllText(Path.Combine(dir, "scenario_04_ancestors", "scenario_04_ancestors_100k.cypher"));
        n4jqueries100k[4] = File.ReadAllText(Path.Combine(dir, "scenario_05_descendants", "scenario_05_descendants_100k.cypher"));
        n4jqueries100k[5] = File.ReadAllText(Path.Combine(dir, "scenario_06_youngest_parent", "scenario_06_youngest_parent.cypher"));
        n4jqueries100k[6] = File.ReadAllText(Path.Combine(dir, "scenario_07_place_name_update", "scenario_07_place_name_update.cypher"));
        n4jqueries100k[7] = File.ReadAllText(Path.Combine(dir, "scenario_08_insert", "scenario_08_insert_100k.cypher"));
        n4jqueries100k[8] = File.ReadAllText(Path.Combine(dir, "scenario_09_delete", "scenario_09_delete_100k.cypher"));
    }
}