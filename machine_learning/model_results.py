import pandas as pd
from pathlib import Path

# Définition du chemin du répertoire de sortie pour les fichiers générés
# Path(__file__).parent : répertoire du fichier courant (ici module machine_learning)
# / 'data' / 'output'   : sous-dossier où les CSV générés seront stockés 
# parents=True : crée les dossiers parents s'ils n'existent pas 
# exist_ok=True : ne lève pas d'erreur si le dossier existe déjà
OUTPUT_DIR = Path(__file__).parent / 'data' / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------
# Fonction pour résumer et afficher les résultats
# -----------------------------------------------
def summarize_results(
    df: pd.DataFrame, 
    feature_cols
) -> pd.DataFrame:
    """
    Affiche les anomalies détectées et les statistiques par groupe, retourne le DataFrame des anomalies
    :param df: DataFrame complet avec les résultats du modèle 
    :param feature_cols: Liste des colonnes utilisées comme features par le modèle
    :return: DataFrame contenant uniquement les lignes anormales (anomaly == -1)
    """
    
    print("\n----- Règles anormales détectées : -----")    
    # Sélection des lignes marquées comme anomalies (-1) et tri par score croissant
    anomalies = df[df['anomaly'] == -1].sort_values('anomaly_score')
 
    if anomalies.empty:
        print("Aucune anomalie détectée")
    else:
        # Affichage des principales colonnes + arrondi à 2 décimales
        cols = ['rule_name', 'family_name', 'error_rate_pct', 'test_volume', 'anomaly_score']
        print(anomalies[cols].round(2))

    print("\n----- Statistiques par groupe : -----")    
    # Calcul des moyennes par groupe normal / anormal
    stats = df.groupby('anomaly')[feature_cols + ['anomaly_score']].mean().round(2)
    print(stats)

    # Nombre d'anomalies détectées et pourcentage
    n_anomalies = len(anomalies)
    print(f"\n{n_anomalies} anomalies détectées sur {len(df)} règles ({n_anomalies/len(df)*100:.1f} %)")

    return anomalies    

# ----------------------------------------------------
# Fonction pour exporter les résultats complets en CSV
# ----------------------------------------------------
def export_results(
    df: pd.DataFrame, 
    filename: str = 'regles_anomalies.csv'
) -> None:
    """
    Exporte le DataFrame complet en CSV dans le répertoire de sortie défini
    :param df: DataFrame complet avec les résultats du modèle
    :param filename: Nom du fichier CSV à générer
    :return: None
    """
    path = OUTPUT_DIR / filename

    # Export en CSV sans l'index pandas
    try:
        df.to_csv(path, index=False)
    except Exception as e:
        print(f"Erreur lors de l'exportation du fichier CSV : {e}")
        return
    print("\nFichiers générés :")
    print(f"  - {path}")