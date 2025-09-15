#----- Importation des modules nécessaires ----- #
import os
import json
import re
import string

from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

from prompts import PROMPTS_MAPPING

# ----- Chemins des règles et documents à analyser ----- #
RULES_DIR = Path("rules")
DOCUMENT_PATH = Path("data/test_doc.txt")

# ----- Chargement des variables d’environnement ----- #
load_dotenv()

# ----- Configuration du client OpenAI ----- #
client = OpenAI(
  base_url = "https://api.scaleway.ai/3f6b92d6-1b09-4510-a0c0-4c3d6cc85743/v1", 
  api_key = os.getenv("SCW_SECRET_KEY") 
)

# ----- Chargement des règles depuis les fichiers .json ----- #
def load_all_rules():
  all_rules = []
  for file in RULES_DIR.glob("*.json"):
    with open(file, encoding="utf-8") as f:
      data = json.load(f)
      category = data.get("category", "Inconnue")
      rules = data.get("rules", [])
      for rule in rules:
        rule["category"] = category
      all_rules.extend(rules)
  return all_rules

# ----- Chargement des prompts ----- #
def get_prompt(rule: dict) -> str:
    if not rule.get("llm_required", False):
        return None

    prompt_key = rule.get("prompt_key")
    if not prompt_key:
        raise ValueError(f"Règle {rule.get('id')} : 'prompt_key' manquant.")

    # Extrait le préfixe SD-08, SD-09, etc.
    prefix = prompt_key.split('.')[0]

    if not PROMPTS_MAPPING:
      raise ValueError("Aucun prompt n’a été chargé : PROMPTS_MAPPING est vide ou mal importé.")

    prompt_dict = PROMPTS_MAPPING.get(prefix)

    if not prompt_dict:
        raise KeyError(f"Aucun fichier de prompts trouvé pour le préfixe '{prefix}'")

    try:
        return prompt_dict[prompt_key]
    except KeyError:
        raise KeyError(f"Prompt '{prompt_key}' introuvable dans {prompt_dict}")

# ----- Chargement du document à analyser ----- #
def load_document_text(path):
  with open(path, encoding="utf-8") as f:
    return f.read()
  
# ----- Chargement des règles nécessitant une analyse RegEx ----- #
def check_rule_with_regex(rule, document_text):
  """
  Applique les RegEx contenues dans les règles et renvoie les erreurs détectées dans un format uniforme avec les règles LLM
  """
  detected_errors = []

  # On parcourt chaque RegEx de la règle une par une (car une règle peut contenir plusieurs expressions régulières)
  # Si la clé "regex" existe bien dans la règle alors on l’utilise (sinon on utilise une liste vide)
  for pattern in rule.get("regex", []):  
    # On extrait la chaîne de caractères RegEx à utiliser
    regex_str = pattern["regex"]
    # On cherche toutes les correspondances dans le texte (re.finditer() scanne tout le texte et renvoie un objet match pour chaque correspondance)
    matches = re.finditer(regex_str, document_text)

    # On récupère les champs dynamiques du message (ex: {decimals})
    placeholders = [field for _, field, _, _ in string.Formatter().parse(rule["error_mesg"]) if field]
    
    # Pour chaque correspondance trouvée (= chaque erreur)
    for match in matches:
      # On génère dynamiquement les valeurs à injecter
      dynamic_values = {}
      for field in placeholders:
        try:
          # Cherche la fonction d’extraction fournie
          extractors = pattern.get("extract", {})
          if field in extractors:
            # Évalue la lambda à partir du texte
            extractor_fn = eval(extractors[field])
            dynamic_values[field] = extractor_fn(match)
          else:
            dynamic_values[field] = "?"
        except Exception:
          dynamic_values[field] = "?"

      # Formatage du message final
      try:
        formatted_message = rule["error_mesg"].format(**dynamic_values)
      except Exception:
        formatted_message = rule["error_mesg"]
      
      matched = match.group()

      # Séparation du texte en phrases (en évitant les cas où le . est utilisé comme séparateur (décimales, adresse IP, etc.))
      sentences = re.split(r'(?<=[^0-9])\.(?=\s+[A-ZÉÈÀÂÊÎÔÛ])', document_text)
      # Recherche de la phrase contenant le match
      context = next(
        (sentence.strip() for sentence in sentences if matched in sentence),
        document_text  # fallback complet si non trouvé
      )

      error = {          
          "rule_name": rule["name"],
          "category": rule["category"],          
          "description": rule["description"],
          "error_mesg": formatted_message,
          "context": context
      }
      # On ajoute l’erreur détectée à la liste detected_errors
      detected_errors.append(error) 
  # On retourne toutes les erreurs détectées   
  return detected_errors

