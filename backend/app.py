# Arquivo: backend/app.py (Versão 6.0 para Hugging Face GPT2 Simples)

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

# 🔑 CHAVE: Será lida da variável de ambiente no Render.
HF_TOKEN = os.environ.get("HF_API_TOKEN") 

# Modelo e Endpoint
# 🚀 MODELO ESCOLHIDO: GPT-2 (a versão mais simples e estável para free tier)
HF_MODEL_NAME = "gpt2"
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
    Recebe uma pergunta, envia para o Agente LexAI e retorna a resposta.
    """
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "Prompt não fornecido"}), 400

    if not HF_TOKEN:
        print("AVISO: Variável HF_API_TOKEN não está configurada.")
        
    print(f"Recebendo prompt: '{prompt}'")

    # Headers para autenticação (Chave Secreta via Variável de Ambiente)
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
    
    response = None # Inicializa a variável response fora do try/except

    try:
        # Envia a requisição para o servidor Hugging Face
        response = requests.post(
            HF_API_URL, 
            headers=headers,
            json=payload,
            timeout=60 # Timeout de 60 segundos para evitar que o Render trave em um modelo em sleep
        )
        
        # Lançar erro para 4xx ou 5xx
        response.raise_for_status() 
        
        hf_response = response.json()
        
        # Extrai o texto gerado (a API retorna uma lista)
        if hf_response and isinstance(hf_response, list) and 'generated_text' in hf_response[0]:
            full_response = hf_response[0]['generated_text'].strip()
        else:
            # Caso o retorno não seja o formato esperado
            full_response = f"Desculpe, a IA retornou um formato inesperado. Detalhes do retorno: {str(hf_response)}"
        
        print(f"Resposta obtida com sucesso do modelo {HF_MODEL_NAME}.")

        return jsonify({"answer": full_response})

    except requests.exceptions.RequestException as e:
        # --- Tratamento de Erros da API de Inferência ---
        error_details = "Sem detalhes na resposta JSON."
        status_code = "Desconhecido"
        
        if response is not None:
             status_code = response.status_code
             try:
                 # Tenta ler o JSON de erro
                 error_details = response.json().get('error', 'Sem detalhes na resposta JSON.')
             except requests.exceptions.JSONDecodeError:
                 # Se não for JSON, pegamos o texto puro
                 error_details = response.text 
        
        error_msg = f"Houve um problema de comunicação com o Agente de IA (Status {status_code})."
        
        if "is currently loading" in error_details or status_code in [503, 504]:
            error_msg += "\nO modelo está em modo de espera (sleep mode) ou carregando. Por favor, tente novamente em 15 segundos."
        elif status_code == 401:
            error_msg += "\nErro de Autorização: Verifique se a variável HF_API_TOKEN é a sua nova chave API."
        elif status_code == 404:
            # O 404 no Hugging Face geralmente significa que o endpoint gratuito foi removido.
            error_msg += f"\nErro Crítico: Endpoint {HF_MODEL_NAME} removido ou indisponível para o free tier."
            
        print(f"ERRO DE REQUISIÇÃO IA: {e}")
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": f"Erro interno no servidor: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
