"""
Script de demostración del Sistema de Seguimiento (job_tracking)

Este script simula diferentes escenarios de seguimiento de trabajos
para mostrar cómo se comporta la barra de tiempo dinámica.
"""

from jobs.models import JobOffer, Bid
from usuarios.models import UserProfile
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

print("="*70)
print("DEMOSTRACIÓN DEL SISTEMA DE SEGUIMIENTO DE TRABAJOS")
print("="*70)

# Verificar si hay trabajos en progreso
in_progress_jobs = JobOffer.objects.filter(status='IN_PROGRESS')

if not in_progress_jobs.exists():
    print("\n⚠️  No hay trabajos en progreso en este momento.")
    print("\nPara probar el sistema de seguimiento:")
    print("1. Crea una oferta de trabajo")
    print("2. Acepta una propuesta (esto cambia el status a IN_PROGRESS)")
    print("3. Accede a /jobs/<job_id>/tracking/")
    print("\nO simula un atraso modificando expected_completion_date en el admin.")
else:
    print(f"\n✓ Encontrados {in_progress_jobs.count()} trabajo(s) en progreso\n")
    
    for job in in_progress_jobs:
        print("-"*70)
        print(f"JOB ID: {job.id} - {job.title}")
        print("-"*70)
        
        winning_bid = job.get_winning_bid()
        
        if winning_bid:
            print(f"Profesional: {winning_bid.professional.nombre_completo}")
            print(f"Monto: ${winning_bid.amount_ars}")
            print(f"Días Estimados: {winning_bid.estimated_days}")
        
        print(f"\nFecha de Inicio: {job.start_confirmed_date}")
        print(f"Fecha Esperada: {job.expected_completion_date}")
        
        # Calcular estado actual
        if job.start_confirmed_date and job.expected_completion_date:
            now = timezone.now()
            elapsed = now - job.start_confirmed_date
            total_duration = job.expected_completion_date - job.start_confirmed_date
            remaining = job.expected_completion_date - now
            
            elapsed_days = elapsed.days
            total_days = total_duration.days
            remaining_hours = int(remaining.total_seconds() / 3600)
            
            # Calcular progreso
            if total_days > 0:
                progress = (elapsed_days / total_days) * 100
            else:
                progress = 0
            
            print(f"\nProgreso: {progress:.1f}%")
            print(f"Días Transcurridos: {elapsed_days}")
            print(f"Horas Restantes: {remaining_hours}h")
            
            # Determinar estado
            job.check_deadline_status()
            
            if job.is_delayed:
                days_delayed = job.get_days_delayed()
                print(f"\n🔴 ESTADO: ATRASADO ({days_delayed} días)")
                print("   Barra: ROJA INTERMITENTE")
            elif remaining_hours <= 24 and remaining_hours > 0:
                print(f"\n🟠 ESTADO: ÚLTIMAS 24 HORAS")
                print("   Barra: NARANJA")
            else:
                print(f"\n🔵 ESTADO: EN TÉRMINO")
                print("   Barra: AZUL")
            
            print(f"\nURL de Seguimiento: /jobs/{job.id}/tracking/")
        else:
            print("\n⚠️  Este trabajo no tiene fechas configuradas")
        
        print()

print("="*70)
print("SIMULACIÓN DE ESCENARIOS")
print("="*70)

print("\n1️⃣  Para simular BARRA AZUL (En término):")
print("   → Trabajo en progreso con tiempo suficiente")
print("   → Más de 24 horas para la fecha esperada")

print("\n2️⃣  Para simular BARRA NARANJA (Últimas 24hs):")
print("   → Modificar expected_completion_date a mañana mismo")
print("   → Ejemplo: timezone.now() + timedelta(hours=12)")

print("\n3️⃣  Para simular BARRA ROJA INTERMITENTE (Atrasado):")
print("   → Modificar expected_completion_date a una fecha pasada")
print("   → Ejemplo: timezone.now() - timedelta(days=3)")

print("\n" + "="*70)
print("CÓDIGO PARA SIMULAR ATRASO")
print("="*70)

if in_progress_jobs.exists():
    job = in_progress_jobs.first()
    print(f"""
# En Django shell:
from jobs.models import JobOffer
from django.utils import timezone
from datetime import timedelta

job = JobOffer.objects.get(id={job.id})

# Simular 3 días de atraso
job.expected_completion_date = timezone.now() - timedelta(days=3)
job.save()

# Verificar
job.check_deadline_status()
print(f"Is delayed: {{job.is_delayed}}")
print(f"Days delayed: {{job.get_days_delayed()}}")

# Ahora accede a: /jobs/{job.id}/tracking/
""")

print("\n" + "="*70)
print("CARACTERÍSTICAS DEL TRACKING")
print("="*70)

print("""
✓ Barra de progreso dinámica con 3 colores:
  • AZUL: En término (on-time)
  • NARANJA: Últimas 24 horas (warning)
  • ROJA INTERMITENTE: Atrasado (delayed)

✓ Panel de alerta de atraso con:
  • Ícono ⚠️  intermitente
  • Cantidad de días de atraso
  • Botones de acción según rol

✓ Timeline de eventos con:
  • Publicación de oferta
  • Aceptación de propuesta
  • Estado actual
  • Historial de justificaciones
  • Fecha esperada

✓ Estadísticas en tiempo real:
  • Días transcurridos
  • Días estimados
  • Días/horas restantes o de atraso
  • Porcentaje de progreso

✓ Botón "Explicar Motivo" (OFICIO):
  • Modal con formulario de justificación
  • Mínimo 50 caracteres
  • Integrado con sistema de Derecho a Réplica

✓ Botón "Indultar" (CLIENTE):
  • Redirige a revisión de justificación
  • Permite aceptar el atraso
  • Mantiene limpia la reputación del profesional
""")

print("="*70)
