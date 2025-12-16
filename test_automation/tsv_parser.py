# Exploitation des rapports TSV

import pandas as pd
from pathlib import Path

# Chemin vers le dossier test_automation
BASE_DIR = Path(__file__).parent   
# Chemin vers le dossier tsv_reports       
TSV_DIR = BASE_DIR.parent / "tsv_reports" 

# ------------------------------------
# Fonction pour charger un rapport TSV
# ------------------------------------
def load_tsv_report(filename: str) -> pd.DataFrame:
    """
    Charge un rapport TSV isChecker, filtre sur les lignes en français (lignes ayant la paire 'lang=FR') et retourne un DataFrame structuré
    :param filename: chemin relatif vers le fichier TSV à charger
    :return : DataFrame pandas avec les colonnes renommées pour correspondre à la base de données
    """
    path = TSV_DIR / filename

    # Vérification de l'existence du fichier
    if not path.exists():
        raise FileNotFoundError(f"Fichier TSV introuvable: {path}")

    # Lecture du fichier TSV 
    # Une ligne contient plusieurs paires "clé=valeur" séparées par des tabulations
    df_tsv = pd.read_csv(
        path,
        sep="\t",
        header=None,
        comment="#",
        dtype=str,
        keep_default_na=False, # Evite la conversion automatique des chaînes vides en NaN
    )

    # Récupération des valeurs de chaque clé par ligne
    records = []
    for _, row in df_tsv.iterrows():
        record: dict[str, str] = {}
        for cell in row:
            if not cell:
                continue
            if "=" in cell:
                key, value = cell.split("=", 1)
                record[key] = value
        if record:
            records.append(record)

    df_tsv = pd.DataFrame(records)

    # Filtrage sur les lignes en langue française uniquement
    if "lang" in df_tsv.columns:
        df_tsv = df_tsv[df_tsv["lang"] == "FR"]
        
    # Réinitialisation des index
    # Après le filtrage l’index garde les anciens numéros de lignes (0, 2, 5, 7, …)
    # Avec reset_index(drop=True) on remet un index propre de 0 à n-1
    df_tsv = df_tsv.reset_index(drop=True)

    # Suppresion de la colonne 'severity'
    if "severity" in df_tsv.columns:
        df_tsv = df_tsv.drop(columns=["severity"])

    # Création de la colonne 'ischecker_status' à partir de la présence ou non d'un message dans 'description'
    # Si 'description' est vide → 'no_violation', sinon 'violation'
    if "description" in df_tsv.columns:
        df_tsv["ischecker_status"] = df_tsv["description"].apply(
            lambda x: "no_violation" if x == "" else "violation"
        )
    else:
        # Renvoie une erreur si la colonne n'existe pas
        raise ValueError(
            "Erreur: La colonne 'description' est absente du rapport TSV, impossible de déterminer le statut isChecker."
        )
    
    # Renommage des noms de colonnes pour correspondre à la base de données
    df_tsv = df_tsv.rename(
        columns={
            "ruleName": "rule_name",
            "lang": "language",
            "description": "ischecker_message",
        }
    )

    print(f"----- Aperçu du rapport TSV chargé depuis {path} -----")
    print(df_tsv.head())

    return df_tsv
