# Arquivo: backend/app.py

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os # Importar para usar variáveis de ambiente

# 1. Configurar Flask para servir o frontend
# O caminho '../frontend' assume que o app.py está em 'backend/'
app = Flask(__name__, static_folder='../frontend', static_url_path='/') 
CORS(app) 

# 2. Usar Variável de Ambiente para a URL do Ollama
# Em um deploy real, você apontaria para um servidor Ollama externo, ou
# para uma API de um provedor de nuvem.
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/generate")

@app.route('/')
def serve_index():
    """Rota que serve o arquivo index.html."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/ask', methods=['POST'])
def ask_llama():
    """
    Recebe uma pergunta e a envia para o endpoint Ollama configurado.
    """
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "Prompt não fornecido"}), 400

    print(f"Recebendo prompt: '{prompt}'")

    ollama_payload = {
        "model": "llama3",  
        "prompt": prompt,
        "stream": False     
    }

    try:
        # A URL agora vem da variável de ambiente, ou do fallback
        response = requests.post(OLLAMA_API_URL, json=ollama_payload)
        response.raise_for_status() 
        
        ollama_response = response.json()
        full_response = ollama_response.get('response', 'Desculpe, não consegui obter uma resposta.')
        
        return jsonify({"answer": full_response})

    except requests.exceptions.RequestException as e:
        error_msg = f"Erro de Conexão: Não foi possível conectar ao agente de IA em {OLLAMA_API_URL}. Verifique se a URL está correta (ex: Render não consegue acessar localhost)."
        print(f"ERRO: {error_msg}")
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": f"Erro interno no servidor: {e}"}), 500

if __name__ == '__main__':
    # O Render/Docker irá definir a porta, mas usamos 5001 para desenvolvimento local
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)