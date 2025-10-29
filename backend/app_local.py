# Arquivo: backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
# Permite que o frontend (rodando em outra porta ou localhost) se comunique com o backend
CORS(app) 

# Endpoint da API do Ollama. Se você usou o Docker, esta é a porta padrão.
OLLAMA_API_URL = "http://localhost:11434/api/generate"

@app.route('/api/ask', methods=['POST'])
def ask_llama():
    """
    Recebe uma pergunta, envia para o Ollama e retorna a resposta do Llama 3.
    """
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "Prompt não fornecido"}), 400

    print(f"Recebendo prompt: '{prompt}'")

    # Estrutura de requisição para a API /api/generate do Ollama
    ollama_payload = {
        "model": "llama3",  # O modelo que você especificou
        "prompt": prompt,
        "stream": False     # Não queremos streaming para esta aplicação simples
    }

    try:
        # Envia a requisição para o servidor Ollama
        response = requests.post(
            OLLAMA_API_URL, 
            json=ollama_payload
        )
        response.raise_for_status()  # Lança exceção para status de erro (4xx ou 5xx)
        
        ollama_response = response.json()
        
        # Extrai o texto da resposta
        full_response = ollama_response.get('response', 'Desculpe, não consegui obter uma resposta.')
        
        print("Resposta do Llama 3 obtida com sucesso.")

        return jsonify({"answer": full_response})

    except requests.exceptions.ConnectionError:
        error_msg = "Erro de Conexão: Não foi possível conectar ao servidor Ollama em http://localhost:11434. Verifique se o Docker e o Ollama estão rodando corretamente."
        print(f"ERRO: {error_msg}")
        return jsonify({"error": error_msg}), 500
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição Ollama: {e}")
        return jsonify({"error": f"Erro na requisição Ollama: {e}"}), 500
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": f"Erro interno no servidor: {e}"}), 500

if __name__ == '__main__':
    # Rodar em 0.0.0.0 para garantir acessibilidade, na porta 5000
    app.run(host='0.0.0.0', port=5001, debug=True)