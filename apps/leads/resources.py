import re
import unicodedata
from import_export import resources, fields
from .models import Lead

class LeadResource(resources.ModelResource):
    # Dejamos los column_name en MAYÚSCULAS para que la exportación salga así
    full_name = fields.Field(attribute='full_name', column_name='NOMBRE')
    dni = fields.Field(attribute='dni', column_name='DNI')
    phone = fields.Field(attribute='phone', column_name='TELEFONO')
    email = fields.Field(attribute='email', column_name='EMAIL')
    birthdate = fields.Field(attribute='birthdate', column_name='FECHA DE NACIMIENTO')
    observations = fields.Field(attribute='observations', column_name='OBSERVACIONES')
    
    status = fields.Field(attribute='get_status_display', column_name='ESTADO', readonly=True)
    productor = fields.Field(attribute='productor__get_full_name', column_name='PRODUCTOR', readonly=True)
    n_poliza = fields.Field(attribute='n_poliza', column_name='NRO DE POLIZA', readonly=True)
    date_creation = fields.Field(attribute='date_creation', column_name='FECHA DE REGISTRO', readonly=True)
    date_first_contact = fields.Field(attribute='date_first_contact', column_name='FECHA PRIMER CONTACTO', readonly=True)
    date_last_contact = fields.Field(attribute='date_last_contact', column_name='FECHA ULTIMO CONTACTO', readonly=True)

    class Meta:
        model = Lead
        import_id_fields = ('dni',)
        fields = ('full_name', 'dni', 'phone', 'email', 'birthdate', 'observations', 'status', 'productor', 'n_poliza', 'date_creation', 'date_first_contact', 'date_last_contact')
        skip_unchanged = True
        raise_errors = False 

    def before_import_row(self, row, **kwargs):
        """
        Esta es la clave: 
        Normalizamos lo que viene del Excel pero lo guardamos en 'row' 
        usando las llaves en MAYÚSCULAS exactas que definimos arriba.
        """
        # Mapeo de: "encabezado normalizado" -> "Nombre exacto en fields.Field"
        mapeo_identidad = {
            'nombre': 'NOMBRE',
            'dni': 'DNI',
            'telefono': 'TELEFONO',
            'email': 'EMAIL',
            'fecha de nacimiento': 'FECHA DE NACIMIENTO',
            'observaciones': 'OBSERVACIONES'
        }

        new_row = {}
        for key, value in row.items():
            # 1. Normalizamos la llave del Excel (ej: 'Teléfono' -> 'telefono')
            clean_key = ''.join(
                c for c in unicodedata.normalize('NFD', str(key).lower())
                if unicodedata.category(c) != 'Mn'
            ).strip()

            # 2. Si la columna existe en nuestro mapeo, la guardamos con el nombre oficial
            if clean_key in mapeo_identidad:
                official_name = mapeo_identidad[clean_key]
                new_row[official_name] = value.strip() if isinstance(value, str) else value
        
        # 3. Limpiamos y actualizamos la fila
        row.clear()
        row.update(new_row)

        # 4. Lógica de limpieza usando las llaves oficiales (MAYÚSCULAS)
        dni_raw = str(row.get('DNI') or '')
        row['DNI'] = re.sub(r'[^0-9]', '', dni_raw)
        
        if row.get('OBSERVACIONES') is None:
            row['OBSERVACIONES'] = ""

    def skip_row(self, instance, original, row, import_validation_errors=None):
        # Para skip_row, la librería ya mapeó 'DNI' al atributo 'dni' de la instancia
        if original and original.pk:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)