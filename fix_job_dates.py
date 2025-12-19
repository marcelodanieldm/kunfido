"""
Script para actualizar trabajos en progreso existentes
que no tienen fechas configuradas
"""

from jobs.models import JobOffer
from django.utils import timezone
from datetime import timedelta

print("="*60)
print("ACTUALIZACIÓN DE TRABAJOS EN PROGRESO")
print("="*60)

# Buscar trabajos en progreso sin fechas
jobs_to_update = JobOffer.objects.filter(
    status='IN_PROGRESS',
    start_confirmed_date__isnull=True
)

print(f"\nEncontrados {jobs_to_update.count()} trabajo(s) para actualizar\n")

for job in jobs_to_update:
    print("-"*60)
    print(f"Actualizando: {job.title} (ID: {job.id})")
    
    winning_bid = job.get_winning_bid()
    
    if winning_bid:
        # Establecer fechas
        job.start_confirmed_date = timezone.now() - timedelta(days=2)  # Simular que empezó hace 2 días
        job.expected_completion_date = job.start_confirmed_date + timedelta(days=winning_bid.estimated_days)
        job.save()
        
        print(f"✓ Fecha de inicio: {job.start_confirmed_date}")
        print(f"✓ Fecha esperada: {job.expected_completion_date}")
        print(f"✓ Días estimados: {winning_bid.estimated_days}")
    else:
        print("⚠️  No hay propuesta ganadora para este trabajo")
    
    print()

print("="*60)
print("ACTUALIZACIÓN COMPLETADA")
print("="*60)

# Mostrar resumen
in_progress_with_dates = JobOffer.objects.filter(
    status='IN_PROGRESS',
    start_confirmed_date__isnull=False
)

print(f"\nTrabajos en progreso con fechas: {in_progress_with_dates.count()}")
print("\nAccede a la vista de seguimiento en:")
for job in in_progress_with_dates:
    print(f"  → /jobs/{job.id}/tracking/")
