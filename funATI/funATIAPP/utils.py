from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import UserSettings
import logging

logger = logging.getLogger(__name__)

def send_notification_email(notification):
    """
    Envía un correo electrónico de notificación al usuario si tiene habilitadas las notificaciones por correo.
    
    Args:
        notification: Instancia del modelo Notification
    """
    try:
        # Verificar si el usuario tiene habilitadas las notificaciones por correo
        user_settings = UserSettings.get_user_settings(notification.recipient)
        if not user_settings.email_notifications:
            return False
        
        # Verificar que el usuario tenga email
        if not notification.recipient.email:
            logger.warning(f"Usuario {notification.recipient.username} no tiene email configurado")
            return False
        
        # Configurar el asunto y contenido según el tipo de notificación
        subject = ""
        message = ""
        
        if notification.notification_type == 'follow':
            subject = f"🚀 {notification.sender.username} te está siguiendo en FunATI"
            message = f"""
            ¡Hola {notification.recipient.username}!
            
            {notification.sender.username} comenzó a seguirte en FunATI.
            
            ¡Entra a FunATI para ver tu perfil y conectar con más personas!
            
            ---
            Este email fue enviado desde FunATI.
            Si no quieres recibir más notificaciones por correo, puedes desactivarlas en tu configuración.
            """
            
        elif notification.notification_type == 'friend':
            subject = f"🤝 {notification.sender.username} es ahora tu amigo en FunATI"
            message = f"""
            ¡Hola {notification.recipient.username}!
            
            {notification.sender.username} es ahora tu amigo en FunATI.
            
            ¡Entra a FunATI para chatear y compartir momentos juntos!
            
            ---
            Este email fue enviado desde FunATI.
            Si no quieres recibir más notificaciones por correo, puedes desactivarlas en tu configuración.
            """
            
        elif notification.notification_type == 'comment':
            subject = f"💬 {notification.sender.username} respondió a tu publicación en FunATI"
            comment_preview = notification.comment.content[:100] + ("..." if len(notification.comment.content) > 100 else "")
            message = f"""
            ¡Hola {notification.recipient.username}!
            
            {notification.sender.username} respondió a tu publicación:
            
            "{comment_preview}"
            
            ¡Entra a FunATI para ver la respuesta completa y seguir la conversación!
            
            ---
            Este email fue enviado desde FunATI.
            Si no quieres recibir más notificaciones por correo, puedes desactivarlas en tu configuración.
            """
        
        # Enviar el correo
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        return False 