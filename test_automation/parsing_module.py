import json
import re

def parse_llm_response(response):
    """
    Parse la réponse LLM avec stratégie multi-niveaux
    Retourne : (dict résultat, float confiance)
    """
    
    # Niveau 1 : JSON strict
    try:
        parsed = json.loads(response)
        if 'status' in parsed:
            return parsed, 1.0
    except json.JSONDecodeError:
        pass
    
    # Niveau 2 : Extraction JSON partiel/malformé
    json_pattern = r'\{[^}]*"status"[^}]*\}'
    match = re.search(json_pattern, response, re.DOTALL)
    if match:
        try:
            # Tentative de "réparation" du JSON
            json_str = match.group(0)
            json_str = json_str.replace("'", '"')  # Guillemets simples
            parsed = json.loads(json_str)
            return parsed, 0.8
        except:
            pass
    
    # Niveau 3 : Analyse par mots-clés (fallback)
    response_lower = response.lower()
    
    # Détection d'écart/erreur
    if any(keyword in response_lower for keyword in 
           ['non conforme', 'écart', 'erreur', 'incorrect', 'violation']):
        return {'status': 'FAIL', 'message': response}, 0.6
    
    # Détection de conformité
    if any(keyword in response_lower for keyword in 
           ['conforme', 'correct', 'valide', 'respecte', 'ok']):
        return {'status': 'PASS', 'message': response}, 0.6
    
    # Niveau 4 : Indéterminé - nécessite revue manuelle
    return {'status': 'UNKNOWN', 'message': response}, 0.0


def validate_parsing_quality(sample_size=100):
    """
    Valide la qualité du parsing sur un échantillon
    À exécuter après première passe pour ajuster les règles
    """
    conn = psycopg2.connect(DB_CONN)
    cursor = conn.cursor()
    
    # Échantillon aléatoire
    cursor.execute("""
        SELECT test_id, llm_response, llm_status, parsing_confidence
        FROM test_results
        ORDER BY RANDOM()
        LIMIT %s
    """, (sample_size,))
    
    print("Validation manuelle de l'échantillon :")
    correct = 0
    
    for row in cursor.fetchall():
        test_id, response, parsed_status, confidence = row
        print(f"\n[{test_id}] Confiance: {confidence:.2f}")
        print(f"Réponse LLM : {response[:200]}...")
        print(f"Parsing : {parsed_status}")
        
        user_input = input("Correct ? (o/n) : ")
        if user_input.lower() == 'o':
            correct += 1
    
    accuracy = correct / sample_size
    print(f"\n=== Précision du parsing : {accuracy:.1%} ===")
    
    return accuracy