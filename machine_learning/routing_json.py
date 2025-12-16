import pandas as pd
import json
from pathlib import Path
from typing import Dict

# Définition des chemins de base
# Dossier du module machine_learning
BASE_DIR = Path(__file__).parent
# Dossier des fichiers JSON de règles, à la racine du projet
RULES_DIR = BASE_DIR.parent / 'rules'

# ------------------------------------------------
# Fonction pour décider la méthode de vérification
# ------------------------------------------------
def decide_recommended_method(
    anomaly_score: float,
    parsing_confidence: float | None = None,
) -> str:
    """
    Détermine la méthode de vérification recommandée à partir de 'anomaly_score' et de 'parsing_confidence' (si disponible)
    Seuils définis :
    - anomaly_score < -0.05 → REGEX
    - anomaly_score > +0.05 → LLM
    - -0.05 =< score =< +0.05 → LLM si parsing_confidence > 0.8 (sinon REGEX)
    :param anomaly_score: Score d'anomalie (float)
    :param parsing_confidence: Confiance de parsing (float entre 0 et 1) ou None
    :return: "REGEX" ou "LLM"
    """
    if anomaly_score < -0.05:
        return "REGEX"
    if anomaly_score > 0.05:
        return "LLM"
    if parsing_confidence is not None and parsing_confidence > 0.8:
        return "LLM"
    return "REGEX"

# -----------------------------------
# Fonction pour construire le mapping
# -----------------------------------
def build_mapping(
    df_scored: pd.DataFrame,
    rule_col: str = 'rule_name',
    score_col: str = 'anomaly_score',
    parsing_conf_col: str = 'parsing_confidence',
) -> Dict[str, dict]:
    """
    Construit un mapping de la forme :
    {
        'rule_name1': {'anomaly_score': ..., 'parsing_confidence': ...},
        'rule_name2': {...},
        ...
    }
    à partir du DataFrame df_scored
    :param df_scored: DataFrame contenant 'rule_name', 'anomaly_score' (et éventuellement 'parsing_confidence')
    :return: dict indexé par 'rule_name'
    :raises ValueError: si des colonnes obligatoires sont manquantes ou si le DataFrame est vide
    """
    # Vérification de l'existence de df_scored et de son contenu
    if df_scored is None or df_scored.empty:
        raise ValueError("Erreur: df_scored est vide ou None dans build_mapping")

    # Vérification de la présence des colonnes nécessaires
    required_cols = {rule_col, score_col}
    missing = required_cols - set(df_scored.columns)
    if missing:
        raise ValueError(
            f"Erreur: Colonnes manquantes dans df_scored: {missing}"
        )
    
    # Présence de parsing_confidence (optionnelle)
    has_parsing_conf = parsing_conf_col in df_scored.columns

    # Construction du mapping
    mapping: Dict[str, dict] = {}
    for _, row in df_scored.iterrows():
        rule_name = row[rule_col]
        score = float(row[score_col])
        parsing_conf = float(row[parsing_conf_col]) if has_parsing_conf else None

        mapping[str(rule_name)] = {
            'anomaly_score': score,
            'parsing_confidence': parsing_conf,
        }

    return mapping

