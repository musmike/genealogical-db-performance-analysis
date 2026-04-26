namespace benchmark_scr.benchmark.readmodels;

// Sc04 + Sc05 — Ancestor / Descendant
public class RelativeScratch
{
    public int RelativeId;
    public int Generation;
    public string GivenName = "";
    public string Surname = "";
    public string Sex = "";
    public DateOnly? BirthDate;
    public string? BirthPlace;
    public DateOnly? DeathDate;
    public string? DeathPlace;
    public string? BurialPlace;
    public string? CauseOfDeath;
    public int? FatherId;
    public int? MotherId;
}