from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El Email es obligatorio')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ADMIN = 'ADMIN'
    SUPERVISOR = 'SUPERVISOR'
    PRODUCTOR = 'PRODUCTOR'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrador'),
        (SUPERVISOR, 'Supervisor'),
        (PRODUCTOR, 'Productor'),
    ]
    
    username = None
    
    role = models.CharField(
        'Rol del usuario',
        max_length=20,
        choices=ROLE_CHOICES,
        default=PRODUCTOR
    )
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productores',
        limit_choices_to={'role': SUPERVISOR},
        verbose_name='Supervisor a cargo'
    )
    
    dni = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def clean(self):
        if self.supervisor != None:
            if self.role == self.SUPERVISOR:
                raise ValidationError("Un SUPERVISOR no puede tener un SUPERVISOR asignado.")
            if self.role == self.ADMIN:
                raise ValidationError("Un ADMINISTRADOR no puede tener un SUPERVISOR asignado.")
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.get_full_name() or self.email}"