from channels.auth import AuthMiddlewareStack
import logging

logger = logging.getLogger(__name__)

def QueryAuthMiddlewareStack(inner):
    """
    Simplified middleware stack that just uses Django's standard auth
    """
    return AuthMiddlewareStack(inner) 