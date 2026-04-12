"""
Central configuration module for the demographic simulation.
Contains the random seed, scenario parameters for three population scales,
and dictionaries of historical data: names, surnames, places, and occupations.
"""

# A fixed seed guarantees full reproducibility of simulation results
SEED = 185242

# Scenario parameters for each population scale.
# Define genealogical tree depth (ancestors/descendants),
# simulation start year, number of founding pairs, and fertility rate.
SCENARIOS = {
   1000: {
       'min_lca_path': 8, 'max_lca_path': 8, 'ancestors_depth': 5, 'descendants_depth': 3,
       'start_year': 1800, 'initial_pairs': 24, 'avg_children': 3.88, 'immigrants': 1
   },
   10000: {
       'min_lca_path': 12, 'max_lca_path': 12, 'ancestors_depth': 10, 'descendants_depth': 6,
       'start_year': 1500, 'initial_pairs': 94, 'avg_children': 3.08, 'immigrants': 1
   },
   100000: {
       'min_lca_path': 16, 'max_lca_path': 16, 'ancestors_depth': 15, 'descendants_depth': 10,
       'start_year': 800, 'initial_pairs': 125, 'avg_children': 2.85, 'immigrants': 1
   }
}

MALE_NAMES = [
    "Jan", "Piotr", "Michał", "Andrzej", "Tomasz", "Krzysztof", "Jakub", "Wojciech", "Stanisław",
    "Maciej", "Adam", "Paweł", "Marcin", "Józef", "Kamil", "Łukasz", "Bartosz", "Grzegorz",
    "Marek", "Mateusz", "Szymon", "Filip", "Antoni", "Franciszek", "Ignacy", "Kazimierz",
    "Władysław", "Zygmunt", "Tadeusz", "Stefan", "Julian", "Leon", "Henryk", "Czesław",
    "Marian", "Ryszard", "Jerzy", "Wiesław", "Mirosław", "Dariusz"
]

FEMALE_NAMES = [
    "Anna", "Maria", "Katarzyna", "Małgorzata", "Agnieszka", "Barbara", "Krystyna", "Ewa",
    "Elżbieta", "Zofia", "Joanna", "Aleksandra", "Monika", "Teresa", "Danuta", "Natalia",
    "Julia", "Zuzanna", "Alicja", "Wiktoria", "Oliwia", "Maja", "Helena", "Jadwiga", "Irena",
    "Halina", "Grażyna", "Bożena", "Urszula", "Wanda", "Ludwika", "Marianna", "Rozalia",
    "Stefania", "Leokadia", "Genowefa", "Kazimiera", "Czesława", "Józefa", "Regina"
]

SURNAMES = [
    "Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski",
    "Zieliński", "Szymański", "Woźniak", "Dąbrowski", "Kozłowski", "Jankowski", "Mazur",
    "Wojciechowski", "Kwiatkowski", "Krawczyk", "Kaczmarek", "Piotrowski", "Grabowski",
    "Zając", "Pawłowski", "Michalski", "Król", "Wieczorek", "Jabłoński", "Wróbel", "Nowakowski",
    "Majewski", "Olszewski", "Stępień", "Malinowski", "Jaworski", "Adamczyk", "Dudek", "Górski",
    "Pawlak", "Sikora", "Walczak", "Baran"
]

# Includes historical German variations of Polish cities for scenario testing (e.g., Posen -> Poznań)
PLACES = [
    "Warszawa", "Kraków", "Posen", "Danzig", "Breslau", "Łódź", "Lublin", "Stettin", "Bromberg",
    "Katowice", "Białystok", "Gdynia", "Częstochowa", "Radom", "Sosnowiec", "Thorn", "Kielce",
    "Rzeszów", "Gliwice", "Olsztyn", "Lipce", "Bronowice", "Zalipie", "Chochołów", "Sromowce",
    "Lanckorona", "Złoty Potok", "Supraśl", "Tykocin", "Biecz", "Kazimierz Dolny", "Sandomierz",
    "Zwierzyniec", "Reszel", "Chełmno", "Pszczyna", "Cieszyn", "Sanok", "Krynica", "Wisła"
]

# Nones are intentionally injected to simulate missing data (approx. 20% sparsity)
OCCUPATIONS = [
    "Farmer", "Blacksmith", "Shoemaker", "Tailor", "Carpenter", "Merchant", "Teacher", "Doctor", "Soldier",
    "Baker", "Butcher", "Weaver", "Miller", "Fisherman", "Potter", "Mason", "Scribe", "Priest", "Innkeeper",
    "Tanner", "Cooper", "Wheelwright", "Miner", "Hunter", "Shepherd", "Clerk", "Judge", "Lawyer", "Artist",
    None, None, None, None, None, None
]

CAUSES_OF_DEATH = [
    "Infectious disease", "Accident", "Pneumonia", "Fever", "Unknown", "Consumption", "Heart failure",
    "Stroke", "Cancer", "Drowning", "War casualty", "Plague", "Smallpox", "Cholera", "Typhus",
    "Dysentery", "Influenza", "Starvation", "Fire", "Murder", "Dropsy", "Apoplexy",
    None, None, None, None
]