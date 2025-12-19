"""
Script de verificación del Sistema de Derecho a Réplica
Ejecutar con: python manage.py shell < test_delay_system.py
"""

from jobs.models import JobOffer, Bid, DelayRegistry
from usuarios.models import UserProfile
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

print("="*60)
print("VERIFICACIÓN DEL SISTEMA DE DERECHO A RÉPLICA")
print("="*60)

# 1. Verificar campos en JobOffer
print("\n1. Verificando campos en JobOffer...")
job_fields = [f.name for f in JobOffer._meta.get_fields()]
required_fields = ['start_confirmed_date', 'expected_completion_date', 'is_delayed']

for field in required_fields:
    if field in job_fields:
        print(f"   ✓ Campo '{field}' encontrado")
    else:
        print(f"   ✗ Campo '{field}' NO encontrado")

# 2. Verificar modelo DelayRegistry
print("\n2. Verificando modelo DelayRegistry...")
try:
    delay_fields = [f.name for f in DelayRegistry._meta.get_fields()]
    required_delay_fields = ['bid', 'days_delayed', 'reason', 'accepted_by_client', 'status']
    
    for field in required_delay_fields:
        if field in delay_fields:
            print(f"   ✓ Campo '{field}' encontrado")
        else:
            print(f"   ✗ Campo '{field}' NO encontrado")
except Exception as e:
    print(f"   ✗ Error al verificar DelayRegistry: {e}")

# 3. Verificar métodos
print("\n3. Verificando métodos...")
try:
    job = JobOffer()
    
    # check_deadline_status
    if hasattr(job, 'check_deadline_status'):
        print("   ✓ Método 'check_deadline_status' existe")
    else:
        print("   ✗ Método 'check_deadline_status' NO existe")
    
    # get_days_delayed
    if hasattr(job, 'get_days_delayed'):
        print("   ✓ Método 'get_days_delayed' existe")
    else:
        print("   ✗ Método 'get_days_delayed' NO existe")
    
except Exception as e:
    print(f"   ✗ Error al verificar métodos: {e}")

# 4. Verificar métodos de DelayRegistry
print("\n4. Verificando métodos de DelayRegistry...")
try:
    delay_methods = ['accept_delay', 'reject_delay', 'apply_penalty', 'create_delay_report']
    
    for method in delay_methods:
        if hasattr(DelayRegistry, method):
            print(f"   ✓ Método '{method}' existe")
        else:
            print(f"   ✗ Método '{method}' NO existe")
            
except Exception as e:
    print(f"   ✗ Error al verificar métodos de DelayRegistry: {e}")

# 5. Verificar vistas
print("\n5. Verificando vistas...")
try:
    from jobs import views
    
    view_functions = [
        'submit_delay_justification',
        'review_delay_justification',
        'delay_registries_list'
    ]
    
    for view_func in view_functions:
        if hasattr(views, view_func):
            print(f"   ✓ Vista '{view_func}' existe")
        else:
            print(f"   ✗ Vista '{view_func}' NO existe")
            
except Exception as e:
    print(f"   ✗ Error al verificar vistas: {e}")

# 6. Contar registros
print("\n6. Estado actual de la base de datos...")
print(f"   - Ofertas de trabajo: {JobOffer.objects.count()}")
print(f"   - Propuestas (Bids): {Bid.objects.count()}")
print(f"   - Registros de atraso: {DelayRegistry.objects.count()}")
print(f"   - Ofertas con atraso: {JobOffer.objects.filter(is_delayed=True).count()}")

# 7. Verificar templates
print("\n7. Verificando templates...")
import os
from django.conf import settings

template_dir = os.path.join(settings.BASE_DIR, 'templates', 'jobs')
required_templates = [
    'delay_justification_form.html',
    'review_delay_justification.html',
    'delay_registries_list.html'
]

for template in required_templates:
    template_path = os.path.join(template_dir, template)
    if os.path.exists(template_path):
        print(f"   ✓ Template '{template}' existe")
    else:
        print(f"   ✗ Template '{template}' NO existe")

print("\n" + "="*60)
print("VERIFICACIÓN COMPLETADA")
print("="*60)
