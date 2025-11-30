import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.scaleway.ai/v1",
    api_key=os.getenv("SCW_SECRET_KEY")  # Clé stockée dans variable d'environnement
)

def call_llm_api(system_prompt, rule_prompt, target_text, max_retries=3):
    """
    Appelle l'API LLaMA avec gestion d'erreurs
    
    Returns:
        tuple (response_text, execution_time_seconds)
    """
    import time
    
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{rule_prompt}\n\nTexte à analyser : {target_text}"}
                ],
                temperature=0,      # Déterministe
                top_p=0.95,         # Limitation vocabulaire
                max_tokens=300      # Suffisant pour réponse structurée
            )
            
            execution_time = time.time() - start_time
            return response.choices[0].message.content, execution_time
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Échec définitif après 3 tentatives
            time.sleep(2 ** attempt)  # Backoff exponentiel