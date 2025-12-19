from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('<int:job_id>/', views.job_detail, name='job_detail'),
    path('<int:job_id>/tracking/', views.job_tracking, name='job_tracking'),
    path('<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('<int:job_id>/submit-bid/', views.submit_bid, name='submit_bid'),
    path('bid/<int:bid_id>/accept/', views.accept_bid, name='accept_bid'),
    
    # Gestión de atrasos - Derecho a Réplica
    path('<int:job_id>/delay/justify/', views.submit_delay_justification, name='submit_delay_justification'),
    path('delay/<int:delay_id>/review/', views.review_delay_justification, name='review_delay_justification'),
    path('delays/', views.delay_registries_list, name='delay_registries_list'),
    
    # Sistema de Escrow - Confirmaciones de obra
    path('<int:job_id>/confirm-start/', views.confirm_work_start, name='confirm_work_start'),
    path('<int:job_id>/complete/', views.complete_work, name='complete_work'),
]
