# Arquivo: backend/app.py (Versão Final e Robusta para Free Tier)

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
HF_TOKEN = os.environ.get("HF_API_TOKEN") 

# 🚀 ALTERAÇÃO FINAL: Trocando para GPT-2 Medium (muito leve e quase sempre ativo)
HF_MODEL_NAME = "gpt2-medium"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL_NAME}"

# --- Rotas da Aplicação ---

@app.route('/')
def serve_index():
    """
    Rota que serve o arquivo index.html, que está dentro da pasta 'static' no container.
    """
    # Usamos app.static_folder para garantir que o caminho seja encontrado.
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/ask', methods=['POST'])
def ask_ai_agent():
    """
    Recebe uma pergunta, envia para a Hugging Face Inference API e retorna a resposta.
    """
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "Prompt não fornecido"}), 400

    if not HF_TOKEN:
        print("AVISO: Variável HF_API_TOKEN não está configurada.")
        
    print(f"Recebendo prompt: '{prompt}'")

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Payload no formato da API de Inferência para Text Generation
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 100, 
            "temperature": 0.7,
            "return_full_text": False 
        }
    }

    try:
        # Envia a requisição para o servidor Hugging Face
        # 💡 Adicionando timeout de 60 segundos para evitar que o Render trave
        response = requests.post(
            HF_API_URL, 
            headers=headers,
            json=payload,
            timeout=60 
        )
        
        # Lançar erro para 4xx ou 5xx
        response.raise_for_status() 
        
        hf_response = response.json()
        
        # Extrai o texto da resposta
        if hf_response and isinstance(hf_response, list) and 'generated_text' in hf_response[0]:
            full_response = hf_response[0]['generated_text'].strip()
        else:
            # Caso o retorno não seja a lista esperada
            full_response = f"Desculpe, a IA retornou um formato inesperado. Detalhes do retorno: {str(hf_response)}"
        
        print(f"Resposta obtida com sucesso do modelo {HF_MODEL_NAME}.")

        return jsonify({"answer": full_response})

    except requests.exceptions.RequestException as e:
        error_details = "Sem detalhes na resposta JSON."
        status_code = "Desconhecido"
        
        if response is not None:
             status_code = response.status_code
             try:
                 # Tenta ler o JSON de erro se ele existir (muitas vezes é um 503 com JSON)
                 error_details = response.json().get('error', 'Sem detalhes na resposta JSON.')
             except requests.exceptions.JSONDecodeError:
                 # Se não for JSON, pegamos o texto puro, que pode ser uma mensagem de "Loading"
                 error_details = response.text 
        
        error_msg = f"Houve um problema de comunicação com o Agente LexAI (Status {status_code})."
        
        # 💡 Mensagem específica para o free tier
        if "is currently loading" in error_details or status_code in ["503", "504"]:
            error_msg += "\nO modelo está em modo de espera (sleep mode) ou carregando. Por favor, tente novamente em 15 segundos."
        elif status_code == 401:
            error_msg += "\nErro de Autorização: Verifique se a variável HF_API_TOKEN está correta no Render."
            
        print(f"ERRO DE REQUISIÇÃO IA: {e}")
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": f"Erro interno no servidor: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
