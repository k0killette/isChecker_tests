import pandas as pd

# Fonctions utilitaires du projet
from test_automation.tsv_parser import load_tsv_report, load_all_tsv_reports
from test_automation.rules_loader import load_rules_mapping
from prompts import PROMPTS_MAPPING
from test_automation.llm_client import call_llama_for_test
from test_automation.parsing_llm_responses import parse_llm_response_for_test
from test_automation.comparator import add_comparison_columns, compute_confusion_and_metrics
from test_automation.db import get_connection, get_or_create_campaign_id, insert_fact_results

# ----------------------------------------------------
# Fonction pour récupérer le prompt d'une règle donnée
# ----------------------------------------------------
def get_base_prompt_for_rule(rule_cfg: dict) -> str:
    """
    Récupère le prompt à utiliser à partir de PROMPTS_MAPPING
    :param rule_cfg : dictionnaire de configuration de la règle
    :return : texte du prompt
    """    
    # Vérification de l'existence de la clé du prompt et extraction si présente
    prompt_key = rule_cfg.get("prompt_key")
    if not prompt_key:
        raise ValueError(f"Règle {rule_cfg.get('name')} : 'prompt_key' manquant.")
    
    # Récupération du préfixe de la clé uniquement
    # On sépare les composants de la clé grâce au "." et on prend le premier élément
    # Exemple pour "SD-08.01", le préfixe est "SD-08"
    prefix = prompt_key.split(".")[0] 
    prompt_dict = PROMPTS_MAPPING.get(prefix)
    if not prompt_dict:
        raise KeyError(f"Aucun fichier de prompts trouvé pour le préfixe '{prefix}'")

    try:
        return prompt_dict[prompt_key]
    except KeyError:
        raise KeyError(f"Prompt '{prompt_key}' introuvable dans le mapping.")

# -------------------------------------------
# Fonction principale pour exécuter les tests
# -------------------------------------------
def main(insert_in_db: bool = True):
    try:
        df_tests = load_tsv_report("AcceptableUnit.tsv")    # à (dé)commenter selon l'option
        # df_tests = load_all_tsv_reports()                     # à (dé)commenter selon l'option
        ### DEBUG ###
        print("Nb de lignes dans df_tests :", len(df_tests))
        print("Premières colonnes :", df_tests.columns)
        ### DEBUG ###
        rules_mapping = load_rules_mapping()

        results = []

        for row in df_tests.itertuples():
            rule_name = row.rule_name
            target_text = row.target_text
            report_name = row.source_file
            
            rule_cfg = rules_mapping.get(rule_name)
            ### DEBUG ###
            ### print("Traitement règle:", rule_name, "| fichier:", report_name, "| rule_cfg:", rule_cfg is not None)
            ### DEBUG ###
            if rule_cfg is None:
                # Si la règle est présente dans le TSV mais pas dans les JSON, on log et on continue
                print(f"Règle inconnue dans les JSON: {rule_name}"
                      f"(issue du fichier : {report_name})")
                continue
            try:
                # Récupération du prompt de base pour cette règle
                base_prompt = get_base_prompt_for_rule(rule_cfg)
                # Appel au LLM
                llm_raw_response = call_llama_for_test(
                    rule_cfg=rule_cfg,
                    target_text=target_text,
                    base_prompt=base_prompt,
                )
                # Parsing de la réponse du LLM
                parsed = parse_llm_response_for_test(llm_raw_response)            
                # Exemple d’accès aux champs parsés
                violation = parsed["violation"]            # True / False / None
                error_message = parsed["error_message"]
                parsing_confidence = parsed["parsing_confidence"]
                # Construction de la ligne de résultat
                results.append(
                    {
                        "rule_name": row.rule_name,
                        "source_file": row.source_file,
                        "target_text": row.target_text,
                        "ischecker_status": row.ischecker_status,
                        "llm_violation": violation,
                        "llm_status": (
                            "violation" if violation is True
                            else "no_violation" if violation is False
                            else None
                        ),
                        "llm_error_message": error_message,
                        "parsing_confidence": parsing_confidence,
                    }
                )

                # Log de suivi
                print(
                    f"[{report_name}] règle={rule_name} | "
                    f"target_text={target_text} | "
                    f"llm_status={results[-1]['llm_status']} | "
                    f"parsing_confidence={parsing_confidence:.2f}"
                )

            except (ValueError, KeyError, RuntimeError) as e:
                print(f"Erreur pour la règle {rule_name} / test '{report_name}': {e}")
                continue

        # --- Fin de boucle : on travaille maintenant sur le DataFrame complet ---
        if not results:
            print("Aucun résultat LLM à analyser.")
            return

        df_results = pd.DataFrame(results)

        # Pour le comparateur, on préfère une colonne booléenne 'violation'
        # 'violation' = True si le LLM pense qu'il y a infraction à la règle (= False sinon)
        # On comparera cette colonne à 'ischecker_status' pour voir s'il y a matching
        df_results = df_results.rename(columns={"llm_violation": "violation"})

        # Ajout des colonnes TP/TN/FP/FN 
        # Marquage des lignes utilisables pour les métriques (parsing_confidence >= 0.8 avec usable_for_metrics)
        df_results = add_comparison_columns(df_results, confidence_threshold=0.8)

        # Calcul des métriques globales à partir des labels TP/TN/FP/FN
        # accuracy, precision, recall, f1-score
        metrics = compute_confusion_and_metrics(df_results)
        counts = metrics["counts"]
        print("\n----- Matrice de confusion (parsing_confidence >= 0.8) -----")
        # Affichage de la matrice de confusion
        print(f"                    LLM: violation   LLM: no_violation")
        print(f"isChecker: violation      TP = {counts['TP']:<3}       FN = {counts['FN']:<3}")
        print(f"isChecker: no_violation  FP = {counts['FP']:<3}       TN = {counts['TN']:<3}")

        print("\n----- Métriques globales (parsing_confidence >= 0.8) -----")
        print(f"Nombre total de tests pris en compte : {metrics['total']}")
        print(f"Accuracy  : {metrics['accuracy']:.3f}  "
              f"(part de prédictions correctes sur l'ensemble des tests)")
        print(f"Precision : {metrics['precision']:.3f}  "
              f"(quand le LLM dit 'violation', il a raison dans ~{metrics['precision']*100:.1f} % des cas)")
        print(f"Recall    : {metrics['recall']:.3f}  "
              f"(le LLM retrouve ~{metrics['recall']*100:.1f} % des violations d'isChecker)")
        print(f"F1-score  : {metrics['f1']:.3f}  "
              "(équilibre entre precision et recall)")

        # Colonne 'match' : True si le LLM et isChecker sont d'accord (TP ou TN), False sinon
        df_results["match"] = df_results["comparison_label"].isin(["TP", "TN"])
        
        if insert_in_db:
            conn = get_connection()
            try:
                campaign_id = get_or_create_campaign_id(
                    conn,
                    llm_model_name="llama-3.3-70b-instruct",
                    llm_provider="Scaleway",
                    temperature=0.0,
                    top_p=0.95,
                    presence_penalty=0.0,
                    description="Campagne de tests automatiques isChecker vs LLM",
                )
                insert_fact_results(conn, df_results, campaign_id=campaign_id)
            finally:
                conn.close()

    except Exception as e:
        print(f"Erreur dans le pipeline de tests : {e}")

if __name__ == "__main__":
    main(insert_in_db=False)    # Passer à True pour insérer les résultats dans la base de données
