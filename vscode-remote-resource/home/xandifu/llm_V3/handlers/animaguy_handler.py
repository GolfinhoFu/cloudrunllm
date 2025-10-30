"""
Handler para requisições do modo AnimaGuy.
"""

import logging
import uuid
from typing import Dict, Any

from services import rag_service, gemini_service
from utils import firestore_client
from models import PROMPT_ANIMAGUY

logger = logging.getLogger(__name__)

def handle_animaguy_request(text: str, session_id: str = None) -> Dict[str, Any]:
    """
    Processa uma requisição do modo AnimaGuy.
    
    Args:
        text: Mensagem do usuário
        session_id: ID da sessão (opcional, cria nova se None)
        
    Returns:
        Dict: Resposta com 'answer' e 'session_id'
    """
    # Gera ou usa session_id existente
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(f"Nova sessão AnimaGuy criada: {session_id}")
    else:
        logger.info(f"Usando sessão existente: {session_id}")
    
    try:
        # 1. Busca contexto relevante no RAG
        logger.info("Buscando contexto RAG para AnimaGuy...")
        context = rag_service.find_relevant_context(text)
        
        if not context:
            context = "Nenhum contexto adicional da base de conhecimento encontrado."
            logger.warning("RAG não retornou contexto relevante.")
        
        # 2. Monta o prompt do sistema com contexto
        system_prompt = PROMPT_ANIMAGUY.format(context=context)
        
        # 3. Recupera histórico da sessão
        history = firestore_client.get_session_history(session_id)
        
        # 4. Gera resposta com Gemini
        logger.info("Gerando resposta com Gemini...")
        answer = gemini_service.generate_chat_response(
            user_message=text,
            system_prompt=system_prompt,
            history=history
        )
        
        # 5. Atualiza histórico
        history.append({"role": "user", "parts": [text]})
        history.append({"role": "model", "parts": [answer]})
        firestore_client.save_session_history(session_id, history)
        
        logger.info(f"Resposta AnimaGuy gerada com sucesso para sessão {session_id}")
        
        return {
            "answer": answer,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar requisição AnimaGuy: {e}", exc_info=True)
        raise
