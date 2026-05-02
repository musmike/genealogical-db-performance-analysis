using System.Text.Json;
using benchmark_scr.benchmark.readmodels;
using Neo4j.Driver;

namespace benchmark_scr.queries
{
    public class DatabaseValidator {
        private readonly QueryRepo _repo;
        private readonly Dictionary<string, int> _expCounts;
        private readonly JsonSerializerOptions _jsonOptions;
        private readonly string _expectedDataDir;

        private readonly List<LcaScratch> _exp01;
        private readonly List<PersonScratch> _exp02;
        private readonly List<BirthStatScratch> _exp03;
        private readonly List<RelativeScratch> _exp04;
        private readonly List<RelativeScratch> _exp05;
        private readonly List<YoungestParentScratch> _exp06;

        public DatabaseValidator(Dataset dataset) {
            _repo = QueryRepo.Get(Configg.basePath, dataset);
            _expCounts = _repo.ExpectedCounts;

            var suffix = dataset switch {
                Dataset.small => "1k",
                Dataset.medium => "10k",
                Dataset.large => "100k",
                _ => throw new Exception("Unknown dataset")
            };

            _expectedDataDir = Path.Combine(AppContext.BaseDirectory, "scenarios", "scenario_validation",
                $"expected_data_{suffix}");
            _jsonOptions = new JsonSerializerOptions { IncludeFields = true };

            _exp01 = ReadCsv("Sc01").Select(c => new LcaScratch {
                LcaId = int.Parse(c[0]), GivenName = c[1] == "" ? null : c[1], Surname = c[2] == "" ? null : c[2],
                Sex = c[3], BirthDate = c[4] == "" ? null : DateOnly.Parse(c[4]), BirthPlace = c[5] == "" ? null : c[5],
                DeathDate = c[6] == "" ? null : DateOnly.Parse(c[6]), DeathPlace = c[7] == "" ? null : c[7],
                PathFromA = int.Parse(c[8]), PathFromB = int.Parse(c[9]), TotalDist = int.Parse(c[10])
            }).OrderBy(x => x.LcaId).ToList();

            _exp02 = ReadCsv("Sc02").Select(c => new PersonScratch {
                PersonId = int.Parse(c[0]), GivenName = c[1] == "" ? null : c[1], Surname = c[2] == "" ? null : c[2],
                Sex = c[3], BirthDate = c[4] == "" ? null : DateOnly.Parse(c[4]), BirthPlace = c[5] == "" ? null : c[5],
                DeathDate = c[6] == "" ? null : DateOnly.Parse(c[6]), DeathPlace = c[7] == "" ? null : c[7]
            }).OrderBy(x => x.BirthDate).ThenBy(x => x.PersonId).ToList();

            _exp03 = ReadCsv("Sc03").Select(c => new BirthStatScratch {
                City = c[0], QuarterCenturyStart = int.Parse(c[1]), BirthCount = long.Parse(c[2])
            }).OrderBy(x => x.City, StringComparer.Ordinal).ThenBy(x => x.QuarterCenturyStart).ToList();

            RelativeScratch ParseRelative(string[] c) => new RelativeScratch {
                RelativeId = int.Parse(c[0]), Generation = int.Parse(c[1]), GivenName = c[2] == "" ? null : c[2],
                Surname = c[3] == "" ? null : c[3], Sex = c[4], BirthDate = c[5] == "" ? null : DateOnly.Parse(c[5]),
                BirthPlace = c[6] == "" ? null : c[6], DeathDate = c[7] == "" ? null : DateOnly.Parse(c[7]),
                DeathPlace = c[8] == "" ? null : c[8], BurialPlace = c[9] == "" ? null : c[9],
                CauseOfDeath = c[10] == "" ? null : c[10], FatherId = c[11] == "" ? null : int.Parse(c[11]),
                MotherId = c[12] == "" ? null : int.Parse(c[12])
            };

            _exp04 = ReadCsv("Sc04").Select(ParseRelative).OrderBy(x => x.Generation).ThenBy(x => x.RelativeId)
                .ToList();
            _exp05 = ReadCsv("Sc05").Select(ParseRelative).OrderBy(x => x.Generation).ThenBy(x => x.RelativeId)
                .ToList();

            _exp06 = ReadCsv("Sc06").Select(c => new YoungestParentScratch {
                ParentId = int.Parse(c[0]), GivenName = c[1] == "" ? null : c[1], Surname = c[2] == "" ? null : c[2],
                Sex = c[3], BirthDate = c[4] == "" ? null : DateOnly.Parse(c[4]), BirthPlace = c[5] == "" ? null : c[5],
                AgeAtFirstChild = int.Parse(c[6]), AgeDiffDays = int.Parse(c[7]), ChildId = int.Parse(c[8]),
                ChildBirthDate = c[9] == "" ? null : DateOnly.Parse(c[9]), ChildBirthPlace = c[10] == "" ? null : c[10]
            }).OrderBy(x => x.ParentId).ThenBy(x => x.ChildId).ToList();
        }

