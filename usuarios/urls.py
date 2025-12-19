from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('onboarding/', views.onboarding_rol, name='onboarding_rol'),
    
    # Ofertas y Propuestas
    path('ofertas/', views.ofertas_lista, name='ofertas_lista'),
    path('ofertas/<int:oferta_id>/', views.oferta_detalle, name='oferta_detalle'),
    path('ofertas/<int:oferta_id>/propuesta/', views.crear_propuesta, name='crear_propuesta'),
]
