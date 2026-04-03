import re
from datetime import date
from django.db import models
from django.conf import settings
from django.utils import timezone

class Lead(models.Model):
    STATUS = (
        ('PENDIENTE', 'Pendiente'),
        # ('CONTACTADO', 'Contactado'),
        ('INTERESADO', 'Interesado'),
        ('NO_INTERESADO', 'No Interesado'),
        ('POR_CERRAR_VENTA', 'Por Cerrar Venta'),
        ('VENTA_CERRADA', 'Venta Cerrada'),
    )

    # Datos Personales
    full_name = models.CharField(
        'Nombre Completo',
        max_length=150
    )
    dni = models.CharField(
        'DNI', 
        max_length=20, 
        unique=True
    )
    phone = models.CharField(
        'Teléfono', 
        max_length=50
    )
    email = models.EmailField(
        'Correo Electrónico', 
        blank=True, 
        null=True
    )
    birthdate = models.DateField(
        'Fecha de Nacimiento',
        null=True,
        blank=True
    )
    status = models.CharField(
        'Estado',
        max_length=20, 
        choices=STATUS, 
        default='PENDIENTE'
    )
    observations = models.TextField(
        'Observaciones generales', 
        blank=True
    )
    productor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='my_leads',
        limit_choices_to={'role': 'PRODUCTOR'},
        verbose_name='Productor a Cargo',
        null=True,
        blank=True
    )
    date_creation = models.DateTimeField('Creación', auto_now_add=True)
    date_first_contact = models.DateTimeField('Primer Contacto', null=True, blank=True)
    date_last_contact = models.DateTimeField('Último Contacto', null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Limpia el DNI antes de guardar en cualquier caso
        if self.dni:
            self.dni = re.sub(r'[^0-9]', '', str(self.dni))
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Lead - Potencial Cliente'
        verbose_name_plural = 'Leads - Potenciales Clientes '
        ordering = ['-date_creation']

    @property
    def age(self):
        if self.birthdate:
            today = date.today()
            return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        return None
    
    @property
    def n_records(self):
        return self.historial.count()

    def __str__(self):
        return f"{self.full_name}"
    
    
class LeadManagement(models.Model):
    lead = models.ForeignKey(
        Lead, 
        on_delete=models.CASCADE, 
        related_name='historial'
    )
    date = models.DateTimeField(
        'Fecha de Contacto',
        default=timezone.now
    )
    comment = models.TextField(
        'Comentarios',
        blank=True
    )
    response = models.TextField(
        'Respuesta del Lead',
        blank=True
    )
    new_status = models.CharField(
        'Nuevo Estado',
        max_length=20,
        choices=Lead.STATUS,
    )
    create_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Gestión de Leads'
        verbose_name_plural = 'Historial de Gestion de Leads'
        
    def __str__(self):
        count = self.lead.historial.filter(id__lte=self.id).count() or "Nuevo"
        estado_nombre = self.get_new_status_display()
        return f"Mensaje {count} - Estado: {estado_nombre}"
        
    def save(self, *args, **kwargs):
        # 1. Ejecutar el guardado normal del historial
        super().save(*args, **kwargs)
        # 2. Actualizar datos en el Lead vinculado
        lead = self.lead
        # Actualizar Status
        lead.status = self.new_status
        # Actualizar Fecha Primer Contacto (solo si es el primer registro)
        if not lead.date_first_contact:
            lead.date_first_contact = self.date
        # Actualizar Fecha Último Contacto (siempre la más reciente)
        # Comparamos para asegurar que si se carga un historial viejo no pise la fecha actual
        if not lead.date_last_contact or self.date > lead.date_last_contact:
            lead.date_last_contact = self.date
            
        lead.save()