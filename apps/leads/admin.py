import re
from datetime import date, timedelta
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import DateRangeFilter

from .models import Lead, LeadManagement
from .resources import LeadResource


User = get_user_model()


class AgeRangeFilter(admin.SimpleListFilter):
    title = _('Rango de Edad')
    parameter_name = 'age_range'

    def lookups(self, request, model_admin):
        return (
            ('sin_fnac', _('Sin fecha de nacimiento')),
            ('joven', _('Jóvenes (< 25)')),
            ('adulto', _('Adultos (25-50)')),
            ('senior', _('Seniors (> 50)')),
        )

    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == 'sin_fnac':
            return queryset.filter(birthdate__isnull=True)
        if self.value() == 'joven':
            return queryset.filter(birthdate__gt=today.replace(year=today.year - 25))
        if self.value() == 'adulto':
            return queryset.filter(
                birthdate__range=[today.replace(year=today.year - 50), today.replace(year=today.year - 25)]
            )
        if self.value() == 'senior':
            return queryset.filter(birthdate__lt=today.replace(year=today.year - 50))
        
        
class ProductorFilter(admin.SimpleListFilter):
    title = 'Productor'
    parameter_name = 'productor'

    def lookups(self, request, model_admin):
        user = request.user
        # Si es Admin, ve a todos los que tengan rol PRODUCTOR
        if user.is_superuser or user.role == 'ADMIN':
            return [(u.id, u.get_full_name() or u.email) for u in User.objects.filter(role='PRODUCTOR')]
        
        # Si es Supervisor, SOLO ve a sus productores a cargo
        if user.role == 'SUPERVISOR':
            productores = User.objects.filter(supervisor=user, role='PRODUCTOR')
            return [(u.id, u.get_full_name() or u.email) for u in productores]
        
        # Si es Productor, no tiene sentido filtrar por otros, devolvemos vacío o solo a él mismo
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(productor_id=self.value())
        return queryset
    
    
class MonthFilter(admin.SimpleListFilter):
    title = _('Mes de UltimoContacto')
    parameter_name = 'month'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Enero')), ('2', _('Febrero')), ('3', _('Marzo')),
            ('4', _('Abril')), ('5', _('Mayo')), ('6', _('Junio')),
            ('7', _('Julio')), ('8', _('Agosto')), ('9', _('Septiembre')),
            ('10', _('Octubre')), ('11', _('Noviembre')), ('12', _('Diciembre')),
        )

    def queryset(self, request, queryset):
        if self.value():
            # Filtra por el mes en el campo date_last_contact
            return queryset.filter(date_last_contact__month=self.value())
        return queryset


class LeadManagementInline(admin.StackedInline):
    model = LeadManagement
    extra = 0
    fields = ('date', 'comment', 'response', 'new_status', 'create_by')
    readonly_fields = ('create_by',)
    
    def __str__(self):
        return super().__str__()


