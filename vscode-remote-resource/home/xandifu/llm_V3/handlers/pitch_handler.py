"""
Handler para requisições do modo Pitch.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage

from services import rag_service, gemini_service
from utils import firestore_client, get_audio_mime_type
from models import PROMPT_PITCH_INSTRUCTION

logger = logging.getLogger(__name__)

def handle_pitch_request(text: Optional[str] = None, audio_file: Optional[FileStorage] = None) -> Dict[str, Any]:
    """
    Processa uma requisição do modo Pitch.
    
    Args:
        text: Texto do pitch (opcional)
        audio_file: Arquivo de áudio do pitch (opcional)
        
    Returns:
        Dict: Resposta com análise dos investidores e transcrição (se houver áudio)
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Processando pitch {job_id}")
    
    try:
        # 1. Monta o conteúdo do pitch
        pitch_content = ""
        
        if text:
            pitch_content = f"Texto do pitch:\n{text}"
            logger.info(f"Pitch com texto ({len(text)} chars)")
        
        # 2. Busca contexto relevante no RAG
        query_for_rag = text if text else "dicas de pitch para investidores"
        logger.info("Buscando contexto RAG para Pitch...")
        context = rag_service.find_relevant_context(query_for_rag)
        
        if not context:
            context = "Analise o pitch com base em suas melhores práticas de avaliação de negócios."
            logger.warning("RAG não retornou contexto relevante.")
        
        # 3. Processa com áudio ou texto
        if audio_file:
            logger.info(f"Pitch com áudio: {audio_file.filename}")
            
            # Lê o arquivo de áudio
            audio_file.seek(0)
            audio_data = audio_file.read()
            audio_mime_type = get_audio_mime_type(audio_file.filename)
            
            logger.info(f"Áudio: {len(audio_data)} bytes, tipo: {audio_mime_type}")
            
            # Monta o prompt com contexto RAG
            prompt = PROMPT_PITCH_INSTRUCTION.format(
                context=context,
                pitch_content="(Áudio do pitch anexado)"
            )
            
            # Cria job no Firestore (opcional, para tracking)
            firestore_client.create_pitch_job(job_id, {
                "has_audio": True,
                "has_text": bool(text)
            })
            
            # Analisa com Gemini (processamento nativo de áudio)
            result = gemini_service.analyze_pitch_with_audio(
                prompt=prompt,
                audio_data=audio_data,
                audio_mime_type=audio_mime_type
            )
            
            # Adiciona campo de transcrição vazio (Gemini processa internamente)
            result["transcription_text"] = ""
            
            # Atualiza job como completo
            firestore_client.update_pitch_job(job_id, {"status": "COMPLETE", "result": result})
            
        else:
            # Apenas texto
            logger.info("Pitch apenas com texto")
            
            # Monta o prompt com contexto RAG
            prompt = PROMPT_PITCH_INSTRUCTION.format(
                context=context,
                pitch_content=pitch_content
            )
            
            # Cria job no Firestore
            firestore_client.create_pitch_job(job_id, {
                "has_audio": False,
                "has_text": True
            })
            
            # Analisa com Gemini
            result = gemini_service.analyze_pitch_with_text(
                prompt=prompt,
                pitch_text=text
            )
            
            # Adiciona campo de transcrição vazio
            result["transcription_text"] = ""
            
            # Atualiza job como completo
            firestore_client.update_pitch_job(job_id, {"status": "COMPLETE", "result": result})
        
        logger.info(f"Pitch {job_id} processado com sucesso")
        return result
        
    except Exception as e:
        logger.error(f"Erro ao processar pitch {job_id}: {e}", exc_info=True)
        firestore_client.update_pitch_job(job_id, {"status": "ERROR", "error": str(e)})
        raise
