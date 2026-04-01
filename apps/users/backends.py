from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrDNIBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # El argumento 'username' aquí es lo que el usuario escribe en el input de "Login"
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        try:
            # Buscamos al usuario que coincida con el email o con el DNI
            user = User.objects.get(Q(email=username) | Q(dni=username))
        except User.DoesNotExist:
            return None
        
        # Verificamos la contraseña y si el usuario está activo
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None