# -----------------------------------------------------
# Fonction pour mettre à jour un fichier JSON de règles
# -----------------------------------------------------
def update_rules_file(
    json_path: Path,
    scores_mapping: Dict[str, dict],
    rule_name_key: str = 'name',
) -> None:
    """
    Met à jour un fichier JSON de règles en ajoutant les champs 'anomaly_score' et 'recommended_method' pour chaque règle identifiée par rule_name_key
    :param json_path: chemin du fichier JSON (ex: ./rules/fr_rules_liste.json)
    :param scores_mapping: dictionnaire {rule_name: {...}} construit par build_mapping
    :param rule_name_key: clé portant le nom de la règle dans le JSON (ici: 'name')
    :raises RuntimeError: si la lecture, la vérification de structure ou l'écriture du JSON échoue
    """
    # Vérification de l'existence du fichier JSON
    if not json_path.exists():
        raise RuntimeError(f"Erreur: Fichier JSON introuvable: {json_path}")

    # Ouverture du fichier JSON et chargement des données en mémoire
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la lecture du JSON '{json_path}': {e}")

    # Vérification de la structure du fichier JSON
    # - option 1 : data est un objet dict qui contient une clé 'rules' qui contient la liste des règles (scénario ici)
    # - option 2 : data est une liste de règles
    if isinstance(data, dict) and 'rules' in data:
        rules = data['rules']
    elif isinstance(data, list):
        rules = data
    else:
        raise RuntimeError(f"Structure JSON non reconnue pour '{json_path}'")

    # Définition d'un compteur pour suivre le nombre de règles mises à jour ou manquantes (donc ignorées)
    updated_count = 0
    missing_count = 0

    for rule in rules:
        # Récupération du nom de la règle dans le JSON
        rule_name = rule.get(rule_name_key)
        # Si le nom d'une règle n'est pas trouvé on ajoute 1 au compteur de règles manquantes et on passe à la suivante
        if rule_name is None:
            missing_count += 1
            continue

        # Si la règle a été trouvée on récupère le score associé 
        score_info = scores_mapping.get(str(rule_name))
        # Si pas de score trouvé pour la règle on ajoute 1 au compteur de règles manquantes et on passe à la suivante
        if not score_info:
            missing_count += 1
            continue
        
        # Récupération des scores
        anomaly_score = score_info['anomaly_score']
        parsing_conf = score_info['parsing_confidence']

        # Calcul de la méthode recommandée REGEX ou LLM
        recommended_method = decide_recommended_method(anomaly_score, parsing_conf)

        # Mise à jour des champs dans la règle JSON
        rule['anomaly_score'] = anomaly_score
        rule['recommended_method'] = recommended_method

        # Suppression du champs 'llm_required' s'il existe car obsolète avec le mapping
        if 'llm_required' in rule:
            rule.pop('llm_required')
        
        # Incrémentation du compteur des règles mises à jour
        updated_count += 1

    # Si le JSON est un dict avec une clé 'rules', on remet la liste modifiée dedans par sécurité
    if isinstance(data, dict) and 'rules' in data:
        data['rules'] = rules
    
    # Réécriture du fichier JSON à jour    
    try:
        with json_path.open("w", encoding="utf-8") as f:        # On ouvre le fichier en écriture pour pouvoir remplacer le contenu
            json.dump(data, f, ensure_ascii=False, indent=2)    # On sérialise l’objet Python 'data' en JSON bien formaté avec conservation des caractères accentués et indentation
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'écriture du JSON '{json_path}': {e}")

    print(
        f"Fichier mis à jour: {json_path.name} "
        f"(règles mises à jour: {updated_count}, règles non trouvées: {missing_count})"
    )

# ---------------------------------------------------------------------------
# Fonction pour orchestrer la mise à jour de tous les fichiers JSON de règles
# ---------------------------------------------------------------------------
def update_json_rules_routing(
    df_scored: pd.DataFrame,
    json_dir: str | Path = RULES_DIR,
    rule_name_key: str = "name",
) -> None:
    """
    Orchestre la mise à jour globale de tous les fichiers JSON de règles dans le répertoire json_dir :
    - vérifie que le répertoire JSON existe
    - construit le mapping {rule_name: scores} à partir de df_scored
    - parcourt tous les fichiers JSON du répertoire json_dir
    - met à jour anomaly_score et recommended_method dans chaque fichier

    :param df_scored: DataFrame complet après scoring (anomaly, anomaly_score, ...)
    :param json_dir: dossier contenant les fichiers de règles (ici : 'rules')
    :param rule_name_key: clé portant le nom de la règle dans les JSON (ici : 'name')
    """
    # Normalisation du chemin en objet Path
    json_dir = Path(json_dir)

    # Vérification que le répertoire JSON existe
    if not json_dir.exists():
        raise RuntimeError(f"Erreur: Le répertoire JSON n'existe pas: {json_dir}")

    # Construction du mapping global à partir de df_scored
    scores_mapping = build_mapping(df_scored)

    # Recherche de tous les fichiers avec l'extension '.json' dans le dossier
    json_files = sorted(json_dir.glob('*.json'))
    if not json_files:
        print(f"Aucun fichier JSON trouvé dans {json_dir}.")
        return

    print("\n----- Mise à jour des fichiers JSON de règles -----")
    print(f"Répertoire: {json_dir}")
    print(f"Fichiers trouvés: {[file.name for file in json_files]}")

    # Parcourt chaque fichier JSON et le met à jour indépendamment
    for json_path in json_files:
        try:
            update_rules_file(json_path, scores_mapping, rule_name_key=rule_name_key)
        except RuntimeError as e:
            # Logue l'erreur mais continue avec les autres fichiers
            print(f"Erreur lors de la mise à jour de '{json_path.name}': {e}")
