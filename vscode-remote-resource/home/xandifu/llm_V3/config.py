"""
Configurações e variáveis de ambiente para o serviço LLM V3.
"""

import os

# --- Google Cloud Configuration ---
PROJECT_ID = os.environ.get("PROJECT_ID")
GCS_RAG_BUCKET_NAME = os.environ.get("GCS_RAG_BUCKET_NAME")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- Gemini Configuration ---
GEMINI_MODEL = "gemini-2.0-flash-exp"  # Modelo principal
EMBEDDING_MODEL = "models/text-embedding-004"  # Para embeddings RAG

# --- RAG Configuration ---
RAG_TOP_K = 5  # Número de chunks mais relevantes a recuperar
RAG_INDEX_PATH = "/tmp/faiss_index.bin"  # Caminho local para índice FAISS
RAG_CHUNKS_PATH = "/tmp/text_chunks.json"  # Caminho local para chunks de texto

# --- Server Configuration ---
PORT = int(os.environ.get("PORT", 8080))
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# --- Timeouts ---
REQUEST_TIMEOUT = 300  # 5 minutos
GEMINI_TIMEOUT = 180  # 3 minutos

# --- Validação de Configurações Críticas ---
def validate_config():
    """Valida se todas as variáveis de ambiente críticas estão configuradas."""
    missing = []
    
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not GCS_RAG_BUCKET_NAME:
        missing.append("GCS_RAG_BUCKET_NAME")
    if not PROJECT_ID:
        missing.append("PROJECT_ID")
    
    if missing:
        raise EnvironmentError(
            f"Variáveis de ambiente faltando: {', '.join(missing)}. "
            "Configure-as antes de iniciar o serviço."
        )
