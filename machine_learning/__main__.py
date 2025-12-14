from data_loading import load_data
from data_preprocessing import check_data, select_features, feature_cols
from model_isolation_forest import train_isolation_forest, apply_model, contamination_sensitivity_test
from model_results import summarize_results, export_results
from visualization import plot_anomalies

def main():
    try:
        # Chargement des données
        df = load_data('regles_ml.csv')
        # Vérification des données
        check_data(df)
        # Sélection des features
        X = select_features(df, feature_cols)
        # # Test de sensibilité pour le paramètre contamination
        # sensitivity = contamination_sensitivity_test(X)
        # Entraînement du modèle
        model = train_isolation_forest(X, contamination=0.20)
        # Application du modèle
        df_scored = apply_model(df, X, model)
        # Résumés + anomalies
        anomalies = summarize_results(df_scored, feature_cols)
        # Export CSV
        export_results(df_scored, 'regles_anomalies.csv')

    except (FileNotFoundError, RuntimeError, ValueError) as e:
        print(f"Erreur dans le processus : {e}")
        return




    # # Visualisations
    # plot_anomalies(df_scored, anomalies, "anomalies_regles_barchart.png")

if __name__ == "__main__":
    main()    