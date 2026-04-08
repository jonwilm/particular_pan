from django.urls import path
from .views import supervisor_dashboard

urlpatterns = [
    path('dashboard/', supervisor_dashboard, name='leads_dashboard'),
]