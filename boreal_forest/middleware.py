from django.utils import timezone
from django.conf import settings

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verifica si el usuario tiene un atributo 'timezone' en su perfil
        user_timezone = getattr(request.user, 'timezone', None)
        if user_timezone:
            timezone.activate(user_timezone)  # Activa la zona horaria del usuario
        else:
            timezone.activate(settings.TIME_ZONE)  # Activa la zona horaria por defecto (en settings.py)

        response = self.get_response(request)  # Continúa con el procesamiento de la solicitud
        return response