# ----- Chargement des règles nécessitant un LLM ----- #
def check_rule_with_llm(rule, document_text, prompt):
  # On demande au LLM de répondre en JSON
  full_prompt = (
    f"{prompt}\n\n"
    f"Texte à analyser :\n{document_text}\n\n"
    "Identifie les erreurs présentes dans ce texte. Renvoie uniquement la liste des erreurs, dans l'ordre du texte et au format .JSON. Tu dois utiliser les clés de la règle enfreinte, notamment le message d’erreur fourni via `error_mesg` : \n"
    "{\n"    
    ' "rule_name": rule["name"],\n'
    ' "category": rule["category"],\n'    
    ' "description": rule["description"],\n'
    ' "error_mesg": rule["error_mesg"],\n'
    ' "context": "la phrase complète contenant l\'erreur"\n'
    "}\n\n"
    "Tu dois reprendre exactement les valeurs des clés dans les règles. Ne modifie pas les valeurs `rule_name`, `category`, `description`, ou `error_mesg`.\n"
    "IMPORTANT : ne retourne PAS le fragment isolé de l'erreur, mais uniquement la phrase entière (context)."
    "}\n\n"
  )  
  
  # Envoi de la demande à l’IA
  response = client.chat.completions.create(
    model="llama-3.3-70b-instruct", #gemma-3-27b-it  #llama-3.3-70b-instruct  #mistral-smal-3.1-24b-instruct-2503
    messages=[
      { 
        "role": "system", 
        "content": "Tu es un expert en vérification linguistique. Ton rôle est d'analyser des textes pour vérifier qu’ils respectent les règles spécifiées. Prends en compte l'ensemble de la phrase et son contexte. Sois précis et concis." 
      },
      { 
        "role": "user", 
        "content": full_prompt 
      }
    ],
    temperature=0,
    top_p=0.95, 
    presence_penalty=0 
    )
  
  content = response.choices[0].message.content.strip()

  # Nettoyage des blocs Markdown si présents
  if content.startswith("```"):
    content = re.sub(r"^```json\s*", "", content)  # enlève le début ```json
    content = re.sub(r"```$", "", content)  # enlève la fin ```
    content = content.strip()

  # Pour manipuler ces données il faut transformer les chaînes de caractères JSON en objets Python (= Parsing JSON avec la fonction json.loads())
  try:
    errors = json.loads(content)
    # Si le résultat n'est pas une liste (isinstance(obj, type) sert à vérifier si un objet est d’un certain type)
    if not isinstance(errors, list):
      print("Erreur : la réponse JSON n'est pas une liste")
      return []
    # Sinon on renvoie la liste d'erreurs en Python
    return errors
  
  # Si `content` n’est pas un JSON valide, json.loads(content) lance une exception appelée JSONDecodeError interceptée par `except``
  except json.JSONDecodeError as err:
    print("Erreur de parsing JSON de la réponse LLM :", err)
    print("Contenu reçu :", content)
    # On renvoie une liste vide car on ne peut pas traiter la réponse
    return []

def main(document_path):
  rules = load_all_rules()
  document = load_document_text(document_path)

  all_detected_errors = []

  for rule in rules:
    # Vérification RegEx
    if rule.get("regex"):
      detected_errors = check_rule_with_regex(rule, document)
      all_detected_errors.extend(detected_errors)

    # Vérification LLM
    if rule.get("llm_required", False):
      try:
        prompt = get_prompt(rule)  # on récupère le prompt
        if not prompt:
          continue  # au cas où get_prompt() retournerait None, même si improbable
        # Appel de la fonction de vérification LLM
        detected_errors = check_rule_with_llm(rule, document, prompt=prompt)
        all_detected_errors.extend(detected_errors)
      except (KeyError, ValueError) as e:
        print(e)
        continue

  for error in all_detected_errors:
    print(error)

if __name__ == "__main__":
  main(document_path=Path("data/test_doc.txt"))
