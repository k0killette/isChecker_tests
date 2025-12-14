import pandas as pd
from pathlib import Path

# Définition du chemin du répertoire où se trouvent les données
DATA_DIR = Path(__file__).parent / 'data' / 'input'

# ---------------------------------
# Fonction pour charger les données
# ---------------------------------
def load_data(filename: str = 'regles_ml.csv') -> pd.DataFrame:
    """
    Charge les données des règles depuis le fichier CSV spécifié
    :param filename: Nom du fichier CSV dans le répertoire
    :return: DataFrame pandas contenant les données
    """

    # Construction du chemin vers le fichier CSV
    input_path = DATA_DIR / filename

    # Vérification de l'existence du fichier
    if not input_path.exists():
        raise FileNotFoundError(f"Erreur: Le fichier '{input_path}' est introuvable.")
    
    # Lecture du fichier CSV avec encodage UTF-8
    try:
        df = pd.read_csv(input_path, encoding='utf-8')
    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement du fichier '{input_path}': {e}")
    
    # Vérification du contenu attendu du fichier
    if df.empty:
        raise ValueError(f"Erreur: Le fichier '{input_path}' est vide.")
    required_cols = {'rule_name', 'family_name', 'error_rate_pct', 'test_volume'}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Erreur: Il manque des colonnes dans le fichier '{input_path}' : {missing}")
    
    print(f"Données correctement chargées depuis: {input_path}")

    # Affichage d'un aperçu des données chargées
    print("\n----- Aperçu des données -----")
    print(df.head())
    print(f"\nDataset: {len(df)} règles analysées")
    
    return df
