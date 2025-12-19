from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('onboarding/', views.onboarding_rol, name='onboarding_rol'),
    
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
]
