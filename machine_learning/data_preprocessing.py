import pandas as pd

def inspect_data(df: pd.DataFrame) -> None:
    """
    Affiche des informations de base sur le DataFrame.
    """
    print("\n----- Vérification des données -----")
    print(df.info())

    print("\n----- Statistiques descriptives -----")
    print(df.describe().round(2))

def select_features(df: pd.DataFrame, features=None) -> pd.DataFrame:
    """
    Sélectionne les features à utiliser pour le modèle.
    """
    if features is None:
        features = ["error_rate_pct", "test_volume"]

    print(f"\nFeatures utilisées: {features}")
    return df[features]