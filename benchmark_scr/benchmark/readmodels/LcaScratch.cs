namespace benchmark_scr.benchmark.readmodels;

// Sc01 — LCA
public class LcaScratch
{
    public int LcaId;
    public string? GivenName = "";
    public string? Surname = "";
    public string Sex = "";
    public DateOnly? BirthDate;
    public string? BirthPlace;
    public DateOnly? DeathDate;
    public string? DeathPlace;
    public int PathFromA;
    public int PathFromB;
    public int TotalDist;
}