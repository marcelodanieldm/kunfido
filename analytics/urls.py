from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.superuser_dashboard, name='superuser_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/banear/<int:user_id>/', views.banear_usuario, name='banear_usuario'),
    path('admin/verificar/<int:user_id>/', views.verificar_cuit, name='verificar_cuit'),
    path('reporte/transacciones/csv/', views.generar_reporte_csv, name='reporte_csv'),
    path('reporte/comisiones/csv/', views.generar_reporte_comisiones_csv, name='reporte_comisiones_csv'),
    path('reporte/mensual/csv/', views.generar_reporte_mensual_csv, name='reporte_mensual_csv'),
]