@admin.register(Lead)
class LeadAdmin(ImportExportModelAdmin):
    resource_class = LeadResource
    list_display = ('full_name', 'dni', 'age_display', 'gender', 'status', 'get_n_records', 'productor', 'date_first_contact', 'date_last_contact', 'date_creation', 'highlight_row')
    list_editable = ()
    list_filter = ('status', 'gender', AgeRangeFilter, ProductorFilter, ('date_last_contact', admin.DateFieldListFilter), ('date_last_contact', DateRangeFilter),)
    search_fields = ('full_name', 'dni', 'phone',)
    inlines = [LeadManagementInline]
    readonly_fields = ('date_creation', 'date_first_contact', 'date_last_contact', 'email_link', 'phone_link', 'age_display')
    
    def get_whatsapp_link(self, phone_number):
        if not phone_number:
            return None
        clean_number = re.sub(r'[^0-9]', '', str(phone_number))
        if len(clean_number) <= 13 and not clean_number.startswith('54'):
            clean_number = f"54{clean_number}"
        return f"https://wa.me/{clean_number}"

    def email_link(self, obj):
        if obj.email:
            return format_html(
                '<a href="mailto:{0}" target="_blank" style="font-weight: bold; color: #205493; font-size: 14px;">'
                '{0}'
                '</a>',
                obj.email
            )
        return "Sin correo registrado"
    
    def phone_link(self, obj):
        if obj.phone:
            url = self.get_whatsapp_link(obj.phone)
            return format_html(
                '<a href="{0}" target="_blank" style="font-weight: bold; color: #205493; font-size: 14px;">'
                '{1}'
                '</a>',
                url,
                obj.phone
            )
        return "Sin número registrado"
    
    email_link.short_description = 'Contácto'
    phone_link.short_description = 'Contácto'
    
    def has_import_permission(self, request):
        # return request.user.is_superuser
        return request.user.is_authenticated

    def has_export_permission(self, request):
        return request.user.is_authenticated
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
        
    def get_age(self, obj):
        return obj.age
    get_age.short_description = 'Edad'

    def age_display(self, obj):
        return f"{obj.age} años" if obj.age else "-"
    age_display.short_description = 'Edad'
    
    def get_n_records(self, obj):
        return obj.n_records
    get_n_records.short_description = 'N° Msjs'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "productor":
            user = request.user
            if user.is_superuser or user.role == 'ADMIN':
                kwargs["queryset"] = User.objects.filter(role='PRODUCTOR')
            elif user.role == 'SUPERVISOR':
                kwargs["queryset"] = User.objects.filter(supervisor=user, role='PRODUCTOR')
            else:
                kwargs["queryset"] = User.objects.filter(pk=user.pk)
                
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_changelist_instance(self, request, *args, **kwargs):
        self.list_editable = ()
        if request.user.is_superuser or request.user.role in ['ADMIN', 'SUPERVISOR']:
            self.list_editable = ('productor',)
        
        return super().get_changelist_instance(request, *args, **kwargs)
    
    def get_list_display(self, request):
        if request.user.role == 'PRODUCTOR':
            list_display = ('full_name', 'dni', 'age_display', 'gender', 'status', 'get_n_records', 'phone_link', 'email_link', 'date_first_contact', 'date_last_contact', 'n_poliza', 'highlight_row')
        else:
            list_display = ('full_name', 'dni', 'age_display', 'gender', 'status', 'get_n_records', 'productor', 'phone_link', 'email_link', 'date_first_contact', 'date_last_contact', 'n_poliza', 'highlight_row')
        return list_display
    
    def get_fieldsets(self, request, obj=None):
        datos_personales = ('Datos Personales', {
            'fields': ('full_name', 'dni', 'birthdate', 'age_display')
        })
        contacto = ('Contacto', {
            'fields': (('phone', 'phone_link'), ('email', 'email_link'))
        })
        gestion = ('Gestión', {
            'fields': ('status', 'observations', 'n_poliza')
        })
        gestion_con_productor = ('Gestión', {
            'fields': ('productor', 'status', 'observations', 'n_poliza')
        })
        if request.user.role == 'PRODUCTOR':
            return (datos_personales, contacto, gestion)
        else:
            return (datos_personales, contacto, gestion_con_productor)
        
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser or user.role == 'ADMIN':
            return qs
        if user.role == 'SUPERVISOR':
            return qs.filter(productor__supervisor=user)
        return qs.filter(productor=user)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, LeadManagement) and not instance.pk:
                instance.create_by = request.user
            instance.save()
        formset.save_m2m()
        
    def save_model(self, request, obj, form, change):
        if not change:  # Solo al crear
            if request.user.role == 'PRODUCTOR':
                obj.productor = request.user
        super().save_model(request, obj, form, change)
        
    def get_import_data_kwargs(self, request, *args, **kwargs):
        kwargs.update({'request': request})
        return kwargs
        
    def highlight_row(self, obj):
        clase = f"row-{obj.status.lower()}"

        return format_html(
            '<script>document.currentScript.closest("tr").classList.add("{}");</script>',
            clase
        )
    highlight_row.short_description = ''
    
    class Media:
        js = (static('admin/js/admin_filters_custom.js'),)
        css = {
            'all': (static('admin/css/admin_filters_custom.css'),)
        }