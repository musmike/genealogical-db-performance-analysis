using Npgsql;
using Neo4j.Driver;

namespace benchmark_scr.benchmark.readmodels
{
    public static class PostgresMappers
    {
        public static void MapSc01(NpgsqlDataReader r, LcaScratch s) {
            s.LcaId      = r.GetInt32(0);
            s.GivenName  = r.IsDBNull(1) ? null : r.GetString(1);
            s.Surname    = r.IsDBNull(2) ? null : r.GetString(2);
            s.Sex        = r.GetString(3);
            s.BirthDate  = r.IsDBNull(4) ? null : r.GetFieldValue<DateOnly>(4);
            s.BirthPlace = r.IsDBNull(5) ? null : r.GetString(5);
            s.DeathDate  = r.IsDBNull(6) ? null : r.GetFieldValue<DateOnly>(6);
            s.DeathPlace = r.IsDBNull(7) ? null : r.GetString(7);
            s.PathFromA  = r.GetInt32(8);
            s.PathFromB  = r.GetInt32(9);
            s.TotalDist  = r.GetInt32(10);
        }

        public static void MapSc02(NpgsqlDataReader r, PersonScratch s) {
            s.PersonId   = r.GetInt32(0);
            s.GivenName  = r.IsDBNull(1) ? null : r.GetString(1);
            s.Surname    = r.IsDBNull(2) ? null : r.GetString(2);
            s.Sex        = r.GetString(3);
            s.BirthDate  = r.IsDBNull(4) ? null : r.GetFieldValue<DateOnly>(4);
            s.BirthPlace = r.IsDBNull(5) ? null : r.GetString(5);
            s.DeathDate  = r.IsDBNull(6) ? null : r.GetFieldValue<DateOnly>(6);
            s.DeathPlace = r.IsDBNull(7) ? null : r.GetString(7);
        }

        public static void MapSc03(NpgsqlDataReader r, BirthStatScratch s) {
            s.City                = r.GetString(0);
            s.QuarterCenturyStart = r.GetInt32(1);
            s.BirthCount          = r.GetInt64(2);
        }
        
        public static void MapRelative(NpgsqlDataReader r, RelativeScratch s) {
            s.RelativeId   = r.GetInt32(0);
            s.Generation   = r.GetInt32(1);
            s.GivenName    = r.IsDBNull(2) ? null : r.GetString(2);
            s.Surname      = r.IsDBNull(3) ? null : r.GetString(3);
            s.Sex          = r.GetString(4);
            s.BirthDate    = r.IsDBNull(5)  ? null : r.GetFieldValue<DateOnly>(5);
            s.BirthPlace   = r.IsDBNull(6)  ? null : r.GetString(6);
            s.DeathDate    = r.IsDBNull(7)  ? null : r.GetFieldValue<DateOnly>(7);
            s.DeathPlace   = r.IsDBNull(8)  ? null : r.GetString(8);
            s.BurialPlace  = r.IsDBNull(9)  ? null : r.GetString(9);
            s.CauseOfDeath = r.IsDBNull(10) ? null : r.GetString(10);
            s.FatherId     = r.IsDBNull(11) ? null : r.GetInt32(11);
            s.MotherId     = r.IsDBNull(12) ? null : r.GetInt32(12);
        }

        public static void MapSc06(NpgsqlDataReader r, YoungestParentScratch s) {
            s.ParentId         = r.GetInt32(0);
            s.GivenName        = r.IsDBNull(1) ? null : r.GetString(1);
            s.Surname          = r.IsDBNull(2) ? null : r.GetString(2);
            s.Sex              = r.GetString(3);
            s.BirthDate        = r.IsDBNull(4) ? null : r.GetFieldValue<DateOnly>(4);
            s.BirthPlace       = r.IsDBNull(5) ? null : r.GetString(5);
            s.AgeAtFirstChild  = r.GetInt32(6);
            s.AgeDiffDays      = r.GetInt32(7);
            s.ChildId          = r.GetInt32(8);
            s.ChildBirthDate   = r.IsDBNull(9)  ? null : r.GetFieldValue<DateOnly>(9);
            s.ChildBirthPlace  = r.IsDBNull(10) ? null : r.GetString(10);
        }
    }

    public static class Neo4jMappers
    {
        public static void MapSc01(IRecord r, LcaScratch s) {
            s.LcaId      = r[0].As<int>();
            s.GivenName  = r[1].As<string?>();
            s.Surname    = r[2].As<string?>();
            s.Sex        = r[3].As<string>();
            s.BirthDate  = r[4] is LocalDate bd ? new DateOnly(bd.Year, bd.Month, bd.Day) : null;
            s.BirthPlace = r[5].As<string?>();
            s.DeathDate  = r[6] is LocalDate dd ? new DateOnly(dd.Year, dd.Month, dd.Day) : null;
            s.DeathPlace = r[7].As<string?>();
            s.PathFromA  = r[8].As<int>();
            s.PathFromB  = r[9].As<int>();
            s.TotalDist  = r[10].As<int>();
        }

        public static void MapSc02(IRecord r, PersonScratch s) {
            s.PersonId   = r[0].As<int>();
            s.GivenName  = r[1].As<string?>();
            s.Surname    = r[2].As<string?>();
            s.Sex        = r[3].As<string>();
            s.BirthDate  = r[4] is LocalDate bd ? new DateOnly(bd.Year, bd.Month, bd.Day) : null;
            s.BirthPlace = r[5].As<string?>();
            s.DeathDate  = r[6] is LocalDate dd ? new DateOnly(dd.Year, dd.Month, dd.Day) : null;
            s.DeathPlace = r[7].As<string?>();
        }

        public static void MapSc03(IRecord r, BirthStatScratch s) {
            s.City                = r[0].As<string>();
            s.QuarterCenturyStart = r[1].As<int>();
            s.BirthCount          = r[2].As<long>();
        }
        
        public static void MapRelative(IRecord r, RelativeScratch s) {
            s.RelativeId   = r[0].As<int>();
            s.Generation   = r[1].As<int>();
            s.GivenName    = r[2].As<string?>();
            s.Surname      = r[3].As<string?>();
            s.Sex          = r[4].As<string>();
            s.BirthDate    = r[5] is LocalDate bd ? new DateOnly(bd.Year, bd.Month, bd.Day) : null;
            s.BirthPlace   = r[6].As<string?>();
            s.DeathDate    = r[7] is LocalDate dd ? new DateOnly(dd.Year, dd.Month, dd.Day) : null;
            s.DeathPlace   = r[8].As<string?>();
            s.BurialPlace  = r[9].As<string?>();
            s.CauseOfDeath = r[10].As<string?>();
            s.FatherId     = r[11].As<int?>();
            s.MotherId     = r[12].As<int?>();
        }

        public static void MapSc06(IRecord r, YoungestParentScratch s) {
            s.ParentId         = r[0].As<int>();
            s.GivenName        = r[1].As<string?>();
            s.Surname          = r[2].As<string?>();
            s.Sex              = r[3].As<string>();
            s.BirthDate        = r[4] is LocalDate bd ? new DateOnly(bd.Year, bd.Month, bd.Day) : null;
            s.BirthPlace       = r[5].As<string?>();
            s.AgeAtFirstChild  = r[6].As<int>();
            s.AgeDiffDays      = r[7].As<int>();
            s.ChildId          = r[8].As<int>();
            s.ChildBirthDate   = r[9] is LocalDate cbd ? new DateOnly(cbd.Year, cbd.Month, cbd.Day) : null;
            s.ChildBirthPlace  = r[10].As<string?>();
        }
    }
}