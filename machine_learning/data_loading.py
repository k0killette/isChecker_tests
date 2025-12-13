import pandas as pd
from pathlib import Path

# Définition du chemin du répertoire où se trouvent les données
DATA_DIR = Path(__file__).parent / "data" / "input"

# Fonction pour charger les données
def load_data(filename: str = "regles_ml.csv") -> pd.DataFrame:
    """
    Charge les données des règles depuis le fichier CSV spécifié
    """
    # Construction du chemin vers le fichier CSV
    input_path = DATA_DIR / filename
    # Lecture du fichier CSV avec encodage UTF-8
    df = pd.read_csv(input_path, encoding="utf-8")
    print(f"Chargement des données depuis: {input_path}")
    # Affichage d'un aperçu des données chargées
    print("\n----- Aperçu des données -----")
    print(df.head())
    print(f"\nDataset: {len(df)} règles analysées")
    return df