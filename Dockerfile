# Usa uma imagem oficial Python
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /usr/src/app

# Copia os arquivos de configuração do Flask e o frontend
COPY backend/app.py .
COPY requirements.txt .
COPY frontend/ frontend/

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta que o Gunicorn irá usar
EXPOSE 8080

# Comando para rodar a aplicação usando Gunicorn.
# O Gunicorn é o servidor web robusto que o Render usará no lugar do app.run() do Flask.
# 'app:app' significa 'o objeto app dentro do módulo app.py'
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]