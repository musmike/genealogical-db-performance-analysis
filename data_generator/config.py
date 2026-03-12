"""
Global configuration for the genealogical simulation.

Defines the random seed, per-scenario graph analysis parameters,
and all name/place/occupation/cause-of-death pools used during generation.
"""

# Fixed random seed ensures fully reproducible simulation runs across executions.
SEED = 26

# Per-population-size configuration for the LCA and ancestor-retrieval analytics.
# - min_lca_path / max_lca_path: the required total path length between two individuals
#   through their Lowest Common Ancestor, used to select a representative pair for
#   graph querying benchmarks.
# - ancestors_depth: the maximum number of generations traversed upward when counting
#   distinct ancestors for the ancestor-retrieval scenario.
SCENARIOS = {
    1000: {
        'min_lca_path': 8,
        'max_lca_path': 8,
        'ancestors_depth': 5,
        'descendants_depth': 3
    },
    10000: {
        'min_lca_path': 12,
        'max_lca_path': 12,
        'ancestors_depth': 10,
        'descendants_depth': 6
    },
    100000: {
        'min_lca_path': 16,
        'max_lca_path': 16,
        'ancestors_depth': 15,
        'descendants_depth': 10
    }
}

# Pool of historically plausible Polish male given names used when generating individuals.
MALE_NAMES = [
    "Jan", "Piotr", "Michał", "Andrzej", "Tomasz", "Krzysztof", "Jakub", "Wojciech", "Stanisław", "Maciej",
    "Adam", "Paweł", "Marcin", "Józef", "Kamil", "Łukasz", "Bartosz", "Grzegorz", "Marek", "Mateusz",
    "Szymon", "Filip", "Antoni", "Franciszek", "Ignacy", "Kazimierz", "Władysław", "Zygmunt", "Tadeusz", "Stefan",
    "Julian", "Leon", "Henryk", "Czesław", "Marian", "Ryszard", "Jerzy", "Wiesław", "Mirosław", "Dariusz"
]

# Pool of historically plausible Polish female given names used when generating individuals.
FEMALE_NAMES = [
    "Anna", "Maria", "Katarzyna", "Małgorzata", "Agnieszka", "Barbara", "Krystyna", "Ewa", "Elżbieta", "Zofia",
    "Joanna", "Aleksandra", "Monika", "Teresa", "Danuta", "Natalia", "Julia", "Zuzanna", "Alicja", "Wiktoria",
    "Oliwia", "Maja", "Helena", "Jadwiga", "Irena", "Halina", "Grażyna", "Bożena", "Urszula", "Wanda",
    "Ludwika", "Marianna", "Rozalia", "Stefania", "Leokadia", "Genowefa", "Kazimiera", "Czesława", "Józefa", "Regina"
]

# Pool of common Polish surnames. Female individuals receive grammatically
# adjusted forms (e.g., "Kowalski" → "Kowalska") via adjust_surname().
SURNAMES = [
    "Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski", "Zieliński", "Szymański", "Woźniak",
    "Dąbrowski", "Kozłowski", "Jankowski", "Mazur", "Wojciechowski", "Kwiatkowski", "Krawczyk", "Kaczmarek", "Piotrowski", "Grabowski",
    "Zając", "Pawłowski", "Michalski", "Król", "Wieczorek", "Jabłoński", "Wróbel", "Nowakowski", "Majewski", "Olszewski",
    "Stępień", "Malinowski", "Jaworski", "Adamczyk", "Dudek", "Górski", "Pawlak", "Sikora", "Walczak", "Baran"
]

# Pool of towns and villages used as birth, death, and marriage locations.
PLACES = [
    "Warszawa", "Kraków", "Posen", "Danzig", "Breslau", "Łódź", "Lublin", "Stettin", "Bromberg", "Katowice",
    "Białystok", "Gdynia", "Częstochowa", "Radom", "Sosnowiec", "Thorn", "Kielce", "Rzeszów", "Gliwice", "Olsztyn",
    "Lipce", "Bronowice", "Zalipie", "Chochołów", "Sromowce", "Lanckorona", "Złoty Potok", "Supraśl", "Tykocin", "Biecz",
    "Kazimierz Dolny", "Sandomierz", "Zwierzyniec", "Reszel", "Chełmno", "Pszczyna", "Cieszyn", "Sanok", "Krynica", "Wisła"
]

# Pool of pre-industrial occupations assigned to individuals upon marriage or death.
# None values increase the probability of an individual having no recorded occupation.
OCCUPATIONS = [
    "Farmer", "Blacksmith", "Shoemaker", "Tailor", "Carpenter", "Merchant", "Teacher", "Doctor", "Soldier",
    "Baker", "Butcher", "Weaver", "Miller", "Fisherman", "Potter", "Mason", "Scribe", "Priest", "Innkeeper",
    "Tanner", "Cooper", "Wheelwright", "Miner", "Hunter", "Shepherd", "Clerk", "Judge", "Lawyer", "Artist",
    None, None, None, None, None, None
]

# Pool of historically plausible causes of death.
# None values represent cases where no cause of death was recorded.
CAUSES_OF_DEATH = [
    "Infectious disease", "Accident", "Pneumonia", "Fever", "Unknown", "Consumption", "Heart failure",
    "Stroke", "Cancer", "Drowning", "War casualty", "Plague", "Smallpox", "Cholera", "Typhus",
    "Dysentery", "Influenza", "Starvation", "Fire", "Murder", "Dropsy", "Apoplexy",
    None, None, None, None
]