# parsing_llm_responses.py

import json
import re
from typing import Any, Dict


# -------------------------------------------------------------------
# Nettoyage du texte (code fences Markdown, espaces, etc.)
# -------------------------------------------------------------------
def clean_llm_output(raw_text: str) -> str:
    """
    Nettoie la réponse brute du LLM :
    - supprime les blocs `````` éventuels
    - supprime les backticks superflus
    - strip espaces de début / fin

    :param raw_text: Réponse brute renvoyée par le modèle
    :return: Chaîne nettoyée, censée contenir du JSON
    """
    text = raw_text.strip()

    # Si la réponse est encadrée par des fences Markdown ``````
    if text.startswith("```"):
        # On enlève un éventuel préfixe ```json ou ```
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        # On enlève le bloc ```
        text = re.sub(r"```$", "", text)
        text = text.strip()

    return text

# -------------------------------------------------------------------
# Tentative de parsing JSON + calcul d'un score de confiance
# -------------------------------------------------------------------
def parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """
    Tente de parser la réponse du LLM en JSON, calcule un parsing_confidence
    et retourne un dictionnaire structuré.

    Format attendu (objet JSON unique) :
    {
      "violation": true | false,
      "error_message": "...",
      "explanation": "...",
      "context": "..."
    }

    parsing_confidence (0.0 -> 1.0) :
    - 1.0 : JSON valide, toutes les clés attendues sont présentes
    - 0.8 : JSON valide mais certaines clés sont manquantes
    - 0.4 : JSON invalide mais tentative de récupération minimale
    - 0.0 : parsing impossible

    :param raw_text: Réponse brute du LLM
    :return: dict avec au minimum les clés :
             - violation: bool | None
             - error_message: str | None
             - explanation: str | None
             - context: str | None
             - parsing_confidence: float
             - raw_content: str (contenu original, pour debug)
    """
    cleaned = clean_llm_output(raw_text)

    base_result: Dict[str, Any] = {
        "violation": None,
        "error_message": None,
        "explanation": None,
        "context": None,
        "parsing_confidence": 0.0,
        "raw_content": raw_text,
    }

    if not cleaned:
        # Rien à parser
        return base_result

    # Tentative de parsing strict
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # JSON invalide : on renvoie le résultat de base avec faible confiance
        base_result["parsing_confidence"] = 0.0
        return base_result

    # Si on arrive ici, on a un JSON valide (dict ou autre)
    # On attend un objet JSON (dict), pas une liste
    if isinstance(data, list):
        # Si le modèle a renvoyé une liste, on prend le premier élément pour simplifier
        if data:
            data = data[0]
        else:
            base_result["parsing_confidence"] = 0.4
            return base_result

    if not isinstance(data, dict):
        # Type inattendu
        base_result["parsing_confidence"] = 0.4
        return base_result

    # Extraction des champs avec valeurs par défaut
    violation = data.get("violation")
    error_message = data.get("error_message")
    explanation = data.get("explanation")
    context = data.get("context")

    result = {
        "violation": bool(violation) if violation is not None else None,
        "error_message": error_message if isinstance(error_message, str) else None,
        "explanation": explanation if isinstance(explanation, str) else None,
        "context": context if isinstance(context, str) else None,
        "raw_content": raw_text,
    }

    # Calcul simple du parsing_confidence en fonction de la complétude
    expected_keys = ["violation", "error_message", "explanation", "context"]
    present_keys = [k for k in expected_keys if data.get(k) is not None]
    completeness_ratio = len(present_keys) / len(expected_keys)

    if completeness_ratio == 1.0:
        confidence = 1.0
    elif completeness_ratio >= 0.5:
        confidence = 0.8
    else:
        confidence = 0.4

    result["parsing_confidence"] = confidence

    return result

# -------------------------------------------------------------------
# Fonction utilitaire de haut niveau pour le pipeline
# -------------------------------------------------------------------
def parse_llm_response_for_test(raw_text: str) -> Dict[str, Any]:
    """
    Interface de haut niveau utilisée dans le pipeline :
    prend la réponse brute du LLM et renvoie un dict structuré
    avec violation / no_violation + parsing_confidence.

    :param raw_text: Réponse brute renvoyée par l'API LLaMA
    :return: dict prêt à être fusionné avec les résultats de comparaison
    """
    return parse_llm_json(raw_text)
