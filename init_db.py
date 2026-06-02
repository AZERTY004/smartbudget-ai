import sqlite3

# Connexion à la base (crée le fichier s'il n'existe pas)
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Création de la table des dépenses
cursor.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    montant REAL NOT NULL,
    categorie TEXT NOT NULL,
    description TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()
print("Base de données initialisée avec succès (fichier database.db créé) !")