import os
import json
import urllib.request
import urllib.error
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "success",
        "message": "Serveur SmartBudget AI pret (Connexion API directe)",
    })

@app.route('/api/expense', methods=['POST'])
def process_expense():
    data = request.get_json()
    user_text = data.get("text", "")

    if not user_text:
        return jsonify({"error": "Le texte est vide"}), 400

    system_prompt = (
        "Tu es un assistant financier. Analyse la phrase de l'utilisateur pour extraire "
        "le montant (nombre seul) et la categorie (Alimentation, Transport, Loisirs, Autre). "
        "Reponds UNIQUEMENT sous la forme d'un objet JSON propre, sans texte avant ou apres. "
        "Exemple : {\"montant\": 25, \"categorie\": \"Alimentation\"}"
    )

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(
            GROQ_API_URL, 
            data=json.dumps(payload).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            ai_analysis = res_data["choices"][0]["message"]["content"]
            return jsonify({
                "status": "success",
                "data": json.loads(ai_analysis)
            })

    except urllib.error.HTTPError as e:
        return jsonify({"error": f"Erreur API Groq: {e.read().decode('utf-8')}"}), e.code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)