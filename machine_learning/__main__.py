from data_loading import load_data
from data_preprocessing import check_data, select_features, feature_cols
from model_isolation_forest import train_isolation_forest, apply_model, contamination_sensitivity_test
from model_results import summarize_results, export_results
from visualization import plot_scatter_anomalies, plot_barchart_anomalies
from routing_json import update_json_rules_routing

def main():
    try:
        # Chargement des données
        df = load_data('regles_ml.csv')
        # Vérification des données
        check_data(df)
        # Sélection des features
        X = select_features(df, feature_cols)
        # Test de sensibilité pour le paramètre contamination
        sensitivity = contamination_sensitivity_test(X)
        # Entraînement du modèle
        model = train_isolation_forest(X, contamination=0.20)
        # Application du modèle
        df_scored = apply_model(df, X, model)
        # Résumés + anomalies
        anomalies = summarize_results(df_scored, feature_cols)
        # Export CSV
        export_results(df_scored, 'regles_anomalies.csv')
        # Visualisations
        plot_scatter_anomalies(df_scored, 'anomalies_scatter.png')
        plot_barchart_anomalies(anomalies, 'anomalies_regles_barchart.png')
        # Routage construit à partir de l'anomaly_score
        update_json_rules_routing(df_scored)

    except (FileNotFoundError, RuntimeError, ValueError) as e:
        print(f"Erreur dans le processus : {e}")
        return

if __name__ == "__main__":
    main()    