        private List<string[]> ReadCsv(string name) {
            var path = Path.Combine(_expectedDataDir, $"{name}.csv");
            if (!File.Exists(path)) return new List<string[]>();
            return File.ReadAllLines(path).Skip(1).Select(l => l.Split(',')).ToList();
        }

        public async Task ValidatePostgresAsync(PostgresDriver pg) {
            Console.WriteLine("\n[Validator] Starting PostgreSQL pre-flight checks...");
            
            long totalPpl = 0, totalFam = 0, totalChild = 0;
            await pg.ExecuteConsumingAsync("SELECT COUNT(*) FROM people;", new object(),
                (r, _) => totalPpl = r.GetInt64(0));
            await pg.ExecuteConsumingAsync("SELECT COUNT(*) FROM families;", new object(),
                (r, _) => totalFam = r.GetInt64(0));
            await pg.ExecuteConsumingAsync("SELECT COUNT(*) FROM family_children;", new object(),
                (r, _) => totalChild = r.GetInt64(0));
            
            AssertEquals(totalPpl, _expCounts["TotalPeople"], "PostgreSQL Import - People");
            AssertEquals(totalFam, _expCounts["TotalFamilies"], "PostgreSQL Import - Families");
            AssertEquals(totalChild, _expCounts["TotalFamilyChildren"], "PostgreSQL Import - FamilyChildren");
            
            var pgIndexes = new List<string>();
            await pg.ExecuteConsumingAsync("SELECT indexname FROM pg_indexes WHERE schemaname = 'public';", 
                pgIndexes, (r, list) => list.Add(r.GetString(0)));
            
            string[] requiredPgIndexes = { 
                "people_pkey", "families_pkey", "pk_family_children", 
                "idx_fc_child_bio_cov", "idx_families_id_cov", 
                "idx_ppl_surname_birthdate", "idx_ppl_birthplace_birthdate", 
                "idx_families_husband", "idx_families_wife", 
                "idx_fc_family_bio_cov", "idx_fc_child" 
            };
            
            foreach (var idx in requiredPgIndexes) {
                if (!pgIndexes.Contains(idx)) {
                    throw new Exception($"[VALIDATION FAILED] PostgreSQL Index/Constraint '{idx}' is missing!");
                }
            }

            var act01 = new List<LcaScratch>();
            await pg.ExecuteConsumingAsync(_repo.PgScenario1, act01, (r, list) => {
                var s = new LcaScratch();
                PostgresMappers.MapSc01(r, s);
                list.Add(s);
            });
            act01 = act01.OrderBy(x => x.LcaId).ToList();
            AssertDeepEqual(act01, _exp01, "Pg01");

            var act02 = new List<PersonScratch>();
            await pg.ExecuteConsumingAsync(_repo.PgScenario2, act02, (r, list) => {
                var s = new PersonScratch();
                PostgresMappers.MapSc02(r, s);
                list.Add(s);
            });
            act02 = act02.OrderBy(x => x.BirthDate).ThenBy(x => x.PersonId).ToList();
            AssertDeepEqual(act02, _exp02, "Pg02");

            var act03 = new List<BirthStatScratch>();
            await pg.ExecuteConsumingAsync(_repo.PgScenario3, act03, (r, list) => {
                var s = new BirthStatScratch();
                PostgresMappers.MapSc03(r, s);
                list.Add(s);
            });
            act03 = act03.OrderBy(x => x.City, StringComparer.Ordinal).ThenBy(x => x.QuarterCenturyStart).ToList();
            AssertDeepEqual(act03, _exp03, "Pg03");

            var act04 = new List<RelativeScratch>();
            await pg.ExecuteConsumingAsync(_repo.PgScenario4, act04, (r, list) => {
                var s = new RelativeScratch();
                PostgresMappers.MapRelative(r, s);
                list.Add(s);
            });
            act04 = act04.OrderBy(x => x.Generation).ThenBy(x => x.RelativeId).ToList();
            AssertDeepEqual(act04, _exp04, "Pg04");

            var act05 = new List<RelativeScratch>();
            await pg.ExecuteConsumingAsync(_repo.PgScenario5, act05, (r, list) => {
                var s = new RelativeScratch();
                PostgresMappers.MapRelative(r, s);
                list.Add(s);
            });
            act05 = act05.OrderBy(x => x.Generation).ThenBy(x => x.RelativeId).ToList();
            AssertDeepEqual(act05, _exp05, "Pg05");

            var act06 = new List<YoungestParentScratch>();
            await pg.ExecuteConsumingAsync(_repo.PgScenario6, act06, (r, list) => {
                var s = new YoungestParentScratch();
                PostgresMappers.MapSc06(r, s);
                list.Add(s);
            });
            act06 = act06.OrderBy(x => x.ParentId).ThenBy(x => x.ChildId).ToList();
            AssertDeepEqual(act06, _exp06, "Pg06");

            var aff07 = await pg.ExecuteNonQueryAsync(_repo.PgScenario7);
            AssertEquals(aff07, _expCounts["Pg07"], "Pg07 Update execution");
            var aff07_rev = await pg.ExecuteNonQueryAsync(_repo.PgReverse7);
            AssertEquals(aff07_rev, _expCounts["Pg07"], "Pg07 Reverse update execution");

            var aff08 = await pg.ExecuteNonQueryAsync(_repo.PgScenario8);
            AssertEquals(aff08, _expCounts["Pg08"], "Pg08 Insert execution");

            var aff09 = await pg.ExecuteNonQueryAsync(_repo.PgScenario9);
            AssertEquals(aff09, _expCounts["Pg09"], "Pg09 Delete execution");
            
            pg.ExecuteNonQuery("VACUUM (ANALYZE) people;");
            pg.ExecuteNonQuery("VACUUM (ANALYZE) families;");
            pg.ExecuteNonQuery("VACUUM (ANALYZE) family_children;");

            Console.WriteLine("[Validator] PostgreSQL pre-flight checks PASSED.");
        }

