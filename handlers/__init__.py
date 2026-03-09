"""
Handlers package - Processadores de requisições.
"""

from .animaguy_handler import handle_animaguy_request
from .pitch_handler import handle_pitch_request

__all__ = [
    'handle_animaguy_request',
    'handle_pitch_request'
]
