from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-home/', views.dashboard_home, name='dashboard_home'),
    
    # Registro y Autenticación
    path('signup/', views.signup_choice, name='signup_choice'),
    
    # Onboarding
    path('onboarding/', views.onboarding_rol, name='onboarding_rol'),  # Legacy
    path('role-selection/', views.role_selection, name='role_selection'),
    path('onboarding-form/', views.onboarding_form, name='onboarding_form'),
    
    # Feed Público
    path('trabajos/', views.public_feed, name='public_feed'),
    path('trabajos/<int:oferta_id>/', views.job_detail_public, name='job_detail_public'),
    
    # Ofertas y Propuestas
    path('ofertas/', views.ofertas_lista, name='ofertas_lista'),
    path('ofertas/<int:oferta_id>/', views.oferta_detalle, name='oferta_detalle'),
    path('ofertas/<int:oferta_id>/propuesta/', views.crear_propuesta, name='crear_propuesta'),
    path('ofertas/<int:oferta_id>/privado/', views.job_detail_private, name='job_detail_private'),
    
    # Votación
    path('propuestas/<int:propuesta_id>/votar/', views.votar_propuesta, name='votar_propuesta'),
    
    # Justificaciones de Atraso
    path('ofertas/<int:oferta_id>/justificar-atraso/', views.crear_justificacion_atraso, name='crear_justificacion_atraso'),
    path('justificaciones/<int:justificacion_id>/aceptar/', views.aceptar_replica_atraso, name='aceptar_replica_atraso'),
    path('justificaciones/<int:justificacion_id>/rechazar/', views.rechazar_replica_atraso, name='rechazar_replica_atraso'),
    
    # Aprobación de Trabajo y Pagos
    path('ofertas/<int:oferta_id>/aprobar-trabajo/', views.aprobar_trabajo_completado, name='aprobar_trabajo_completado'),
    path('ofertas/<int:oferta_id>/rechazar-trabajo/', views.rechazar_trabajo_completado, name='rechazar_trabajo_completado'),
    path('ofertas/<int:oferta_id>/solicitar-reembolso/', views.solicitar_reembolso, name='solicitar_reembolso'),
    
    # Billetera
    path('wallet/', views.wallet_detalle, name='wallet_detalle'),
    path('wallet/escrow/', views.wallet_escrow, name='wallet_escrow'),
    path('wallet/cargar-fondos/', views.cargar_fondos, name='cargar_fondos'),
    
    # Admin Dashboard
    path('admin-dashboard/', views.admin_custom_dashboard, name='admin_custom_dashboard'),
    path('admin-dashboard/exportar-trabajos/', views.exportar_trabajos_csv, name='exportar_trabajos_csv'),
]
