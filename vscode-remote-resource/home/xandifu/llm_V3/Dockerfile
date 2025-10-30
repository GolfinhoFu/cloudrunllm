# Use Python 3.11 slim como base
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos de dependências
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Cria diretório /tmp para os arquivos RAG
RUN mkdir -p /tmp

# Expõe a porta 8080
EXPOSE 8080

# Define variáveis de ambiente padrão
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Comando para iniciar a aplicação com gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 2 --timeout 300 main:app
