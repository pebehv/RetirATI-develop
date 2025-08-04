from .models import UserSettings

def user_settings(request):
    """Context processor para proporcionar configuraciones del usuario a todos los templates"""
    if request.user.is_authenticated:
        settings = UserSettings.get_user_settings(request.user)
        return {
            'user_settings': settings
        }
    return {
        'user_settings': None
    } 