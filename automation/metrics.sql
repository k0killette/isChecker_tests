-- Taux de concordance global
SELECT 
    COUNT(CASE WHEN match THEN 1 END) * 100.0 / COUNT(*) as accuracy
FROM test_results
WHERE parsing_confidence >= 0.8;

-- Précision (fiabilité des détections LLM)
SELECT 
    COUNT(CASE WHEN comparison_category = 'TRUE_POSITIVE' THEN 1 END) * 100.0 /
    COUNT(CASE WHEN llm_status = 'VIOLATION' THEN 1 END) as precision
FROM test_results
WHERE parsing_confidence >= 0.8;

-- Rappel (sensibilité - capacité à détecter les vraies infractions)
SELECT 
    COUNT(CASE WHEN comparison_category = 'TRUE_POSITIVE' THEN 1 END) * 100.0 /
    COUNT(CASE WHEN ischecker_status = 'VIOLATION' THEN 1 END) as recall
FROM test_results
WHERE parsing_confidence >= 0.8;

-- F1-Score
WITH metrics AS (
    SELECT 
        COUNT(CASE WHEN comparison_category = 'TRUE_POSITIVE' THEN 1 END) * 1.0 as tp,
        COUNT(CASE WHEN llm_status = 'VIOLATION' THEN 1 END) as llm_viol,
        COUNT(CASE WHEN ischecker_status = 'VIOLATION' THEN 1 END) as isch_viol
    FROM test_results
    WHERE parsing_confidence >= 0.8
)
SELECT 
    2 * (tp / llm_viol) * (tp / isch_viol) / ((tp / llm_viol) + (tp / isch_viol)) as f1_score
FROM metrics;