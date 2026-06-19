import os
import json
import sqlite3
import urllib.request
import urllib.error
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialisation automatique de la base de données
def init_sqlite_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        montant REAL NOT NULL,
        categorie TEXT NOT NULL,
        description TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

init_sqlite_db()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(system_prompt, user_prompt, require_json=False):
    """Fonction générique utilisant le modèle de production llama-3.1-8b-instant"""
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1
    }
    
    if require_json:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(GROQ_API_URL, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        return res_data["choices"][0]["message"]["content"].strip()

def execute_generated_sql(sql_query):
    """Exécute la requête SQL générée par l'Agent 2 sur la base SQLite"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        if sql_query.strip().upper().startswith("SELECT"):
            result = cursor.fetchall()
            conn.close()
            return f"Résultat SQL: {result}"
        else:
            conn.commit()
            conn.close()
            return "Succès : Opération d'écriture validée en base de données."
    except Exception as e:
        conn.close()
        return f"Erreur d'exécution SQL: {str(e)}"

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/api/expense', methods=['POST'])
def process_agent_workflow():
    data = request.get_json()
    user_text = data.get("text", "")

    if not user_text:
        return jsonify({"error": "Le texte est vide"}), 400

    try:
        # --- AGENT 1 : COMPRÉHENSION & EXTRACTION ---
        prompt_agent_1 = (
            "Tu es l'Agent 1 (Aiguilleur). Analyse la phrase de l'utilisateur et extrais les données au format JSON strict.\n"
            "L'objet JSON doit CONTENIR EXACTEMENT ces trois clés :\n"
            "{\n"
            "  \"intention\": \"ADD\" (si l'utilisateur ajoute une dépense) ou \"QUERY\" (s'il demande un total ou un historique),\n"
            "  \"montant\": nombre_ou_null,\n"
            "  \"categorie\": \"Alimentation\", \"Transport\", \"Loisirs\", \"Autre\" ou null\n"
            "}\n"
            "Ne renvoie aucun texte avant ou après le JSON."
        )
        analysis_raw = call_groq_api(prompt_agent_1, user_text, require_json=True)
        agent1_data = json.loads(analysis_raw)

        # --- AGENT 2 : TEXT-TO-SQL ENGINEER ---
        schema_info = "Table 'expenses' avec colonnes: id (INTEGER), montant (REAL), categorie (TEXT), description (TEXT), date (TIMESTAMP)"
        prompt_agent_2 = (
            f"Tu es l'Agent 2 (Expert SQL). En fonction du schéma suivant : {schema_info}, "
            f"génère UNIQUEMENT la requête SQL SQLite correspondant à l'analyse de l'Agent 1.\n"
            "Exemple ADD: INSERpython app.pyT INTO expenses (montant, categorie, description) VALUES (50, 'Alimentation', 'texte utilisateur');\n"
            "Exemple QUERY: SELECT SUM(montant) FROM expenses;\n"
            "Interdiction d'inclure du Markdown ou des blocs de code (pas de ```sql). Renvoie la ligne SQL brute directement."
        )
        user_payload_for_agent2 = f"Texte initial: {user_text} | Analyse Agent 1: {json.dumps(agent1_data)}"
        generated_sql = call_groq_api(prompt_agent_2, user_payload_for_agent2, require_json=False)
        
        # Nettoyage de sécurité au cas où le modèle ajouterait des balises de bloc
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        
        # Log dans le terminal pour suivre l'activité de l'IA en temps réel
        print(f"\n[AGENT 2] Requête SQL générée dynamiquement : {generated_sql}\n")

        # EXÉCUTION DE LA REQUÊTE SQL GÉNÉRÉE DYNAMIQUEMENT
        db_execution_result = execute_generated_sql(generated_sql)

        # --- AGENT 3 : CONSEILLER FINANCIER (SYNTHÈSE) ---
        prompt_agent_3 = (
            "Tu es l'Agent 3 (Conseiller Financier). Reçois l'instruction initiale de l'utilisateur, "
            "la requête SQL exécutée, ainsi que le résultat brut de la base de données. Synthétise une réponse "
            "claire, amicale et professionnelle en français pour l'utilisateur. Donne un court conseil budgétaire si pertinent."
        )
        context_agent_3 = f"Instruction utilisateur: {user_text} | Requête SQL exécutée: {generated_sql} | Retour BDD: {db_execution_result}"
        final_response = call_groq_api(prompt_agent_3, context_agent_3, require_json=False)

        return jsonify({
            "status": "success",
            "agent1_intent": agent1_data.get("intention"),
            "agent2_sql": generated_sql,
            "db_log": db_execution_result,
            "agent3_answer": final_response
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, montant, categorie, description, date FROM expenses ORDER BY date DESC LIMIT 50")
        rows = cursor.fetchall()
        expenses = [dict(row) for row in rows]
        
        cursor.execute("SELECT categorie, SUM(montant) as total FROM expenses GROUP BY categorie")
        cat_rows = cursor.fetchall()
        categories = {row['categorie']: row['total'] for row in cat_rows}
        
        cursor.execute("SELECT SUM(montant) as total FROM expenses")
        total_row = cursor.fetchone()
        total = total_row['total'] if total_row['total'] else 0
        
        conn.close()
        return jsonify({
            "status": "success",
            "expenses": expenses,
            "categories": categories,
            "total": total
        })
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)