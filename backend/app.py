# Arquivo: backend/app.py (Versão 3.0 para Hugging Face)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os 
import json # Usado para manipulação de payloads mais complexos

# --- Configurações da Aplicação ---
app = Flask(__name__) 
CORS(app) 

# --- Variáveis de Ambiente ---
# O Render definirá a porta, mas usamos 5001 para desenvolvimento local
PORT = int(os.environ.get("PORT", 5001))

# O TOKEN de API será lido da variável de ambiente no Render.
# EX: HF_API_TOKEN
HF_TOKEN = os.environ.get("HF_API_TOKEN") 

# ⚠️ ALTERAÇÃO AQUI: Trocando para GPT-2 (mais estável no free Inference API)
HF_MODEL_NAME = "openai-community/gpt2"
# O endpoint é gerado com base no nome do modelo:
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL_NAME}"


# --- Rotas da Aplicação ---

@app.route('/')
def serve_index():
    """
    Rota que serve o arquivo index.html.
    O index.html está agora dentro da pasta 'static'.
    """
    # ⚠️ ALTERAÇÃO AQUI: Agora ele envia o arquivo 'index.html' da pasta 'static'
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
        return jsonify({"error": "Token de API (HF_API_TOKEN) não configurado no Render."}), 500

    print(f"Recebendo prompt: '{prompt}'")

    # Headers para autenticação (Chave Secreta via Variável de Ambiente)
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Payload no formato da API de Inferência para Text Generation
    # Adicionamos a tag do prompt para o modelo Mistral-Instruct
    full_prompt = f"<s>[INST] {prompt} [/INST]"
    
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": 100, # Limitar a resposta para não gastar muitos créditos
            "temperature": 0.7,
            "return_full_text": False # Queremos apenas a parte gerada pela IA
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
            full_response = "Desculpe, a IA retornou uma resposta inesperada."
        
        print("Resposta do Agente LexAI obtida com sucesso.")

        return jsonify({"answer": full_response})

    except requests.exceptions.RequestException as e:
        error_msg = f"Erro na requisição IA: {e}. "
        print(f"ERRO: {error_msg}")
        # Retorna o erro da resposta se for um erro do lado do HF (ex: "Model not found")
        try:
             error_details = response.json().get('error', 'Sem detalhes.')
        except:
             error_details = str(e)

        return jsonify({"error": f"Erro do Agente LexAI: {error_details}"}), 500
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": f"Erro interno no servidor: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)