from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Q
from django.utils.html import format_html

from .models import User
from .forms import LoginFormCustom


admin.site.login_form = LoginFormCustom

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('dni', 'password')}),
        (('Información Personal'), {
            'fields': (
                'first_name',
                'last_name',
                'email',
            )
        }),
        
        (('Jerarquía'), {
            'fields': (
                'role',
                'supervisor',
            )
        }),

        # (('Permisos'), {
        #     'fields': (
        #         'is_active',
        #         'is_staff',
        #         'is_superuser',
        #         'groups',
        #     ),
        # }),

        ((''), {
            'fields': (
                'last_login',
            )
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'dni',
                'first_name',
                'last_name',
                'email',
                'password1',
                'password2',
                'role',
                'supervisor',
            ),
        }),
    )
    
    login_form = LoginFormCustom
    list_display = ('dni', 'last_name', 'first_name', 'email', 'role', 'supervisor', 'date_joined', 'last_login', 'is_active',)
    list_filter = ('role',)
    list_editable = ('is_active',)
    search_fields = ('first_name', 'last_name', 'email',)
    ordering = ('last_name', 'first_name', 'email',)
    readonly_fields = ('last_login',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        
        # Si es Superusuario o Admin General, ve a todos
        if user.is_superuser or user.role == User.ADMIN:
            return qs
        
        # Si es Supervisor, solo ve a sus productores asociados
        if user.role == User.SUPERVISOR:
            return qs.filter(Q(pk=user.pk) | Q(supervisor=user.pk))
        
        # Si es Productor, solo se ve a sí mismo
        return qs.filter(pk=user.pk)
    
    def get_changelist_instance(self, request):
        user = request.user
        if user.is_superuser or user.role == User.ADMIN:
            self.list_editable = ('role', 'supervisor', 'is_active')
        else:
            self.list_editable = ('is_active',)
            
        return super().get_changelist_instance(request)
    
    def get_readonly_fields(self, request, obj=None):
        user = request.user
        if user.is_superuser or user.role == User.ADMIN:
            return ('last_login',)
        
        return ('role', 'supervisor', 'is_staff', 'is_superuser', 'groups', 'last_login',)
    
    def save_model(self, request, obj, form, change):
        if not change:
            if request.user.role == User.SUPERVISOR:
                obj.role = User.PRODUCTOR
                obj.supervisor = request.user
                obj.is_staff = True
        
        super().save_model(request, obj, form, change)
        
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.role == User.ADMIN:
            return True
        
        if obj and request.user.role == User.SUPERVISOR:
            return obj.supervisor == request.user
            
        return False
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "supervisor":
            kwargs["queryset"] = User.objects.filter(role=User.SUPERVISOR)
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    # def highlight_row(self, obj):
    #     clase = 'row-active' if obj.is_active else 'row-inactive'

    #     return format_html(
    #         '<script>document.currentScript.closest("tr").classList.add("{}");</script>',
    #         clase
    #     )
    # highlight_row.short_description = ''