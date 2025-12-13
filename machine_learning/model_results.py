import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def summarize_results(df: pd.DataFrame, feature_cols) -> pd.DataFrame:
    """
    Affiche les anomalies détectées et les statistiques par groupe.
    Retourne le DataFrame des anomalies.
    """
    print("\n" + "=" * 60)
    print("RÈGLES ANORMALES DÉTECTÉES")
    print("=" * 60)
    anomalies = df[df["anomaly"] == -1].sort_values("anomaly_score")
    print(
        anomalies[
            ["rule_name", "family_name", "error_rate_pct", "test_volume", "anomaly_score"]
        ].round(2)
    )

    print("\n" + "=" * 60)
    print("STATISTIQUES PAR GROUPE")
    print("=" * 60)
    stats = df.groupby("anomaly")[feature_cols + ["anomaly_score"]].mean().round(2)
    print(stats)

    n_anomalies = len(anomalies)
    print(f"\n{n_anomalies} anomalies détectées sur {len(df)} règles ({n_anomalies/len(df)*100:.1f} %)")

    return anomalies    

def export_results(df: pd.DataFrame, filename: str = "regles_anomalies.csv") -> None:
    """
    Exporte le DataFrame complet avec statut d'anomalie en CSV.
    """
    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False)
    print("\nFichiers générés :")
    print(f"  - {path}")