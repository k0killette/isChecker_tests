import pandas as pd

# ----------------------------------
# Fonction pour vérifier les données
# ----------------------------------
def check_data(df: pd.DataFrame) -> None:
    """
    Vérifie la qualité des données du DataFrame et affiche les informations nécessaires
    :param df: DataFrame à vérifier
    """
    
    # Vérification des types de données et des valeurs manquantes
    print("\n----- Vérification des données -----")
    print(df.info())
    
    if df.isna().any().any():
        na_counts = df.isna().sum()
        raise ValueError(
            f"Erreur: Le DataFrame contient des valeurs manquantes:\n{na_counts}"
        )
    print("Aucune valeur manquante détectée.")

    # Arrondi des colonnes numériques (type 'float64') à deux décimales
    numerical_cols = df.select_dtypes(include=['float64']).columns
    if len(numerical_cols) > 0:
        print(f"\nArrondi des colonnes {list(numerical_cols)} à 2 décimales: ")
    for col in numerical_cols:
        df[col] = df[col].round(2)

# ---------------------------------------
# Fonction pour sélectionner les features
# ---------------------------------------
# Définition des features à utiliser
feature_cols = ['error_rate_pct', 'test_volume']

def select_features(df: pd.DataFrame, features=None) -> pd.DataFrame:
    """
    Sélectionne les features à utiliser pour le modèle
    :param df: DataFrame contenant les données
    :param features: Liste des colonnes à sélectionner
    :return: DataFrame avec les features sélectionnées
    :raises ValueError: si une ou plusieurs colonnes sont manquantes
    """

    # Définition des features à utiliser
    if features is None:
        features = feature_cols
    
    # Vérification que toutes les colonnes existent
    missing = set(features) - set(df.columns)
    if missing:
        raise ValueError(
            f"Erreur: Les colonnes suivantes sont manquantes dans le DataFrame: {missing}"
        )

    print(f"\nFeatures utilisées: {features}")
    return df[features]