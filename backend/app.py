# Arquivo: backend/app.py (Versão Corrigida para Hugging Face Gemma 2B)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os 
import json

# --- Configurações da Aplicação ---
# O Flask buscará arquivos estáticos em uma pasta chamada 'static'
app = Flask(__name__) 
CORS(app) 

# --- Variáveis de Ambiente ---
# Porta de execução, lendo do ambiente Render
PORT = int(os.environ.get("PORT", 5001))

# O TOKEN de API será lido da variável de ambiente no Render (HF_API_TOKEN).
HF_TOKEN = os.environ.get("HF_API_TOKEN") 

# 🚀 ALTERAÇÃO: Trocando para Google Gemma 2B (muito estável e melhor que GPT-2 para chat)
HF_MODEL_NAME = "google/gemma-2b-it"
# O endpoint é gerado com base no nome do modelo:
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL_NAME}"


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
    Recebe uma pergunta, envia para a Hugging Face Inference API e retorna a resposta.
    """
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "Prompt não fornecido"}), 400

    # O Token de API é opcional para alguns modelos públicos, mas o header é sempre enviado.
    if not HF_TOKEN:
        print("AVISO: Variável HF_API_TOKEN não está configurada.")
        
    print(f"Recebendo prompt: '{prompt}'")

    # Headers para autenticação (Chave Secreta via Variável de Ambiente)
    headers = {
        # O token é injetado aqui. Se for None, será 'Bearer None', mas o HF pode aceitar.
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Payload no formato da API de Inferência para Text Generation
    # 🐛 CORREÇÃO AQUI: Usando o prompt diretamente, sem tags desnecessárias.
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 150, 
            "temperature": 0.7,
            # Não retornar o prompt completo na resposta
            "return_full_text": False 
        }
    }

    try:
        # Envia a requisição para o servidor Hugging Face
        response = requests.post(
            HF_API_URL, 
            headers=headers,
            json=payload
        )
        response.raise_for_status() # Lança exceção para status de erro (4xx ou 5xx)
        
        # O retorno é uma lista com o objeto de resposta
        hf_response = response.json()
        
        # Extrai o texto da resposta
        if hf_response and isinstance(hf_response, list) and 'generated_text' in hf_response[0]:
            full_response = hf_response[0]['generated_text'].strip()
        else:
            full_response = "Desculpe, a IA retornou uma resposta inesperada. Detalhes: " + str(hf_response)
        
        print(f"Resposta obtida com sucesso do modelo {HF_MODEL_NAME}.")

        return jsonify({"answer": full_response})

    except requests.exceptions.RequestException as e:
        # Tenta extrair detalhes do erro para ajudar na depuração
        error_details = "Sem detalhes."
        try:
             error_details = response.json().get('error', 'Sem detalhes.')
        except:
             pass

        print(f"ERRO DE REQUISIÇÃO IA: {e}")
        return jsonify({"error": f"Erro de API no Hugging Face. Detalhes: {error_details}"}), 500
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": f"Erro interno no servidor: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
