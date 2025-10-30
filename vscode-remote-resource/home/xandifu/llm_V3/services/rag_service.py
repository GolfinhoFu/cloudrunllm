"""
Serviço RAG (Retrieval-Augmented Generation) usando FAISS.
"""

import logging
import json
import numpy as np
import faiss
import google.generativeai as genai
from typing import List, Optional

import config

logger = logging.getLogger(__name__)


class RAGService:
    """Serviço para busca de contexto relevante usando FAISS."""
    
    def __init__(self):
        """Inicializa o serviço RAG."""
        self.index: Optional[faiss.Index] = None
        self.text_chunks: Optional[List[str]] = None
        self.is_loaded = False
        
    def load_index(self) -> bool:
        """
        Carrega o índice FAISS e os chunks de texto do disco.
        
        Returns:
            bool: True se carregado com sucesso, False caso contrário
        """
        if self.is_loaded:
            logger.info("Índice RAG já carregado em memória.")
            return True
            
        try:
            logger.info("Carregando índice FAISS...")
            self.index = faiss.read_index(config.RAG_INDEX_PATH)
            
            logger.info("Carregando chunks de texto...")
            with open(config.RAG_CHUNKS_PATH, 'r', encoding='utf-8') as f:
                self.text_chunks = json.load(f)
            
            self.is_loaded = True
            logger.info(f"Índice RAG carregado com sucesso. Total de chunks: {len(self.text_chunks)}")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Arquivos do índice RAG não encontrados: {e}")
            logger.warning("O serviço continuará sem RAG. As respostas não terão contexto da base de conhecimento.")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar índice RAG: {e}", exc_info=True)
            return False
    
    def find_relevant_context(self, query: str, k: int = None) -> str:
        """
        Encontra os chunks de texto mais relevantes para uma consulta.
        
        Args:
            query: Texto da consulta do usuário
            k: Número de chunks a recuperar (usa config.RAG_TOP_K se None)
            
        Returns:
            str: Contexto relevante concatenado, ou string vazia se RAG não disponível
        """
        if not self.is_loaded:
            logger.warning("RAG não está carregado. Tentando carregar...")
            if not self.load_index():
                return ""
        
        if k is None:
            k = config.RAG_TOP_K
            
        try:
            # Gera embedding para a consulta
            logger.debug(f"Gerando embedding para consulta: '{query[:50]}...'")
            result = genai.embed_content(
                model=config.EMBEDDING_MODEL,
                content=query,
                task_type="retrieval_query"
            )
            query_embedding = np.array([result['embedding']], dtype='float32')
            
            # Busca no índice FAISS
            distances, indices = self.index.search(query_embedding, k)
            
            # Concatena os chunks relevantes
            context_parts = []
            for idx in indices[0]:
                if 0 <= idx < len(self.text_chunks):
                    context_parts.append(self.text_chunks[idx])
            
            context = "\n\n---\n\n".join(context_parts)
            
            logger.info(f"Encontrados {len(context_parts)} chunks relevantes para a consulta.")
            logger.debug(f"Contexto gerado (primeiros 200 chars): {context[:200]}...")
            
            return context
            
        except Exception as e:
            logger.error(f"Erro durante busca RAG: {e}", exc_info=True)
            return ""
    
    def is_available(self) -> bool:
        """
        Verifica se o serviço RAG está disponível.
        
        Returns:
            bool: True se o índice está carregado e pronto para uso
        """
        return self.is_loaded and self.index is not None and self.text_chunks is not None


# Instância global do serviço RAG (singleton)
rag_service = RAGService()
