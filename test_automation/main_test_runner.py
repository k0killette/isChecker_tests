import pandas as pd
from tsv_parser import load_tsv_report, load_all_tsv_reports
from rules_loader import load_rules_mapping

def main():
    try:
        # df_tests = load_tsv_report("GIFASWordNotApproved.tsv")    # à (dé)commenter selon l'option
        df_tests = load_all_tsv_reports()                     # à (dé)commenter selon l'option
        rules_mapping = load_rules_mapping()
        for row in df_tests.itertuples():
            rule_name = row.rule_name
            report_name = row.source_file
            rule_cfg = rules_mapping.get(rule_name)
            if rule_cfg is None:
                # Si la règle est présente dans le TSV mais pas dans les JSON, on log et on continue
                print(f"Règle inconnue dans les JSON: {rule_name}"
                      f"(issue du fichier : {report_name})")
                continue
        # rules_config = load_rules_config("rules/")

        # results = []

        # for row in df_tsv.itertuples():
        #     # construction du prompt + appel LLM + parsing + comparaison
        #     ...
        #     results.append(result_row)

        # df_results = pd.DataFrame(results)
        # save_results_to_db(df_results)
    except Exception as e:
        print(f"Erreur dans le pipeline de tests : {e}")

if __name__ == "__main__":
    main()
