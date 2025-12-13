import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

FIG_DIR = Path(__file__).parent / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

def plot_anomalies(df: pd.DataFrame, anomalies: pd.DataFrame, filename: str = "anomalies_regles_barchart.png") -> None:
    """
    Génère le nuage de points global + bar chart des règles anormales.
    """
    output_path = FIG_DIR / filename
    
    n_anomalies = len(anomalies)

    plt.figure(figsize=(14, 5))

    # 1) Nuage de points global
    plt.subplot(1, 2, 1)
    sns.scatterplot(
        data=df,
        x="error_rate_pct",
        y="test_volume",
        hue="anomaly",
        palette={1: "skyblue", -1: "red"},
        s=200,
    )
    plt.title(f"Détection anomalies ({n_anomalies} règles problématiques)")
    plt.xlabel("Taux d'erreur LLM (%)")
    plt.ylabel("Volume de tests")
    plt.legend(title="Statut", labels=["Normale", "Anomalie"])

        # 2) Bar chart des règles anormales
    plt.subplot(1, 2, 2)
    anomalies_sorted = anomalies.sort_values("error_rate_pct", ascending=False)
    sns.barplot(
        data=anomalies_sorted,
        x="error_rate_pct",
        y="rule_name",
        color="indianred",
    )
    plt.title("Règles anormales (taux d'erreur par règle)")
    plt.xlabel("Taux d'erreur LLM (%)")
    plt.ylabel("Règle")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.show()

    print(f"  - {output_path}")
