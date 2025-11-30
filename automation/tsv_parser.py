import pandas as pd

def parse_ischecker_tsv(filepath):
    """
    Parse un rapport de tests isChecker au format TSV
    
    Args:
        filepath: Chemin vers le fichier TSV
        
    Returns:
        dict contenant métadonnées et liste de tests
    """
    # Lecture du TSV en ignorant les lignes commentées
    df = pd.read_csv(filepath, sep='\t', encoding='utf-8', comment='#')
    df.columns = df.columns.str.strip()
    
    # Extraction du nom de règle depuis le fichier
    rule_name = extract_rule_name_from_file(filepath)
    
    tests = []
    for idx, row in df.iterrows():
        # Détermination du statut basé sur la colonne description
        has_violation = not (pd.isna(row['description']) or row['description'].strip() == '')
        
        tests.append({
            'test_id': f"{rule_name}_{idx+1:03d}",
            'rule_name': row['ruleName'],
            'target_text': row['target_text'].strip(),
            'ischecker_status': 'VIOLATION' if has_violation else 'NO_VIOLATION',
            'ischecker_message': row['description'].strip() if has_violation else '',
            'severity': row.get('severity', ''),
            'language': row.get('lang', 'FR')
        })
    
    return {
        'rule_name': rule_name,
        'total_tests': len(tests),
        'violations': sum(1 for t in tests if t['ischecker_status'] == 'VIOLATION'),
        'no_violations': sum(1 for t in tests if t['ischecker_status'] == 'NO_VIOLATION'),
        'tests': tests
    }

# ------------------------------
# Exemple d'utilisation
# ------------------------------

# result = parse_ischecker_tsv('GIFASWordNotApproved.tsv')

# # Résultat :
# {
#     'rule_name': 'GIFASWordNotApproved',
#     'total_tests': 74,
#     'violations': 52,      # description remplie
#     'no_violations': 22,   # description vide
#     'tests': [...]
# }