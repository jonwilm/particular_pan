from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, ExpressionWrapper, FloatField
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import Lead, LeadManagement

@login_required
def supervisor_dashboard(request):
    user = request.user
    if not (user.is_superuser or user.role in ['ADMIN', 'SUPERVISOR']):
        return redirect('admin:index')

    # --- Filtrado de Leads (Métricas Generales) ---
    leads_qs = Lead.objects.all()
    if not user.is_superuser and user.role == 'SUPERVISOR':
        leads_qs = leads_qs.filter(productor__supervisor=user)

    # --- Filtrado de Productores (Tabla de Rendimiento) ---
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Base de la consulta: todos los usuarios con rol PRODUCTOR
    productores_qs = User.objects.filter(role='PRODUCTOR')

    # SI ES SUPERVISOR: Limitamos a sus subordinados
    # SI ES ADMIN/SUPERUSER: No filtramos, permitimos ver a todos
    if not user.is_superuser and user.role == 'SUPERVISOR':
        productores_qs = productores_qs.filter(supervisor=user)

    # Anotamos las estadísticas sobre el queryset resultante
    productores_stats = productores_qs.annotate(
        total_asignados=Count('my_leads'),
        ventas_logradas=Count('my_leads', filter=Q(my_leads__status='VENTA_CERRADA')),
    ).order_by('-ventas_logradas')
    
    for p in productores_stats:
        if p.total_asignados > 0:
            # Calculamos el porcentaje con un decimal
            p.eficiencia_real = round((p.ventas_logradas / p.total_asignados) * 100, 1)
        else:
            p.eficiencia_real = 0
    
    total_general_leads = leads_qs.count()
    total_general_ventas = leads_qs.filter(status='VENTA_CERRADA').count()
    eficiencia_equipo = 0
    if total_general_leads > 0:
        eficiencia_equipo = round((total_general_ventas / total_general_leads) * 100, 1)

    context = {
        'total_leads': total_general_leads,
        'status_counts': leads_qs.values('status').annotate(total=Count('status')),
        'leads_frios': leads_qs.filter(
            Q(date_last_contact__lt=timezone.now() - timedelta(days=3)) | 
            Q(date_last_contact__isnull=True)
        ).exclude(status='VENTA_CERRADA').count(),
        'eficiencia_equipo': eficiencia_equipo,
        'productores_stats': productores_stats,
    }
    return render(request, 'leads/dashboard.html', context)