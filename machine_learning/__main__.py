from data_loading import load_data
from data_preprocessing import inspect_data, select_features
from model_isolation_forest import train_isolation_forest, apply_model
from model_results import summarize_results, export_results
from visualization import plot_anomalies

def main():
    # Chargement des données
    try:
        df = load_data('regles_ml.csv')
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        print(f"Erreur lors du chargement des données : {e}")
        return
    
    # Vérification des données
    inspect_data(df)

    # Sélection des features
    feature_cols = ["error_rate_pct", "test_volume"]
    X = select_features(df, feature_cols)

    # Entraînement du modèle
    model = train_isolation_forest(X, contamination=0.20)

    # Application du modèle
    df_scored = apply_model(df, X, model)

    # Résumés + anomalies
    anomalies = summarize_results(df_scored, feature_cols)

    # Export CSV
    export_results(df_scored, "regles_anomalies.csv")

    # Visualisations
    plot_anomalies(df_scored, anomalies, "anomalies_regles_barchart.png")

if __name__ == "__main__":
    main()    