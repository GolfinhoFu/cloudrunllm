"""
Cliente para operações com Google Firestore.
"""

import logging
from google.cloud import firestore
from typing import Optional, Dict, Any, List

import config

logger = logging.getLogger(__name__)

class FirestoreClient:
    """Cliente para operações com Firestore."""
    
    def __init__(self):
        """Inicializa o cliente Firestore."""
        self.db: Optional[firestore.Client] = None
        self._initialize()
    
    def _initialize(self):
        """Inicializa a conexão com Firestore."""
        try:
            self.db = firestore.Client(project=config.PROJECT_ID)
            logger.info("Cliente Firestore inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao inicializar Firestore: {e}", exc_info=True)
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Recupera o histórico de uma sessão do AnimaGuy.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            List: Lista com histórico de mensagens
        """
        if not self.db:
            logger.error("Firestore não inicializado.")
            return []
        
        try:
            doc_ref = self.db.collection('animaguy_sessions').document(session_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                history = data.get('history', [])
                logger.info(f"Histórico recuperado para sessão {session_id}: {len(history)} mensagens")
                return history
            else:
                logger.info(f"Nenhum histórico encontrado para sessão {session_id}")
                return []
                
        except Exception as e:
            logger.error(f"Erro ao recuperar histórico da sessão {session_id}: {e}", exc_info=True)
            return []
    
    def save_session_history(self, session_id: str, history: List[Dict[str, Any]]) -> bool:
        """
        Salva o histórico de uma sessão do AnimaGuy.
        
        Args:
            session_id: ID da sessão
            history: Lista com histórico de mensagens
            
        Returns:
            bool: True se salvou com sucesso
        """
        if not self.db:
            logger.error("Firestore não inicializado.")
            return False
        
        try:
            doc_ref = self.db.collection('animaguy_sessions').document(session_id)
            doc_ref.set({
                'history': history,
                'last_updated': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Histórico salvo para sessão {session_id}: {len(history)} mensagens")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar histórico da sessão {session_id}: {e}", exc_info=True)
            return False
    
    def create_pitch_job(self, job_id: str, initial_data: Dict[str, Any]) -> bool:
        """
        Cria um job de processamento de pitch no Firestore.
        
        Args:
            job_id: ID do job
            initial_data: Dados iniciais do job
            
        Returns:
            bool: True se criou com sucesso
        """
        if not self.db:
            logger.error("Firestore não inicializado.")
            return False
        
        try:
            doc_ref = self.db.collection('pitch_jobs').document(job_id)
            job_data = {
                'id': job_id,
                'status': 'PROCESSING',
                'timestamp': firestore.SERVER_TIMESTAMP,
                **initial_data
            }
            doc_ref.set(job_data)
            logger.info(f"Job de pitch {job_id} criado no Firestore.")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar job {job_id}: {e}", exc_info=True)
            return False
    
    def update_pitch_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """
        Atualiza um job de processamento de pitch.
        
        Args:
            job_id: ID do job
            updates: Dados a atualizar
            
        Returns:
            bool: True se atualizou com sucesso
        """
        if not self.db:
            logger.error("Firestore não inicializado.")
            return False
        
        try:
            doc_ref = self.db.collection('pitch_jobs').document(job_id)
            doc_ref.update(updates)
            logger.info(f"Job {job_id} atualizado no Firestore.")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar job {job_id}: {e}", exc_info=True)
            return False

# Instância global do cliente Firestore (singleton)
firestore_client = FirestoreClient()