        public async Task ValidateNeo4jAsync(Neo4jDriver n4j) {
            Console.WriteLine("\n[Validator] Starting Neo4j pre-flight checks...");
            
            long totalPpl = 0, totalFam = 0, totalChild = 0;
            await n4j.ExecuteReadCypherConsumingAsync("MATCH (n:Person) RETURN count(n)", new object(),
                (r, _) => totalPpl = r[0].As<long>());
            await n4j.ExecuteReadCypherConsumingAsync("MATCH (n:Family) RETURN count(n)", new object(),
                (r, _) => totalFam = r[0].As<long>());
            await n4j.ExecuteReadCypherConsumingAsync(
                "MATCH ()-[r:HAS_BIOLOGICAL_CHILD|HAS_ADOPTED_CHILD|HAS_FOSTER_CHILD]->() RETURN count(r)",
                new object(), (r, _) => totalChild = r[0].As<long>());
            
            AssertEquals(totalPpl, _expCounts["TotalPeople"], "Neo4j Import - People");
            AssertEquals(totalFam, _expCounts["TotalFamilies"], "Neo4j Import - Families");
            AssertEquals(totalChild, _expCounts["TotalFamilyChildren"], "Neo4j Import - FamilyChildren");
            
            var neoIndexes = new List<string>();
            await n4j.ExecuteReadCypherConsumingAsync("SHOW INDEXES YIELD name, state WHERE state = 'ONLINE' RETURN name", 
                neoIndexes, (r, list) => list.Add(r[0].As<string>()));
            await n4j.ExecuteReadCypherConsumingAsync("SHOW CONSTRAINTS YIELD name", neoIndexes, 
                (r, list) => list.Add(r[0].As<string>()));
            
            string[] requiredNeoIndexes = { 
                "person_sex_required", "person_id_unique", 
                "person_surname_birthdate", "idx_person_place_birthdate", 
                "person_birthPlace", "person_deathPlace", 
                "family_marriagePlace", "family_id_unique" 
            };
            
            foreach (var idx in requiredNeoIndexes) {
                if (!neoIndexes.Contains(idx)) {
                    throw new Exception($"[VALIDATION FAILED] Neo4j Index/Constraint '{idx}' is missing or not ONLINE!");
                }
            }

            var act01 = new List<LcaScratch>();
            await n4j.ExecuteReadCypherConsumingAsync(_repo.NeoScenario1, act01, (r, list) => {
                var s = new LcaScratch();
                Neo4jMappers.MapSc01(r, s);
                list.Add(s);
            });
            act01 = act01.OrderBy(x => x.LcaId).ToList();
            AssertDeepEqual(act01, _exp01, "Neo01");

            var act02 = new List<PersonScratch>();
            await n4j.ExecuteReadCypherConsumingAsync(_repo.NeoScenario2, act02, (r, list) => {
                var s = new PersonScratch();
                Neo4jMappers.MapSc02(r, s);
                list.Add(s);
            });
            act02 = act02.OrderBy(x => x.BirthDate).ThenBy(x => x.PersonId).ToList();
            AssertDeepEqual(act02, _exp02, "Neo02");

            var act03 = new List<BirthStatScratch>();
            await n4j.ExecuteReadCypherConsumingAsync(_repo.NeoScenario3, act03, (r, list) => {
                var s = new BirthStatScratch();
                Neo4jMappers.MapSc03(r, s);
                list.Add(s);
            });
            act03 = act03.OrderBy(x => x.City, StringComparer.Ordinal).ThenBy(x => x.QuarterCenturyStart).ToList();
            AssertDeepEqual(act03, _exp03, "Neo03");

            var act04 = new List<RelativeScratch>();
            await n4j.ExecuteReadCypherConsumingAsync(_repo.NeoScenario4, act04, (r, list) => {
                var s = new RelativeScratch();
                Neo4jMappers.MapRelative(r, s);
                list.Add(s);
            });
            act04 = act04.OrderBy(x => x.Generation).ThenBy(x => x.RelativeId).ToList();
            AssertDeepEqual(act04, _exp04, "Neo04");

            var act05 = new List<RelativeScratch>();
            await n4j.ExecuteReadCypherConsumingAsync(_repo.NeoScenario5, act05, (r, list) => {
                var s = new RelativeScratch();
                Neo4jMappers.MapRelative(r, s);
                list.Add(s);
            });
            act05 = act05.OrderBy(x => x.Generation).ThenBy(x => x.RelativeId).ToList();
            AssertDeepEqual(act05, _exp05, "Neo05");

            var act06 = new List<YoungestParentScratch>();
            await n4j.ExecuteReadCypherConsumingAsync(_repo.NeoScenario6, act06, (r, list) => {
                var s = new YoungestParentScratch();
                Neo4jMappers.MapSc06(r, s);
                list.Add(s);
            });
            act06 = act06.OrderBy(x => x.ParentId).ThenBy(x => x.ChildId).ToList();
            AssertDeepEqual(act06, _exp06, "Neo06");

            var aff07 = await n4j.ExecuteWriteCypherAsync(_repo.NeoScenario7);
            AssertEquals(aff07, _expCounts["Neo07"], "Neo07 Update execution");
            var aff07_rev = await n4j.ExecuteWriteCypherAsync(_repo.NeoReverse7);
            AssertEquals(aff07_rev, _expCounts["Neo07"], "Neo07 Reverse update execution");

            var aff08 = await n4j.ExecuteWriteCypherAsync(_repo.NeoScenario8);
            AssertEquals(aff08, _expCounts["Neo08"], "Neo08 Insert execution");

            var aff09 = await n4j.ExecuteWriteCypherAsync(_repo.NeoScenario9);
            AssertEquals(aff09, _expCounts["Neo09"], "Neo09 Delete execution");

            Console.WriteLine("[Validator] Neo4j pre-flight checks PASSED.");
        }

        private void AssertEquals(long actual, long expected, string scenario) {
            if (actual != expected)
                throw new Exception($"[VALIDATION FAILED] {scenario}: Expected {expected}, got {actual}.");
        }

        private void AssertDeepEqual<T>(List<T> actual, List<T> expected, string scenario) {
            if (actual.Count != expected.Count)
                throw new Exception(
                    $"[VALIDATION FAILED] {scenario}: Row count mismatch. Expected {expected.Count}, got {actual.Count}.");

            for (int i = 0; i < actual.Count; i++) {
                var actStr = JsonSerializer.Serialize(actual[i], _jsonOptions);
                var expStr = JsonSerializer.Serialize(expected[i], _jsonOptions);
                if (actStr != expStr) {
                    throw new Exception(
                        $"[VALIDATION FAILED] {scenario}: Row {i} mismatch.\nExpected: {expStr}\nActual:   {actStr}");
                }
            }
        }
    }
}