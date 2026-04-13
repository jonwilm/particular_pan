import re
import unicodedata
from datetime import datetime
from import_export import resources, fields, widgets
from import_export.widgets import DateWidget
from .models import Lead
from apps.users.models import User

class LatinoDateWidget(DateWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if not value: return None
        if isinstance(value, datetime): return value.date()
        try:
            return datetime.strptime(str(value).strip(), '%d/%m/%Y').date()
        except (ValueError, TypeError):
            return super().clean(value, row, *args, **kwargs)

class LeadResource(resources.ModelResource):
    # --- CAMPOS DE IMPORTACIÓN Y EXPORTACIÓN ---
    full_name = fields.Field(attribute='full_name', column_name='NOMBRE')
    dni = fields.Field(attribute='dni', column_name='DNI')
    gender = fields.Field(attribute='gender', column_name='SEXO')
    phone = fields.Field(attribute='phone', column_name='TELEFONO')
    email = fields.Field(attribute='email', column_name='EMAIL')
    birthdate = fields.Field(attribute='birthdate', column_name='FECHA DE NACIMIENTO', widget=LatinoDateWidget(format='%d/%m/%Y'))
    observations = fields.Field(attribute='observations', column_name='OBSERVACIONES')
    
    # Este es el único campo que importa datos (usa el DNI para buscar el objeto User)
    productor = fields.Field(
        attribute='productor', 
        column_name='DNI PRODUCTOR', 
        widget=widgets.ForeignKeyWidget(User, 'dni')
    )
    
    # --- CAMPOS EXTRA (SOLO EXPORTACIÓN) ---
    # Al ser readonly=True, django-import-export NO intentará importarlos
    productor_display = fields.Field(attribute='productor__get_full_name', column_name='PRODUCTOR', readonly=True)
    status = fields.Field(attribute='get_status_display', column_name='ESTADO', readonly=True)
    n_poliza = fields.Field(attribute='n_poliza', column_name='NRO DE POLIZA', readonly=True)
    date_creation = fields.Field(attribute='date_creation', column_name='FECHA DE REGISTRO', readonly=True)
    date_first_contact = fields.Field(attribute='date_first_contact', column_name='FECHA PRIMER CONTACTO', readonly=True)
    date_last_contact = fields.Field(attribute='date_last_contact', column_name='FECHA ULTIMO CONTACTO', readonly=True)

    class Meta:
        model = Lead
        import_id_fields = ('dni',)
        # Todos estos campos aparecerán en tu Excel
        fields = (
            'full_name', 'dni', 'gender', 'phone', 'email', 'birthdate', 'observations', 
            'productor', 'productor_display', 'status', 'n_poliza', 
            'date_creation', 'date_first_contact', 'date_last_contact'
        )
        skip_unchanged = True
        raise_errors = False

    def before_import_row(self, row, **kwargs):
        # 1. Normalización de llaves (Tu lógica actual es correcta)
        mapeo = {'nombre':'NOMBRE', 'dni':'DNI', 'sexo':'SEXO', 'telefono':'TELEFONO', 'email':'EMAIL', 'fecha de nacimiento':'FECHA DE NACIMIENTO', 'observaciones':'OBSERVACIONES', 'dni productor': 'DNI PRODUCTOR'}
        new_row = {}
        for key, value in row.items():
            clean_key = ''.join(c for c in unicodedata.normalize('NFD', str(key).lower()) if unicodedata.category(c) != 'Mn').strip()
            if clean_key in mapeo:
                new_row[mapeo[clean_key]] = value
        
        row.clear()
        row.update(new_row)

        # 2. Limpieza de datos
        row['DNI'] = re.sub(r'[^0-9]', '', str(row.get('DNI') or ''))
        row['NOMBRE'] = str(row.get('NOMBRE') or '').upper()
        row['EMAIL'] = str(row.get('EMAIL') or '').lower()
        gender_raw = str(row.get('SEXO') or '').lower()
        if gender_raw in ['masculino', 'm']:
            row['SEXO'] = 'MASCULINO'
        elif gender_raw in ['femenino', 'f']:
            row['SEXO'] = 'FEMENINO'
        else:
            row['SEXO'] = 'OTRO'
        
        if row.get('OBSERVACIONES') is None:
            row['OBSERVACIONES'] = ""
        
        request = kwargs.get('request')
        if not request: 
            return
        user = request.user
        if user.role == 'PRODUCTOR':
            row['DNI PRODUCTOR'] = user.dni 
        elif user.role == 'SUPERVISOR':
            dni_input = str(row.get('DNI PRODUCTOR', '')).strip()
            try:
                productor = User.objects.get(dni=dni_input, role='PRODUCTOR', supervisor=user)
                row['DNI PRODUCTOR'] = productor.dni 
            except User.DoesNotExist:
                row['DNI PRODUCTOR'] = None

    def skip_row(self, instance, original, row, import_validation_errors=None):
        if not str(row.get('DNI', '')).strip(): return True
        if original and original.pk: return True # Solo crear, no actualizar
        return super().skip_row(instance, original, row, import_validation_errors)