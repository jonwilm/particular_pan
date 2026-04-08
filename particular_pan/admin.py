from django.contrib import admin

class MyAdminSite(admin.AdminSite):
    def get_app_list(self, request, app_label=None):
        app_dict = self._build_app_dict(request, app_label)
        
        # --- FILTRO: Eliminamos 'admin_interface' de la lista visual ---
        if 'admin_interface' in app_dict:
            del app_dict['admin_interface']
        
        # Convertimos el diccionario en lista para ordenar
        app_list = list(app_dict.values())
        
        # Tu lógica de ordenamiento existente
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