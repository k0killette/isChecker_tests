import os
from openai import OpenAI

# Test de connexion
def test_api_connection():
    try:
        client = OpenAI(
            base_url="https://api.scaleway.ai/3f6b92d6-1b09-4510-a0c0-4c3d6cc85743/v1", 
            api_key=os.getenv("SCW_SECRET_KEY")
        )
        
        # Test minimal
        response = client.chat.completions.create(
            model="llama-3.3-70b-instruct",  # À ajuster selon le modèle dispo
            messages=[
                {"role": "user", "content": "Dis juste 'OK' si tu me reçois"}
            ],
            max_tokens=10,
            temperature=0
        )
        
        print("✓ API accessible")
        print(f"Réponse : {response.choices[0].message.content}")
        print(f"Modèle utilisé : {response.model}")
        return True
        
    except Exception as e:
        print(f"✗ Erreur d'accès à l'API : {e}")
        return False

if __name__ == "__main__":
    # Assure-toi que SCW_SECRET_KEY est défini
    if not os.getenv("SCW_SECRET_KEY"):
        print("⚠ Variable d'environnement SCW_SECRET_KEY non définie")
    else:
        test_api_connection()