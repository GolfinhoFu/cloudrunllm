"""
Validadores para requisições HTTP.
"""

import logging
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

def validate_animaguy_request(text: Optional[str], audio_file: Optional[FileStorage]) -> Tuple[bool, Optional[str]]:
    """
    Valida uma requisição do modo AnimaGuy.
    
    Args:
        text: Texto da mensagem do usuário
        audio_file: Arquivo de áudio (deve ser None para AnimaGuy)
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not text:
        return False, "Modo 'animaguy' requer o campo 'text'."
    
    if audio_file:
        return False, "Modo 'animaguy' não aceita 'audio_file'. Use 'text' apenas."
    
    if len(text.strip()) == 0:
        return False, "O campo 'text' não pode estar vazio."
    
    if len(text) > 5000:
        return False, "O campo 'text' excede o limite de 5000 caracteres."
    
    return True, None


def validate_pitch_request(text: Optional[str], audio_file: Optional[FileStorage]) -> Tuple[bool, Optional[str]]:
    """
    Valida uma requisição do modo Pitch.
    
    Args:
        text: Texto do pitch (opcional)
        audio_file: Arquivo de áudio do pitch (opcional)
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not text and not audio_file:
        return False, "Modo 'pitch' requer pelo menos 'text' ou 'audio_file'."
    
    # Valida texto se fornecido
    if text:
        if len(text.strip()) == 0:
            return False, "O campo 'text' não pode estar vazio."
        
        if len(text) > 10000:
            return False, "O campo 'text' excede o limite de 10000 caracteres."
    
    # Valida áudio se fornecido
    if audio_file:
        # Verifica se é um arquivo válido
        if not audio_file.filename:
            return False, "Arquivo de áudio inválido."
        
        # Verifica extensão do arquivo
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.webm'}
        file_ext = '.' + audio_file.filename.rsplit('.', 1)[-1].lower() if '.' in audio_file.filename else ''
        
        if file_ext not in allowed_extensions:
            return False, f"Formato de áudio não suportado. Use: {', '.join(allowed_extensions)}"
        
        # Verifica tamanho do arquivo (máximo 25MB)
        audio_file.seek(0, 2)  # Vai para o final do arquivo
        file_size = audio_file.tell()
        audio_file.seek(0)  # Volta para o início
        
        max_size = 25 * 1024 * 1024  # 25MB
        if file_size > max_size:
            return False, f"Arquivo de áudio muito grande. Máximo: 25MB. Tamanho: {file_size / (1024*1024):.1f}MB"
        
        if file_size == 0:
            return False, "Arquivo de áudio está vazio."
    
    return True, None


def validate_mode(mode: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Valida o modo de operação.
    
    Args:
        mode: Modo solicitado ('animaguy' ou 'pitch')
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not mode:
        return False, "Requisição inválida. Forneça o campo 'mode'."
    
    valid_modes = {'animaguy', 'pitch'}
    if mode.lower() not in valid_modes:
        return False, f"Modo inválido. Use 'animaguy' ou 'pitch'."
    
    return True, None


def get_audio_mime_type(filename: str) -> str:
    """
    Retorna o MIME type baseado na extensão do arquivo.
    
    Args:
        filename: Nome do arquivo
        
    Returns:
        str: MIME type
    """
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    mime_types = {
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'm4a': 'audio/mp4',
        'ogg': 'audio/ogg',
        'flac': 'audio/flac',
        'aac': 'audio/aac',
        'webm': 'audio/webm'
    }
    
    return mime_types.get(extension, 'audio/mpeg')  # Default para mp3
