"""
Serviço LLM V3 - API Flask principal.

Serviço monolítico com:
- Gemini Only (processamento de áudio nativo)
- RAG com FAISS (base de conhecimento)
- Modo AnimaGuy (chat assistente)
- Modo Pitch (análise de investidores)
"""

import logging
from flask import Flask, request, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

import config
from services import rag_service, storage_service
from handlers import handle_animaguy_request, handle_pitch_request
from utils import validate_mode, validate_animaguy_request, validate_pitch_request

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cria aplicação Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 26 * 1024 * 1024  # 26MB máximo

# Variável global para indicar se a inicialização foi bem-sucedida
initialization_successful = False

def initialize_services():
    """Inicializa todos os serviços na startup."""
    global initialization_successful
    
    logger.info("=" * 60)
    logger.info("Iniciando LLM V3 Service...")
    logger.info("=" * 60)
    
    try:
        # Valida configuração
        logger.info("Validando configuração...")
        config.validate_config()
        logger.info("✓ Configuração válida")
        
        # Baixa índice RAG do GCS
        logger.info("Baixando índice RAG do Google Cloud Storage...")
        if storage_service.download_rag_files():
            logger.info("✓ Arquivos RAG baixados com sucesso")
            
            # Carrega índice RAG em memória
            logger.info("Carregando índice RAG em memória...")
            if rag_service.load_index():
                logger.info("✓ Índice RAG carregado e pronto")
            else:
                logger.warning("⚠ RAG não disponível - serviço continuará sem contexto da base de conhecimento")
        else:
            logger.warning("⚠ Falha ao baixar arquivos RAG - serviço continuará sem RAG")
        
        initialization_successful = True
        logger.info("=" * 60)
        logger.info("✓ Inicialização concluída com sucesso!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ Erro crítico durante inicialização: {e}", exc_info=True)
        logger.error("=" * 60)
        logger.error("Serviço não foi inicializado corretamente")
        logger.error("=" * 60)
        initialization_successful = False

# Inicializa serviços na startup
initialize_services()

@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint de health check."""
    status = {
        "status": "healthy" if initialization_successful else "degraded",
        "rag_available": rag_service.is_available(),
        "service": "llm-v3"
    }
    return jsonify(status), 200 if initialization_successful else 503

@app.route("/process", methods=["POST"])
def process_request():
    """Endpoint principal para processar requisições."""
    
    if not initialization_successful:
        return jsonify({
            "error": "Serviço não inicializado corretamente. Verifique os logs."
        }), 503
    
    try:
        # Valida modo
        mode = request.form.get('mode')
        is_valid, error_msg = validate_mode(mode)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        mode = mode.lower()
        logger.info(f"Requisição recebida - Modo: {mode}")
        
        # Extrai dados da requisição
        text = request.form.get('text')
        audio_file = request.files.get('audio_file')
        
        # Processa de acordo com o modo
        if mode == "animaguy":
            # Valida requisição AnimaGuy
            is_valid, error_msg = validate_animaguy_request(text, audio_file)
            if not is_valid:
                return jsonify({"error": error_msg}), 400
            
            # Processa AnimaGuy
            session_id = request.form.get('session_id')
            result = handle_animaguy_request(text=text, session_id=session_id)
            return jsonify(result), 200
            
        elif mode == "pitch":
            # Valida requisição Pitch
            is_valid, error_msg = validate_pitch_request(text, audio_file)
            if not is_valid:
                return jsonify({"error": error_msg}), 400
            
            # Processa Pitch
            result = handle_pitch_request(text=text, audio_file=audio_file)
            return jsonify(result), 200
        
        else:
            return jsonify({"error": "Modo inválido."}), 400
            
    except RequestEntityTooLarge:
        logger.error("Requisição muito grande")
        return jsonify({"error": "Arquivo muito grande. Máximo: 25MB"}), 413
        
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {e}", exc_info=True)
        return jsonify({
            "error": f"Erro interno do servidor: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handler para 404."""
    return jsonify({"error": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para 500."""
    logger.error(f"Erro interno: {error}", exc_info=True)
    return jsonify({"error": "Erro interno do servidor"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)
