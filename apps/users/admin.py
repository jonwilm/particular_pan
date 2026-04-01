from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import LoginFormCustom


admin.site.login_form = LoginFormCustom

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'dni', 'password')}),
        (('Información Personal'), {
            'fields': (
                'first_name',
                'last_name',
            )
        }),

        (('Permisos'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
            ),
        }),

        (('Jerarquía'), {
            'fields': (
                'role',
                'supervisor',
            )
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'dni',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'role',
                'supervisor',
            ),
        }),
    )
    
    login_form = LoginFormCustom
    list_display = ('email', 'last_name', 'first_name', 'role', 'supervisor', 'date_joined', 'last_login', 'is_active', )
    list_filter = ('role',)
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
            return qs.filter(supervisor=user.pk)
        
        # Si es Productor, solo se ve a sí mismo
        return qs.filter(pk=user.pk)
    
    def get_readonly_fields(self, request, obj=None):
        user = request.user
        # Solo el Admin puede asignar supervisores o cambiar productores de supervisor
        if not (user.is_superuser or user.role == User.ADMIN):
            return ('role', 'supervisor', 'is_staff', 'is_superuser')
        
        return super().get_readonly_fields(request, obj)
    
    def save_model(self, request, obj, form, change):
        # Los supervisores solo pueden registrar nuevos productores a su cargo.
        if not change:
            if request.user.role == User.SUPERVISOR:
                obj.role = User.PRODUCTOR
                obj.supervisor = request.user
                obj.is_staff = True
        
        super().save_model(request, obj, form, change)
        
    def has_delete_permission(self, request, obj=None):
        # El supervisor puede eliminar a sus productores.
        if request.user.is_superuser or request.user.role == User.ADMIN:
            return True
        
        if obj and request.user.role == User.SUPERVISOR:
            return obj.supervisor == request.user
            
        return False
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "supervisor":
            # Solo permitir elegir a usuarios que tengan el rol de SUPERVISOR
            kwargs["queryset"] = User.objects.filter(role=User.SUPERVISOR)
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)