# Imports des modules spécialisés
from tsv_parser import parse_ischecker_tsv
from rules_loader import load_rules_config
from llm_client import call_llm_api
from response_parser import parse_llm_response, parse_confidence_level
from db_manager import DatabaseManager
from logger import setup_logging

def main():
    # Configuration du logging
    logger = setup_logging('automate_tests.log')
    
    # 1. Chargements initiaux
    logger.info("Chargement des configurations...")
    tests_data = parse_ischecker_tsv('reports/GIFASWordNotApproved.tsv')
    rules = load_rules_config('config/rules_config.json')
    system_prompt = load_file('config/system_prompt.txt')
    
    # 2. Connexion base de données
    db = DatabaseManager()
    execution_id = db.create_execution(
        name=f"Test {tests_data['rule_name']}",
        total_tests=tests_data['total_tests'],
        llm_model="llama-3.3-70b-instruct"
    )
    
    # 3. Boucle principale de tests
    for i, test in enumerate(tests_data['tests'], 1):
        logger.info(f"[{i}/{tests_data['total_tests']}] Test {test['test_id']}")
        
        try:
            # Récupération du prompt de règle
            rule_prompt = rules[test['rule_name']]['llm_prompt']
            
            # Appel API avec mesure de temps
            llm_response, exec_time = call_llm_api(
                system_prompt, 
                rule_prompt, 
                test['target_text']
            )
            
            # Parsing de la réponse
            parsed, confidence = parse_llm_response(llm_response)
            
            # Comparaison
            match = (parsed['status'] == test['ischecker_status'])
            category = determine_category(test['ischecker_status'], parsed['status'])
            
            # Stockage en BDD
            db.store_result(
                execution_id=execution_id,
                test_data=test,
                llm_data=parsed,
                confidence=confidence,
                match=match,
                category=category,
                exec_time=exec_time
            )
            
            logger.info(f"  → {category} (conf: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"  ✗ Erreur : {e}")
            db.store_error(execution_id, test['test_id'], str(e))
    
    # 4. Finalisation
    db.finalize_execution(execution_id)
    logger.info(f"=== Campagne terminée : {tests_data['total_tests']} tests ===")

if __name__ == "__main__":
    main()