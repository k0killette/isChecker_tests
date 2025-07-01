# Envoie une demande à une IA via une API (ici une IA hébergée sur Scaleway)
# Affiche la réponse de l’IA progressivement, en temps réel

# ----- Importation des modules nécessaires ----- #
import os
from openai import OpenAI
from dotenv import load_dotenv

# ----- Chargement des variables d’environnement ----- #
load_dotenv()

# ----- Configuration du client OpenAI ----- #
client = OpenAI(
    base_url = "https://api.scaleway.ai/3f6b92d6-1b09-4510-a0c0-4c3d6cc85743/v1", # adresse du serveur API de Scaleway auquel on envoie la demande
    api_key = os.getenv("SCW_SECRET_KEY") # Importe SCW_SECRET_KEY depuis le fichier .env
)

# ----- Envoi d'une demande à l’IA ----- #
response = client.chat.completions.create(
    model="gemma-3-27b-it", #llama-3.3-70b-instruct  #mistral-smal-3.1-24b-instruct-2503
    messages=[
      { "role": "system", "content": "Tu es un expert en vérification linguistique." },
      { "role": "user", "content": prompt },
    ],
    max_tokens=512,
    temperature=0,
    top_p=0.95, # mots dont la probabilité cumulée atteint 95%
    presence_penalty=0, # Chaque fois qu'un mot apparaît, sa probabilité d'être réutilisé diminue (plus la valeur est élevée, plus l'IA évite les répétitions)
    stream=True, # pour recevoir la réponse petit à petit (mot à mot)
)

# ----- Affichage de la réponse en direct ----- #
for chunk in response:
  if chunk.choices and chunk.choices[0].delta.content: # texte généré par l’IA
    print(chunk.choices[0].delta.content, end="", flush=True) # affiche le texte sans attendre la fin de la réponse complète