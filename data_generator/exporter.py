import os
import csv
from typing import Dict
from models import Person, Family

class DataExporter:
    """
    Handles serialization of in-memory simulation objects (Person, Family) to CSV files
    in two distinct formats: relational (PostgreSQL) and graph (Neo4j).
    Each format is optimized for the bulk import tooling of the respective database.
    """
    def __init__(self, people: Dict[int, Person], families: Dict[int, Family], target_population: int, output_dir: str):
        self.people = people
        self.families = families
        self.target_population = target_population
        self.output_dir = output_dir

    def export_to_postgres_csv(self):
        """
        Generates three CSV files conforming to the relational schema:
        - people.csv — person entities
        - families.csv — family units (marriages/unions)
        - family_children.csv — join table for the many-to-many parent-child relationship
        """
        pg_dir = os.path.join(self.output_dir, 'postgres')
        os.makedirs(pg_dir, exist_ok=True)

        with open(os.path.join(pg_dir, 'people.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(
                ['id', 'given_name', 'surname', 'sex', 'is_deceased', 'birth_place', 'birth_date', 'death_place',
                 'death_date', 'cause_of_death', 'burial_place', 'occupation'])
            
            for p in self.people.values():
                writer.writerow([
                    p.id, p.given_name, p.surname, p.sex, 1 if p.is_deceased else 0,
                    p.birth_place, p.birth_date.isoformat() if p.birth_date else '',
                    p.death_place if p.is_deceased else '',
                    p.death_date.isoformat() if p.death_date else '',
                    p.cause_of_death if p.is_deceased else '',
                    p.burial_place if p.is_deceased else '',
                    p.occupation
                ])

        with open(os.path.join(pg_dir, 'families.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'status', 'marriage_date', 'marriage_place', 'husband_id', 'wife_id'])
            
            for fam in self.families.values():
                writer.writerow([
                    fam.id, fam.status, fam.marriage_date.isoformat() if fam.marriage_date else '',
                    fam.marriage_place, fam.husband_id, fam.wife_id
                ])

        # The parent-child relationship is split into a separate table to avoid
        # multi-valued columns in families (normalizing to 1NF)
        with open(os.path.join(pg_dir, 'family_children.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['family_id', 'child_id', 'relationship_type'])
            for fam in self.families.values():
                for child_dict in fam.children:
                    writer.writerow([fam.id, child_dict['id'], child_dict['type']])

        print(f"[{self.target_population}] PostgreSQL CSV export complete → {pg_dir}/")

    def export_to_neo4j_csv(self):
        """
        Generates CSV files conforming to the neo4j-admin import format:
        node files (nodes_person, nodes_family) and separate relationship files
        for each edge type (HUSBAND_OF, WIFE_OF, HAS_BIOLOGICAL_CHILD, HAS_ADOPTED_CHILD, etc.).
        Separating relationship types into individual files is required by the Neo4j bulk import tool.
        """
        neo4j_dir = os.path.join(self.output_dir, 'neo4j')
        os.makedirs(neo4j_dir, exist_ok=True)

        with open(os.path.join(neo4j_dir, 'nodes_person.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Property types are encoded directly in the headers — required by neo4j-admin import
            writer.writerow([
                'id:ID(Person)', 'givenName:STRING', 'surname:STRING', 'sex:STRING',
                'isDeceased:BOOLEAN', 'birthPlace:STRING', 'birthDate:DATE', 'deathPlace:STRING',
                'deathDate:DATE', 'causeOfDeath:STRING', 'burialPlace:STRING', 'occupation:STRING', ':LABEL'
            ])
            for p in self.people.values():
                writer.writerow([
                    p.id, p.given_name, p.surname, p.sex, 'true' if p.is_deceased else 'false',
                    p.birth_place, p.birth_date.isoformat() if p.birth_date else '',
                    p.death_place if p.is_deceased else '', p.death_date.isoformat() if p.death_date else '',
                    p.cause_of_death if p.is_deceased else '', p.burial_place if p.is_deceased else '',
                    p.occupation if p.occupation else '', 'Person'
                ])

        with open(os.path.join(neo4j_dir, 'nodes_family.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id:ID(Family)', 'status:STRING', 'marriageDate:DATE', 'marriagePlace:STRING', ':LABEL'])
            for fam in self.families.values():
                writer.writerow([
                    fam.id, fam.status, fam.marriage_date.isoformat() if fam.marriage_date else '',
                    fam.marriage_place, 'Family'
                ])

        # Each relationship type goes into its own file — a requirement of neo4j-admin import
        with open(os.path.join(neo4j_dir, 'rels_husband_of.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([':START_ID(Person)', ':END_ID(Family)', ':TYPE'])
            for fam in self.families.values():
                if fam.husband_id:
                    writer.writerow([fam.husband_id, fam.id, 'HUSBAND_OF'])

        with open(os.path.join(neo4j_dir, 'rels_wife_of.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([':START_ID(Person)', ':END_ID(Family)', ':TYPE'])
            for fam in self.families.values():
                if fam.wife_id:
                    writer.writerow([fam.wife_id, fam.id, 'WIFE_OF'])

        child_files = {}
        child_writers = {}

        try:
            for fam in self.families.values():
                for child_dict in fam.children:
                    rel_type_raw = child_dict['type'].upper()
                    neo4j_rel_type = f"HAS_{rel_type_raw}_CHILD"

                    if neo4j_rel_type not in child_writers:
                        filename = f"rels_{neo4j_rel_type.lower()}.csv"
                        f = open(os.path.join(neo4j_dir, filename), 'w', newline='', encoding='utf-8')
                        child_files[neo4j_rel_type] = f
                        writer = csv.writer(f)
                        writer.writerow([':START_ID(Family)', ':END_ID(Person)', ':TYPE'])
                        child_writers[neo4j_rel_type] = writer

                    child_writers[neo4j_rel_type].writerow([fam.id, child_dict['id'], neo4j_rel_type])
        finally:
            for f in child_files.values():
                f.close()

        print(f"[{self.target_population}] Neo4j CSV export complete → {neo4j_dir}/")