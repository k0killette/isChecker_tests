import json
import re

def parse_llm_response(response):
    """
    Parse multi-niveaux pour gérer la variabilité
    
    Returns:
        tuple (dict parsed_result, float confidence_score)
    """
    
    # Niveau 1 : JSON strict (confiance maximale)
    try:
        parsed = json.loads(response)
        if 'status' in parsed:
            return parsed, 1.0
    except json.JSONDecodeError:
        pass
    
    # Niveau 2 : Extraction JSON partiel avec réparation
    json_pattern = r'\{[^}]*"status"\s*:\s*"(NO_VIOLATION|VIOLATION)"[^}]*\}'
    match = re.search(json_pattern, response, re.IGNORECASE | re.DOTALL)
    if match:
        try:
            json_str = match.group(0).replace("'", '"')  # Correction guillemets
            parsed = json.loads(json_str)
            return parsed, 0.8
        except:
            pass
    
    # Niveau 3 : Analyse sémantique par mots-clés
    response_lower = response.lower()
    
    violation_keywords = [
        'violation', 'infraction', 'non conforme', 'écart', 
        'erreur', 'incorrect', 'interdit', 'inadapté', 'inapproprié',
        'ne sont pas approuvé', 'n\'est pas approuvé'
    ]
    
    if any(keyword in response_lower for keyword in violation_keywords):
        return {'status': 'VIOLATION', 'message': response}, 0.6
    
    no_violation_keywords = [
        'conforme', 'correct', 'valide', 'respecte', 
        'ok', 'acceptable', 'approprié', 'pas d\'infraction'
    ]
    
    if any(keyword in response_lower for keyword in no_violation_keywords):
        return {'status': 'NO_VIOLATION', 'message': response}, 0.6
    
    # Niveau 4 : Indéterminé - nécessite revue manuelle
    return {'status': 'UNKNOWN', 'message': response}, 0.0