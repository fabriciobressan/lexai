# Arquivo: backend/app.py (Versão Final: Gemini API)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os 
import json

# --- Configurações da Aplicação ---
app = Flask(__name__) 
CORS(app) 

# --- Variáveis de Ambiente ---
PORT = int(os.environ.get("PORT", 5001))

# 🔑 CHAVE: A chave de API do Gemini será lida no Render.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 

# Modelo e Endpoint
GEMINI_MODEL = "gemini-2.5-flash"
# O endpoint usa a chave como um parâmetro de consulta (Query Parameter)
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


# --- Rotas da Aplicação ---

@app.route('/')
def serve_index():
    """
    Rota que serve o arquivo index.html, que está dentro da pasta 'static' no container.
    """
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/ask', methods=['POST'])
def ask_ai_agent():
    """
    Recebe uma pergunta, envia para a LexAI e retorna a resposta.
    """
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "Prompt não fornecido"}), 400

    if not GEMINI_API_KEY:
        return jsonify({"error": "Erro: Variável GEMINI_API_KEY não configurada no Render."}), 500
        
    print(f"Recebendo prompt: '{prompt}'")

    # Payload no formato da Gemini API
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        # 💡 CORREÇÃO AQUI: Mudando 'config' para 'generationConfig'
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300 
        }
    }

    response = None

    try:
        # Envia a requisição para a Gemini API
        response = requests.post(
            GEMINI_API_URL, 
            json=payload,
            timeout=60
        )
        
        response.raise_for_status() # Lançar exceção para status 4xx ou 5xx
        
        gemini_response = response.json()
        
        # Extrair o texto gerado
        candidates = gemini_response.get('candidates')
        if candidates:
            # A resposta está em candidates[0].content.parts[0].text
            full_response = candidates[0]['content']['parts'][0]['text']
        else:
            # Captura de erros de filtro de conteúdo, etc.
            full_response = f"Desculpe, o Agente LexAI retornou um erro inesperado. Detalhes: {str(gemini_response)}"
        
        print(f"Resposta obtida com sucesso do modelo {GEMINI_MODEL}.")

        return jsonify({"answer": full_response})

    except requests.exceptions.RequestException as e:
        # --- Tratamento de Erros da API Gemini ---
        error_details = "Erro de comunicação ou rede."
        status_code = "Desconhecido"
        
        if response is not None:
             status_code = response.status_code
             try:
                 # Tenta ler o JSON de erro do Google (formato específico)
                 error_details = response.json().get('error', {}).get('message', 'Erro desconhecido da API.')
             except:
                 error_details = response.text

        error_msg = f"Houve um problema de comunicação com o Agente LexAI (Status {status_code}). Detalhes: {error_details}"
        
        print(f"ERRO DE REQUISIÇÃO IA: {e}")
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": f"Erro interno no servidor: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
