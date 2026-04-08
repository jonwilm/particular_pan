from datetime import date, timedelta
from django.contrib import admin
from django.contrib.auth import get_user_model
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
    list_display = ('full_name', 'dni', 'get_age', 'status', 'get_n_records', 'date_creation', 'date_first_contact', 'date_last_contact', 'productor', 'highlight_row')
    list_filter = ('status', AgeRangeFilter, ProductorFilter, ('date_last_contact', admin.DateFieldListFilter), ('date_last_contact', DateRangeFilter),)
    search_fields = ('full_name', 'dni', 'phone',)
    inlines = [LeadManagementInline]
    readonly_fields = ('date_creation', 'date_first_contact', 'date_last_contact')
    
    def has_import_permission(self, request):
        return request.user.is_superuser

    def has_export_permission(self, request):
        return request.user.is_authenticated
        
    def get_age(self, obj):
        return obj.age
    get_age.short_description = 'Edad'

    def age_display(self, obj):
        return f"{obj.age} años" if obj.age else "-"
    age_display.short_description = 'Edad Actual'
    
    def get_n_records(self, obj):
        return obj.n_records
    get_n_records.short_description = 'N° Msjs'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        # 1. Admin ve todos los leads de todos
        if user.is_superuser or user.role == 'ADMIN':
            return qs
        # 2. Supervisor ve los leads de sus productores a cargo
        if user.role == 'SUPERVISOR':
            # Buscamos los leads cuyo productor tenga como supervisor al usuario actual
            return qs.filter(productor__supervisor=user)
        # 3. Productor solo ve sus propios leads
        return qs.filter(productor=user)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, LeadManagement) and not instance.pk:
                instance.create_by = request.user
            instance.save()
        formset.save_m2m()
        
        
    def highlight_row(self, obj):
        clase = f"row-{obj.status.lower()}"

        return format_html(
            '<script>document.currentScript.closest("tr").classList.add("{}");</script>',
            clase
        )
    highlight_row.short_description = ''