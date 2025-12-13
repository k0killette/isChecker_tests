import pandas as pd
from sklearn.ensemble import IsolationForest

def train_isolation_forest(X: pd.DataFrame, contamination: float = 0.20) -> IsolationForest:
    """
    Entraîne un modèle Isolation Forest sur les features X.
    """
    iso_forest = IsolationForest(contamination=contamination, random_state=42)
    iso_forest.fit(X)
    return iso_forest

def apply_model(df: pd.DataFrame, X: pd.DataFrame, model: IsolationForest) -> pd.DataFrame:
    """
    Applique le modèle au DataFrame et ajoute les colonnes anomaly et anomaly_score.
    """
    df = df.copy()
    df["anomaly"] = model.predict(X)               # -1 = anomalie, 1 = normale
    df["anomaly_score"] = model.decision_function(X)
    return df