# Arquivo: Dockerfile (CORREÇÃO DE CAMINHO)

FROM python:3.11-slim

WORKDIR /usr/src/app

# Copia os arquivos de configuração do Flask
COPY backend/app.py .
COPY requirements.txt .

# ⚠️ ALTERAÇÃO AQUI: Copia o conteúdo do frontend para a pasta 'static' padrão do Flask
# Isso garante que a rota seja simples e que o Flask a encontre facilmente.
COPY frontend/ static/

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD gunicorn --bind 0.0.0.0:$PORT app:app