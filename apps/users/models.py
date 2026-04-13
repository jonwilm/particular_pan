from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, dni, password=None, **extra_fields):
        if not dni:
            raise ValueError('El DNI es obligatorio')
        extra_fields.setdefault('is_active', True)
        user = self.model(dni=dni, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, dni, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(dni, password, **extra_fields)


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
    
    dni = models.CharField('DNI', max_length=20, unique=True)
    email = models.EmailField('Email', null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'dni'
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
        return f"{self.get_full_name() or self.dni}"