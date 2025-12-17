def compare_results(ischecker_status, llm_status):
    """Compare isChecker (référence) vs LLM"""
    
    if llm_status == 'UNKNOWN':
        return {
            'category': 'INDETERMINATE',
            'match': False,
            'analysis': 'Réponse LLM non interprétable'
        }
    
    match = (ischecker_status == llm_status)
    
    if match:
        if ischecker_status == 'VIOLATION':
            category = 'TRUE_POSITIVE'
            analysis = 'LLM détecte correctement l\'infraction'
        else:
            category = 'TRUE_NEGATIVE'
            analysis = 'LLM confirme correctement l\'absence d\'infraction'
    else:
        if llm_status == 'VIOLATION' and ischecker_status == 'NO_VIOLATION':
            category = 'FALSE_POSITIVE'
            analysis = 'LLM détecte une infraction absente dans isChecker (sur-détection)'
        else:  # llm_status == 'NO_VIOLATION' and ischecker_status == 'VIOLATION'
            category = 'FALSE_NEGATIVE'
            analysis = 'LLM rate une infraction détectée par isChecker (sous-détection)'
    
    return {
        'category': category,
        'match': match,
        'analysis': analysis
    }

def determine_category(ischecker_status, llm_status):
    """Détermine la catégorie de comparaison"""
    
    if llm_status == 'UNKNOWN':
        return 'INDETERMINATE'
    
    if ischecker_status == llm_status:
        if ischecker_status == 'VIOLATION':
            return 'TRUE_POSITIVE'
        else:
            return 'TRUE_NEGATIVE'
    else:
        if llm_status == 'VIOLATION':
            return 'FALSE_POSITIVE'
        else:
            return 'FALSE_NEGATIVE'