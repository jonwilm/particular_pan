import re
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Lead
from django.contrib.auth import get_user_model

User = get_user_model()

class LeadResource(resources.ModelResource):
    # Mapeamos el productor por ID desde el JSON/Excel
    productor = fields.Field(
        column_name='productor_id',
        attribute='productor',
        widget=ForeignKeyWidget(User, 'id')
    )

    class Meta:
        model = Lead
        # DEFINIMOS EL DNI COMO LLAVE ÚNICA DE IMPORTACIÓN
        import_id_fields = ('dni',)
        
        fields = (
            'full_name', 
            'dni', 
            'phone', 
            'email', 
            'birthdate', 
            'status', 
            'observations', 
            'productor'
        )
        # Si el DNI ya existe y los datos son iguales, ignora la fila
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        """Limpieza del DNI antes de cualquier validación"""
        dni_raw = str(row.get('dni', ''))
        row['dni'] = re.sub(r'[^0-9]', '', dni_raw)

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """
        Esta es la clave: 
        Si 'original' no es None, significa que el registro YA existe en la BD.
        Retornamos True para que ignore la línea por completo.
        """
        if original.pk:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)