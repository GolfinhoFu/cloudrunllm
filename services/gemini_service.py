"""
Serviço para integração com Google Gemini API.
"""

import logging
import json
import google.generativeai as genai
from typing import Dict, Any, List, Optional

import config

logger = logging.getLogger(__name__)

class GeminiService:
    """Serviço para interação com a API Gemini."""
    
    def __init__(self):
        """Inicializa o serviço Gemini."""
        self.is_configured = False
        self._configure()
    
    def _configure(self):
        """Configura a API Gemini com a chave de API."""
        try:
            if not config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY não configurada")
            
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.is_configured = True
            logger.info("Serviço Gemini configurado com sucesso.")
            
        except Exception as e:
            logger.error(f"Erro ao configurar Gemini API: {e}", exc_info=True)
            self.is_configured = False
    
    def generate_chat_response(
        self, 
        user_message: str, 
        system_prompt: str,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Gera uma resposta de chat usando Gemini.
        
        Args:
            user_message: Mensagem do usuário
            system_prompt: Prompt do sistema (contexto)
            history: Histórico de conversa (opcional)
            
        Returns:
            str: Resposta gerada pelo modelo
        """
        if not self.is_configured:
            raise RuntimeError("Serviço Gemini não está configurado")
        
        try:
            model = genai.GenerativeModel(config.GEMINI_MODEL)
            
            # Monta o histórico
            chat_history = []
            
            # Adiciona o prompt do sistema
            chat_history.append({"role": "user", "parts": [system_prompt]})
            chat_history.append({"role": "model", "parts": ["Entendido! Estou pronto para ajudar."]})
            
            # Adiciona histórico anterior se existir
            if history:
                chat_history.extend(history)
            
            # Inicia o chat
            chat = model.start_chat(history=chat_history)
            
            # Envia a mensagem do usuário
            response = chat.send_message(user_message)
            
            logger.info(f"Resposta do Gemini gerada com sucesso. Tamanho: {len(response.text)} chars")
            return response.text
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta do Gemini: {e}", exc_info=True)
            raise
    
    def analyze_pitch_with_audio(
        self,
        prompt: str,
        audio_data: bytes,
        audio_mime_type: str
    ) -> Dict[str, Any]:
        """
        Analisa um pitch com áudio usando Gemini (processamento nativo de áudio).
        
        Args:
            prompt: Prompt de instrução para análise
            audio_data: Dados do arquivo de áudio
            audio_mime_type: Tipo MIME do áudio (ex: 'audio/mpeg')
            
        Returns:
            Dict: Resposta JSON parseada com análise dos investidores
        """
        if not self.is_configured:
            raise RuntimeError("Serviço Gemini não está configurado")
        
        try:
            # Configura o modelo para gerar JSON
            model = genai.GenerativeModel(
                config.GEMINI_MODEL,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Prepara o conteúdo multimodal
            contents = [
                prompt,
                {
                    "mime_type": audio_mime_type,
                    "data": audio_data
                }
            ]
            
            logger.info(f"Enviando áudio ({len(audio_data)} bytes) para análise do Gemini...")
            response = model.generate_content(contents)
            
            # Parse da resposta JSON
            try:
                result = json.loads(response.text)
                logger.info("Análise de pitch concluída com sucesso.")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Resposta do Gemini não é JSON válido: {response.text[:500]}")
                raise ValueError(f"Resposta inválida do Gemini: {e}")
                
        except Exception as e:
            logger.error(f"Erro ao analisar pitch com áudio: {e}", exc_info=True)
            raise
    
    def analyze_pitch_with_text(
        self,
        prompt: str,
        pitch_text: str
    ) -> Dict[str, Any]:
        """
        Analisa um pitch apenas com texto usando Gemini.
        
        Args:
            prompt: Prompt de instrução para análise
            pitch_text: Texto do pitch
            
        Returns:
            Dict: Resposta JSON parseada com análise dos investidores
        """
        if not self.is_configured:
            raise RuntimeError("Serviço Gemini não está configurado")
        
        try:
            # Configura o modelo para gerar JSON
            model = genai.GenerativeModel(
                config.GEMINI_MODEL,
                generation_config={"response_mime_type": "application/json"}
            )
            
            logger.info(f"Analisando pitch com texto ({len(pitch_text)} chars)...")
            response = model.generate_content(prompt)
            
            # Parse da resposta JSON
            try:
                result = json.loads(response.text)
                logger.info("Análise de pitch concluída com sucesso.")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Resposta do Gemini não é JSON válido: {response.text[:500]}")
                raise ValueError(f"Resposta inválida do Gemini: {e}")
                
        except Exception as e:
            logger.error(f"Erro ao analisar pitch com texto: {e}", exc_info=True)
            raise

# Instância global do serviço Gemini (singleton)
gemini_service = GeminiService()
