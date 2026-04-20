"""
Central configuration module for the demographic simulation.
Contains the random seed, scenario parameters for three population scales,
and dictionaries of historical data: names, surnames, places, and occupations.
"""

# A fixed seed guarantees full reproducibility of simulation results
SEED = 748376

# Scenario parameters for each population scale.
# Define scenario-specific genealogical tree depth (LCA/ancestors/descendants),
# simulation start year, number of founding pairs, immigrants, and fertility rate.
SCENARIOS = {
    1000: {
        'lca_path': 8, 'ancestors_depth': 5, 'descendants_depth': 3,
        'start_year': 1650, 'initial_pairs': 19, 'avg_children': 7.1, 'immigrants_per_year': 1
    },
    10000: {
        'lca_path': 12, 'ancestors_depth': 10, 'descendants_depth': 6,
        'start_year': 1400, 'initial_pairs': 63, 'avg_children': 4.99, 'immigrants_per_year': 2
    },
    100000: {
        'lca_path': 16, 'ancestors_depth': 15, 'descendants_depth': 10,
        'start_year': 700, 'initial_pairs': 77, 'avg_children': 4.53, 'immigrants_per_year': 4
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

# Historical places categorized by region (West, North, Greater Poland + Kuyavian-Pomeranian, Central + East, South).
# Includes 6 historical German variations of Polish cities for scenario testing (e.g., Posen -> Poznań)
PLACES = {
    0: [  # West (Lower Silesia + Lubusz + Opole)
        "Breslau", "Legnica", "Wałbrzych", "Jelenia Góra", "Świdnica",
        "Zielona Góra", "Gorzów Wielkopolski", "Opole"
    ],

    1: [  # North (Pomeranian + West Pomeranian + Warmian-Masurian)
        "Danzig", "Gdynia", "Sopot", "Słupsk", "Wejherowo", "Olsztyn", "Malbork", "Chojnice",
        "Stettin", "Koszalin", "Kołobrzeg", "Świnoujście", "Stargard",
        "Elbląg"
    ],

    2: [  # Greater Poland + Kuyavian-Pomeranian
        "Posen", "Gniezno", "Kalisz", "Leszno", "Piła", "Konin", "Śrem",
        "Ostrów Wielkopolski", "Gostyń", "Kościan", "Rawicz", "Września",
        "Bromberg", "Inowrocław", "Włocławek", "Grudziądz", "Thorn"
    ],

    3: [  # Central + East (Masovian + Podlaskie + Lublin + Łódź)
        "Warszawa", "Radom", "Płock", "Ostrołęka", "Siedlce", "Ciechanów",
        "Białystok", "Suwałki", "Łomża",
        "Lublin", "Zamość", "Biała Podlaska", "Chełm",
        "Łódź", "Skierniewice"
    ],

    4: [  # South (Lesser Poland + Subcarpathian + Świętokrzyskie)
        "Kraków", "Tarnów", "Nowy Sącz", "Zakopane", "Bochnia", "Oświęcim",
        "Rzeszów", "Przemyśl", "Krosno", "Tarnobrzeg", "Jasło", "Sanok",
        "Kielce", "Sandomierz", "Ostrowiec Świętokrzyski"
    ]
}

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