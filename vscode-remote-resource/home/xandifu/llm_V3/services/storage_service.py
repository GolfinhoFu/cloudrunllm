"""
Serviço para integração com Google Cloud Storage.
"""

import logging
from google.cloud import storage
from typing import Optional

import config

logger = logging.getLogger(__name__)

class StorageService:
    """Serviço para operações com Google Cloud Storage."""
    
    def __init__(self):
        """Inicializa o serviço de Storage."""
        self.client: Optional[storage.Client] = None
        self.rag_bucket: Optional[storage.Bucket] = None
        self._initialize()
    
    def _initialize(self):
        """Inicializa o cliente GCS e o bucket RAG."""
        try:
            self.client = storage.Client(project=config.PROJECT_ID)
            
            if config.GCS_RAG_BUCKET_NAME:
                self.rag_bucket = self.client.bucket(config.GCS_RAG_BUCKET_NAME)
                logger.info(f"Bucket RAG '{config.GCS_RAG_BUCKET_NAME}' inicializado.")
            else:
                logger.warning("GCS_RAG_BUCKET_NAME não configurado.")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente GCS: {e}", exc_info=True)
    
    def download_rag_files(self) -> bool:
        """
        Baixa os arquivos do índice RAG do GCS para o diretório local /tmp/.
        
        Returns:
            bool: True se download bem-sucedido, False caso contrário
        """
        if not self.rag_bucket:
            logger.error("Bucket RAG não inicializado.")
            return False
        
        try:
            # Download do índice FAISS
            logger.info("Baixando faiss_index.bin do GCS...")
            index_blob = self.rag_bucket.blob("faiss_index.bin")
            index_blob.download_to_filename(config.RAG_INDEX_PATH)
            logger.info(f"faiss_index.bin baixado para {config.RAG_INDEX_PATH}")
            
            # Download dos chunks de texto
            logger.info("Baixando text_chunks.json do GCS...")
            chunks_blob = self.rag_bucket.blob("text_chunks.json")
            chunks_blob.download_to_filename(config.RAG_CHUNKS_PATH)
            logger.info(f"text_chunks.json baixado para {config.RAG_CHUNKS_PATH}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao baixar arquivos RAG do GCS: {e}", exc_info=True)
            return False
    
    def upload_file(self, local_path: str, blob_name: str, bucket_name: Optional[str] = None) -> Optional[str]:
        """
        Faz upload de um arquivo para o GCS.
        
        Args:
            local_path: Caminho local do arquivo
            blob_name: Nome do blob no GCS
            bucket_name: Nome do bucket (usa RAG bucket se None)
            
        Returns:
            str: URI do GCS (gs://bucket/blob) ou None se falhar
        """
        try:
            if bucket_name:
                bucket = self.client.bucket(bucket_name)
            else:
                bucket = self.rag_bucket
            
            if not bucket:
                logger.error("Nenhum bucket disponível para upload.")
                return None
            
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(local_path)
            
            gcs_uri = f"gs://{bucket.name}/{blob_name}"
            logger.info(f"Arquivo enviado com sucesso: {gcs_uri}")
            return gcs_uri
            
        except Exception as e:
            logger.error(f"Erro ao fazer upload de arquivo: {e}", exc_info=True)
            return None

# Instância global do serviço Storage (singleton)
storage_service = StorageService()
