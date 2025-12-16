# ------------------------------
# Importation des librairies
# ------------------------------

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import IsolationForest

# ------------------------------
# Chargement des données
# ------------------------------

# Chargement des données depuis le fichier CSV
df = pd.read_csv('regles_ml.csv', encoding="utf-8")
print(f"\nDonnées correctement chargées depuis 'regles_ml.csv'")
print("Erreur: Le fichier 'regles_ml.csv' est introuvable.")
        
# Affichage d'un aperçu des données
print("Aperçu des données:")
print(df.head())
print(f"\nDataset: {len(df)} règles analysées")

# ------------------------------
# Vérfication des données
# ------------------------------
print("\n" + "="*50)
print("VERIFICATION DES DONNEES")
print("="*50)

# Vérification des types de données et des valeurs manquantes
print("\n----- Vérification des données: -----")
print(df.info())

# Arrondi de error_rate_pct à deux décimales
df['error_rate_pct'] = df['error_rate_pct'].round(2)

# ------------------------------
# Features à utiliser
# ------------------------------

features = ['error_rate_pct', 'test_volume']  
print(f"\nFeatures utilisées: {features}")

X = df[features]

# ------------------------------
# Algorithme Isolation Forest pour détecter les anomalies
# ------------------------------

# # Test sensibilité
# for contam in [0.10, 0.20, 0.30]:
#     iso_forest = IsolationForest(contamination=contam, random_state=42)
#     preds = iso_forest.fit_predict(X)
#     print(f"contamination={contam}: {sum(preds==-1)} anomalies")

# iso_forest = IsolationForest(contamination='auto', random_state=42)

iso_forest = IsolationForest(contamination=0.20, random_state=42)   # ~20% d'anomalies attendues
df['anomaly'] = iso_forest.fit_predict(X)                           # -1 = anomalie, 1 = normale
df['anomaly_score'] = iso_forest.decision_function(X)               # Score d'anomalie (-1 à 1)

# ------------------------------
# Résultats
# ------------------------------

print("\n" + "="*60)
print("RÈGLES ANORMALES DÉTECTÉES")
print("="*60)
anomalies = df[df['anomaly'] == -1].sort_values('anomaly_score')
print(anomalies[['rule_name', 'family_name', 'error_rate_pct', 'test_volume', 'anomaly_score']].round(2))

print("\n" + "="*60)
print("STATISTIQUES PAR GROUPE")
print("="*60)
stats = df.groupby('anomaly')[features + ['anomaly_score']].mean().round(2)
print(stats)

n_anomalies = len(anomalies)
print(f"\n {n_anomalies} anomalies détectées sur {len(df)} règles ({n_anomalies/len(df)*100:.1f}%)")

# ------------------------------
# Génération d'un fichier CSV 
# ------------------------------

df.to_csv('regles_anomalies.csv', index=False)
print(f"\n Fichier regles_anomalies.csv généré")

# ------------------------------
# Visualisations
# ------------------------------

plt.figure(figsize=(14, 5))

# Nuage de points 
plt.subplot(1, 2, 1)
sns.scatterplot(
    data=df, 
    x='error_rate_pct', 
    y='test_volume',
    hue='anomaly', 
    palette={1: 'skyblue', -1: 'red'}, 
    s=200
)
plt.title(f'Détection anomalies ({n_anomalies} règles problématiques)')
plt.xlabel('Taux d\'erreur LLM (%)')
plt.ylabel('Volume de tests')
plt.legend(title='Statut', labels=['Normale', 'Anomalie'])

# Histogramme des scores d'anomalie
# plt.subplot(1, 2, 2)
# sns.histplot(data=df, x='anomaly_score', hue='anomaly', bins=15, alpha=0.7)
# plt.title('Distribution scores anomalies')
# plt.xlabel('Score anomalie (-1 à 1)')
# plt.ylabel('Nombre de règles')

# Bar chart des règles anormales (top 12)
plt.subplot(1, 2, 2)
# On trie les anomalies par error_rate_pct décroissant
anomalies_sorted = anomalies.sort_values('error_rate_pct', ascending=False)
sns.barplot(
    data=anomalies_sorted,
    x='error_rate_pct',
    y='rule_name',
    color='indianred'
)
plt.title("Règles anormales (taux d'erreur par règle)")
plt.xlabel("Taux d'erreur LLM (%)")
plt.ylabel("Règle")

plt.tight_layout()
plt.savefig('anomalies_regles_barchart.png', dpi=300, bbox_inches='tight')
plt.show()
