import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import List, Dict

# -------------------------------------------------------------
# Fonction pour déterminer la meilleure valeur de contamination
# -------------------------------------------------------------
def contamination_sensitivity_test(
    X: pd.DataFrame,
    contamination_values: List[float] = None,
    n_estimators: int = 200,
    max_samples='auto',
    max_features=1.0,
    random_state: int = 42,
) -> Dict[float, int]:
    """
    Retourne, pour chaque valeur testée du paramètre contamination, le nombre d'anomalies détectées
    :param X : DataFrame de features
    :param contamination_values : liste de valeurs de contamination à tester entre 0 et 0.5 (si plus de la moitié des observations sont anormales, la notion d’outlier perd son sens)
    :param n_estimators : nombre d'arbres dans la forêt
    :param max_samples : nombre d'échantillons utilisés par arbre ('auto', int ou float)
    :param max_features : nombre de features utilisées par arbre (int ou float)
    :param random_state : reproductibilité
    :return : dictionnaire {contamination: nombre_d_anomalies}
    """

    if contamination_values is None:
        contamination_values = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

    results = {}

    print("\n----- Test de sensibilité sur le paramètre contamination -----")
    for value in contamination_values:
        model = IsolationForest(
            contamination=value,
            n_estimators=n_estimators,
            max_samples=max_samples,
            max_features=max_features,
            random_state=random_state,
        )
        model.fit(X)
        preds = model.predict(X)  # -1 = anomalie
        n_anoms = (preds == -1).sum()
        results[value] = n_anoms
        print(f"contamination={value:.2f} → {n_anoms} anomalies détectées")

    return results

# ----- Test de sensibilité sur le paramètre contamination -----
# contamination=0.05 → 3 anomalies détectées
# contamination=0.10 → 6 anomalies détectées
# contamination=0.15 → 9 anomalies détectées
# contamination=0.20 → 12 anomalies détectées
# contamination=0.25 → 14 anomalies détectées
# contamination=0.30 → 17 anomalies détectées
# contamination=0.35 → 20 anomalies détectées
# contamination=0.40 → 23 anomalies détectées
# contamination=0.45 → 26 anomalies détectées
# contamination=0.50 → 28 anomalies détectées
# Le test démontre une relation quasi linéaire entre la valeur de contamination et le nombre d’anomalies détectées : 
# de 3 anomalies pour contamination=0.05 jusqu’à 28 anomalies pour contamination=0.50
# A chaque valeur supérieure de 0.05, le test détecte 2 ou 3 nouvelles anomalies
# Le modèle ordonne bien les règles par degré de suspicion et le seuil de décision dépend surtout de la valeur de contamination
# La valeur 0.20 est un bon compromis pour détecter un nombre raisonnable d’anomalies sans être trop restrictif → on est dans une logique de priorisation 

# ---------------------------------
# Fonction pour entrainer le modèle
# ---------------------------------
def train_isolation_forest(
    X: pd.DataFrame,
    contamination: float = 0.20,    # proportion estimée d'anomalies dans les données
    n_estimators: int = 200,        # nombre d’arbres, par défaut 100 → plus il y en a plus le score est stable mais plus le modèle est lent
    max_samples='auto',             # nombre d’échantillons utilisés par arbre, par défaut 'auto' = min (256, n_samples)
    max_features=1.0,               # nombre de features utilisées par arbre, par défaut 1.0 = toutes les features
    random_state: int = 42,         # pour la reproductibilité des résultats
) -> IsolationForest:
    """
    Entraîne un modèle Isolation Forest sur les features définies (X)
    :param X : DataFrame contenant les features pour l'entraînement
    :param contamination : proportion estimée d'anomalies dans les données
    :param n_estimators : nombre d'arbres dans la forêt
    :param max_samples : nombre d'échantillons utilisés par arbre ('auto', int ou float)
    :param max_features : nombre de features utilisées par arbre (int ou float)
    :param random_state : reproductibilité
    :return : modèle IsolationForest entraîné
    :raises ValueError : si X ou les paramètres sont invalides
    :raises RuntimeError : si l'entraînement échoue
    """
    print("\n----- Entraînement du modèle Isolation Forest -----")
    print(f"Paramètres: contamination={contamination}, "
          f"n_estimators={n_estimators}, max_samples={max_samples}, max_features={max_features}, "
          f"random_state={random_state}")

    try:
        iso_forest = IsolationForest(
            contamination=contamination, 
            n_estimators=n_estimators,   
            max_samples=max_samples, 
            max_features=max_features,  
            random_state=random_state,    
        )
        iso_forest.fit(X)
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'entraînement du modèle IsolationForest: {e}")
    return iso_forest

# ---------------------------------
# Fonction pour appliquer le modèle
# ---------------------------------
def apply_model(
    df: pd.DataFrame, 
    X: pd.DataFrame, 
    model: IsolationForest
) -> pd.DataFrame:
    """
    Applique le modèle au DataFrame et ajoute les colonnes 'anomaly' et 'anomaly_score'
    :param df : DataFrame original contenant les données
    :param X : DataFrame contenant les features pour la prédiction
    :param model : modèle IsolationForest entraîné
    :return : DataFrame avec les colonnes 'anomaly' et 'anomaly_score' ajoutées
    """
    df = df.copy()
    try:
        df['anomaly'] = model.predict(X)               # -1 = anomalie, 1 = normale
        df['anomaly_score'] = model.decision_function(X)
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'application du modèle IsolationForest: {e}")
    return df