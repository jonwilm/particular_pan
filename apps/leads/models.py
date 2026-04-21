import re
from datetime import date
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone

class Lead(models.Model):
    GENDER = (
        ('MASCULINO', 'Masculino'),
        ('FEMENINO', 'Femenino'),
        ('OTRO', 'Otro'),
    )
    STATUS = (
        ('PENDIENTE', 'Pendiente'),
        ('CONTACTADO', 'Contactado'),
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
    gender = models.CharField(
        'Sexo',
        max_length=20, 
        choices=GENDER, 
        default='OTRO'
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
        null=True,
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
    quote = models.FileField(
        "Cotización en PDF",
        upload_to='leads/cotizaciones/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        null=True, 
        blank=True,
        help_text="Opcional: Cargar PDF de cotización."
    )
    n_poliza = models.CharField(
        'Número de Póliza',
        max_length=50,
        blank=True,
        null=True,
        help_text="Opcional: Cargar solo si la venta está cerrada."
    )
    poliza = models.FileField(
        "Póliza en PDF",
        upload_to='leads/polizas/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        null=True, 
        blank=True,
        help_text="Opcional: Cargar solo PDF si la venta está cerrada."
    )
    date_creation = models.DateTimeField('Creación', auto_now_add=True)
    date_first_contact = models.DateTimeField('Primer Contacto', null=True, blank=True)
    date_last_contact = models.DateTimeField('Último Contacto', null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Si el nombre existe, lo convertimos a mayúsculas
        if self.full_name:
            self.full_name = self.full_name.upper()
        
        # Opcional: También puedes asegurar que el email sea siempre minúsculas
        if self.email:
            self.email = self.email.lower()
            
        # Limpia el DNI antes de guardar en cualquier caso
        if self.dni:
            self.dni = re.sub(r'[^0-9]', '', str(self.dni))
            
        # Si hay un número de póliza y el estado no es ya 'VENTA_CERRADA'
        if self.n_poliza and self.n_poliza.strip():
            self.status = 'VENTA_CERRADA'
            
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Prospecto - Potencial Cliente'
        verbose_name_plural = 'Prospectos - Potenciales Clientes '
        ordering = ['-date_creation']

    @property
    def age(self):
        if self.birthdate:
            today = date.today()
            return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        return None
    
    @property
    def n_records(self):
        return self.historial_lead.count()

    def __str__(self):
        return f"{self.full_name}"
    
    
class LeadManagement(models.Model):
    lead = models.ForeignKey(
        Lead, 
        on_delete=models.CASCADE, 
        related_name='historial_lead'
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
        'Respuesta del prospecto',
        blank=True
    )
    # new_status = models.CharField(
    #     'Nuevo Estado',
    #     max_length=20,
    #     choices=Lead.STATUS,
    # )
    next_contact_date = models.DateField(
        'Proximo Contacto',
        blank=True,
        null=True
    )
    create_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Gestión de Prospectos'
        verbose_name_plural = 'Historial de Gestion'
        
    def __str__(self):
        count = self.lead.historial_lead.filter(id__lte=self.id).count() or "Nuevo"
        # estado_nombre = self.get_new_status_display()
        # return f"Mensaje {count} - Estado: {estado_nombre}"
        return f"Mensaje {count}"
        
    def save(self, *args, **kwargs):
        # 1. Ejecutar el guardado normal del historial
        super().save(*args, **kwargs)
        # 2. Actualizar datos en el Lead vinculado
        lead = self.lead
        # Actualizar Status
        # lead.status = self.new_status
        # Actualizar Fecha Primer Contacto (solo si es el primer registro)
        if not lead.date_first_contact:
            lead.date_first_contact = self.date
        # Actualizar Fecha Último Contacto (siempre la más reciente)
        # Comparamos para asegurar que si se carga un historial viejo no pise la fecha actual
        if not lead.date_last_contact or self.date > lead.date_last_contact:
            lead.date_last_contact = self.date
            
        lead.save()
        
        
class WhatsappMessage(models.Model):
    title = models.CharField('Título de la opción', max_length=100)
    content = models.TextField('Texto del mensaje')
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Mensaje de WhatsApp'
        verbose_name_plural = 'Mensajes de WhatsApp'

    def __str__(self):
        return self.title