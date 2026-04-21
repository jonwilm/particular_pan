from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

class MyAdminSite(admin.AdminSite):
    # --- AGREGAMOS LA REDIRECCIÓN AQUÍ ---
    def index(self, request, extra_context=None):
        if request.user.is_authenticated:
            if getattr(request.user, 'role', None) == 'PRODUCTOR':
                return redirect(reverse('admin:leads_lead_changelist'))
        return super().index(request, extra_context)

    # --- MANTENEMOS TU LÓGICA DE ORDENAMIENTO ---
    def get_app_list(self, request, app_label=None):
        app_dict = self._build_app_dict(request, app_label)
        if 'admin_interface' in app_dict:
            del app_dict['admin_interface']
        
        app_list = list(app_dict.values())
        app_order = ["auth", "users", "leads"]
        app_list.sort(key=lambda x: app_order.index(x['app_label']) if x['app_label'] in app_order else 99)
        
        model_orders = {
            "auth": ["Group", "User"],
            "users": ["User"],
            "leads": ["Lead", "LeadManagement"],
        }
        
        for app in app_list:
            label = app['app_label']
            if label in model_orders:
                app['models'].sort(key=lambda x: model_orders[label].index(x['object_name']) if x['object_name'] in model_orders[label] else 99)
        return app_list
    

from django.contrib.admin.apps import AdminConfig

class MyAdminConfig(AdminConfig):
    default_site = 'particular_pan.admin.MyAdminSite'
