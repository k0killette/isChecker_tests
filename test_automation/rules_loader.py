import json
from pathlib import Path
from typing import Dict, Any

# Chemin vers le dossier 'test_automation' (où on est actuellement)
BASE_DIR = Path(__file__).parent
# Chemin vers le dossier 'rules' (à la racine du projet)
RULES_DIR = BASE_DIR.parent / "rules"

# -----------------------------------------------
# Fonction pour charger un fichier de règles JSON
# -----------------------------------------------
def load_rules_file(json_path: Path) -> dict:
    """
    Charge un fichier de règles JSON et retourne son contenu sous forme de dictionnaire

    :param json_path : chemin du fichier JSON (ex: rules/fr_rules_liste.json)
    :return : dict Python correspondant au contenu du fichier
    :raises RuntimeError : si la lecture ou le parsing JSON échoue
    """
    # Vérification de l'existence du fichier
    if not json_path.exists():
        raise RuntimeError(f"Erreur: Fichier JSON de règles introuvable: {json_path}")

    # Ouverture du fichier avec encodage UTF-8 et chargement du contenu en mémoire
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la lecture du fichier de règle '{json_path}': {e}")

    # Vérification de la structure 
    if not isinstance(data, dict) or "rules" not in data:
        raise RuntimeError(
            f"Structure JSON non reconnue pour '{json_path}'"
        )

    return data

# -----------------------------------------------------------------------
# Fonction pour construire le mapping des règles à partir du contenu JSON
# -----------------------------------------------------------------------
def build_rules_mapping_from_file(data: dict, source_file: str) -> Dict[str, dict]:
    """
    Construit un mapping {rule_name: config} à partir du contenu d'un fichier JSON de règles
    :param data : dict contenant au minimum 'rules': [ {...}, ... ]
    :param source_file : nom du fichier source pour traçabilité
    :return : dict indexé par rule_name
    """
    rules_mapping: Dict[str, dict] = {}

    category = data.get("category")
    language = data.get("language")
    rules = data.get("rules", [])

    for rule in rules:
        # 'name' est la clé qui identifie la règle (correspond à rule_name côté TSV/ML)
        rule_name = rule.get("name")
        if not rule_name:
            continue  # On ignore les règles sans nom

        # On prépare une configuration structurée pour chaque règle
        rules_mapping[str(rule_name)] = {
            "category": category,
            "language": language,
            "name": rule_name,
            "description": rule.get("description"),
            "error_message": rule.get("error_mesg"),
            "regex": rule.get("regex"),
            "prompt_file": rule.get("prompt_file"),
            "prompt_key": rule.get("prompt_key"),
            # On peut aussi récupérer anomaly_score / recommended_method si présents
            "anomaly_score": rule.get("anomaly_score"),
            "recommended_method": rule.get("recommended_method"),
            "source_json": source_file,
        }

    return rules_mapping

# ---------------------------------------------------------
# Fonction pour charger toutes les règles depuis le dossier
# ---------------------------------------------------------
def load_rules_mapping(
    rules_dir: str | Path = RULES_DIR,
) -> Dict[str, dict]:
    """
    Orchestrateur : parcourt tous les fichiers JSON de règles dans rules_dir et construit un mapping global {rule_name: config}
    :param rules_dir : dossier contenant les fichiers JSON de règles (par défaut RULES_DIR)
    :return : dictionnaire global indexé par rule_name
    """
    rules_dir = Path(rules_dir)

    if not rules_dir.exists():
        raise RuntimeError(f"Erreur: Le répertoire des règles {rules_dir} n'existe pas")

    json_files = sorted(rules_dir.glob("*.json"))
    if not json_files:
        print(f"Aucun fichier JSON de règles trouvé dans {rules_dir}")
        return {}

    print("\n----- Chargement des règles depuis les fichiers JSON -----")
    print(f"Répertoire: {rules_dir}")
    print(f"Fichiers trouvés: {[path.name for path in json_files]}")

    global_mapping: Dict[str, dict] = {}

    for json_path in json_files:
        try:
            data = load_rules_file(json_path)
            file_mapping = build_rules_mapping_from_file(data, source_file=json_path.name)

            # Fusion dans le mapping global
            # En cas de doublon de rule_name, la dernière occurrence écrase la précédente
            global_mapping.update(file_mapping)

            print(
                f"  - {json_path.name}: {len(file_mapping)} règles chargées "
                f"(total cumulé: {len(global_mapping)})"
            )
        except RuntimeError as e:
            # On log l'erreur mais on continue avec les autres fichiers
            print(f"Erreur lors du chargement de '{json_path.name}': {e}")

    return global_mapping
