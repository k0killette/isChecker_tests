import os
import json
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

# Chargement des variables d’environnement (.env)
load_dotenv()

# Dossier test_automation
BASE_DIR = Path(__file__).parent

# Configuration du client LLaMA via l’API Scaleway (compatible OpenAI)
client = OpenAI(
    base_url="https://api.scaleway.ai/3f6b92d6-1b09-4510-a0c0-4c3d6cc85743/v1",
    api_key=os.getenv("SCW_SECRET_KEY"),
)

# -------------------------------------------------
# Construction du prompt complet pour un test donné
# -------------------------------------------------
def build_llm_prompt(rule_cfg: Dict[str, Any], target_text: str, base_prompt: str) -> str:
    """
    Construit le prompt complet envoyé au LLM pour un test donné.

    :param rule_cfg: Configuration de la règle (issue de rules_mapping)
    :param target_text: Texte à analyser (target_text du TSV)
    :param base_prompt: Prompt de base de la règle (chargé via prompts_mapping)
    :return: Chaîne de caractères contenant le prompt complet
    """
    # On réutilise l’esprit de ton POC mais en version "target_text"
    full_prompt = (
        f"{base_prompt}\n\n"
        f"Texte à analyser :\n{target_text}\n\n"
        "Tu dois analyser ce texte au regard de la règle fournie et renvoyer "
        "une UNIQUE réponse JSON structurée, avec les clés suivantes :\n"
        "{\n"
        '  "violation": true | false,\n'
        '  "error_message": "message d\'erreur ou chaîne vide si pas de violation",\n'
        '  "explanation": "explication courte et claire",\n'
        '  "context": "la phrase complète contenant l\'erreur ou le texte complet",\n'
        "}\n\n"
        "IMPORTANT :\n"
        "- renvoie UNIQUEMENT cet objet JSON, sans texte avant ni après,\n"
        "- conserve la cohérence avec la règle et son message d'erreur.\n"
    )
    return full_prompt

# -----------------------------------------------------------------
# Appel LLaMA : envoi du prompt et récupération de la réponse brute
# -----------------------------------------------------------------
def call_llama_raw(prompt: str) -> str:
    """
    Envoie un prompt au modèle LLaMA 3.3-70b-instruct et retourne la réponse brute (texte).

    :param prompt: Contenu du message "user"
    :return: Contenu textuel renvoyé par le modèle
    :raises RuntimeError: en cas d'erreur d'appel à l'API
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en vérification linguistique. "
                        "Ton rôle est d'analyser des textes pour vérifier qu’ils "
                        "respectent des règles spécifiques. Respecte strictement "
                        "le format JSON demandé."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
            top_p=0.95,
            presence_penalty=0,
            max_tokens=300,
        )
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'appel à l'API LLaMA : {e}")

    content = response.choices[0].message.content.strip()
    return content

# -------------------------------------------------------------------
# Appel LLaMA pour un test : règle + target_text
# -------------------------------------------------------------------
def call_llama_for_test(
    rule_cfg: Dict[str, Any],
    target_text: str,
    base_prompt: str,
) -> str:
    """
    Construit le prompt complet à partir de la règle et du target_text,
    puis appelle le modèle LLaMA et retourne la réponse texte.

    :param rule_cfg: Dictionnaire de configuration de la règle (rules_mapping[rule_name])
    :param target_text: Texte à analyser
    :param base_prompt: Prompt détaillé de la règle (issu de PROMPTS_MAPPING)
    :return: Réponse brute du LLM (texte)
    """
    full_prompt = build_llm_prompt(rule_cfg, target_text, base_prompt)
    return call_llama_raw(full_prompt)
