import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Définition du chemin du répertoire pour sauvegarder les figures
FIG_DIR = Path(__file__).parent / 'figures'
# Création du répertoire s'il nexiste pas et ignore l'erreur s'il existe déjà
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------
# Fonction pour générer le nuage de points
# ----------------------------------------
def plot_scatter_anomalies(
    df: pd.DataFrame, 
    filename: str = 'anomalies_scatter.png'
) -> None:
    """
    Génère un nuage de points pour  visualiser les anomalies détectées par l'Isolation Forest
    :param df: DataFrame complet avec les résultats du modèle
    :param filename: Nom du fichier image à générer
    :return: None
    Couleurs :
    - #074650 pour les règles normales
    - #FE6DB6 pour les anomalies
    """
    # Définition du chemin complet du fichier image sauvegardé
    output_path = FIG_DIR / filename

    # Définition de la palette de couleurs : 1 = normale, -1 = anomalie
    palette = {1: "#074650", -1: "#FE6DB6"}

    # Création de la figure
    plt.figure(figsize=(7, 6))
    scatterplot=sns.scatterplot(
        data=df,
        x='error_rate_pct',
        y='test_volume',
        hue='anomaly',
        palette=palette,
        s=200,
    )
    # Définition du titre et des labels de la figure
    n_anomalies = (df['anomaly'] == -1).sum()
    plt.title(f"Détection d'anomalies : {n_anomalies} règles problématiques")
    plt.xlabel("Taux d'erreur du LLM (%)")
    plt.ylabel("Volume de tests")
    # Définition d'une légende personnalisée avec deux entrées : Normale et Anomalie
    handles, _ = scatterplot.get_legend_handles_labels()
    anomaly_handle = handles[0]     # anomaly = -1
    normal_handle = handles[1]      # anomaly = 1
    scatterplot.legend(
        handles=[normal_handle, anomaly_handle],
        labels=["Normale", "Anomalie"],
        title="Statut",
        loc="best",                 # Matplotlib place automatiquement la légende là où elle gêne le moins la lecture des données du graphique (position où la légende recouvre le moins les points)
    )

    try:
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
    except Exception as e:
        plt.close()
        raise RuntimeError(f"Erreur lors de la sauvegarde du nuage de points: {e}")

    plt.show()
    plt.close()
    print(f"Figure générée : {output_path}")

# ------------------------------------------------------------------
# Fonction pour générer le bar chart horizontal des règles anormales
# ------------------------------------------------------------------
def plot_barchart_anomalies(
    anomalies: pd.DataFrame,
    filename: str = 'anomalies_regles_barchart.png',
) -> None:
    """
    Génère un bar chart horizontal du taux d'erreur pour les règles anormales
    :param anomalies: DataFrame contenant uniquement les lignes anormales (anomaly == -1)
    :param filename: Nom du fichier image à générer
    :return: None
    Couleur :
    - #6DB6FF pour toutes les barres.
    """
    # Définition du chemin complet du fichier image sauvegardé
    output_path = FIG_DIR / filename

    # Tri des anomalies par error_rate_pct décroissant
    anomalies_sorted = anomalies.sort_values('error_rate_pct', ascending=False)

    # Création de la figure
    plt.figure(figsize=(7, 6))
    sns.barplot(
        data=anomalies_sorted,
        x='error_rate_pct',
        y='rule_name',
        color='#6DB6FF',
    )
    # Définition du titre et des labels de la figure
    plt.title("Taux d'erreur par règle anormale")
    plt.xlabel("Taux d'erreur du LLM (%)")
    plt.ylabel("Règle")

    try:
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
    except Exception as e:
        plt.close()
        raise RuntimeError(f"Erreur lors de la sauvegarde du bar chart: {e}")
    
    plt.show()
    plt.close()
    print(f"Figure générée : {output_path}")
