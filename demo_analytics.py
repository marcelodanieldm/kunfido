"""
Demo Script - Analytics Dashboard
Genera datos de prueba y muestra los KPIs del dashboard de analytics
"""

from django.contrib.auth.models import User
from usuarios.models import UserProfile, Wallet
from jobs.models import JobOffer, Bid, EscrowTransaction
from django.utils import timezone
from decimal import Decimal


print("\n" + "="*80)
print("🔥 DEMO: ANALYTICS DASHBOARD - KPIs DEL NEGOCIO 🔥")
print("="*80 + "\n")

# ========== KPI 1: GMV TOTAL ==========
print("📊 KPI 1: GMV TOTAL (Gross Merchandise Value)")
print("-" * 80)

jobs_activos = JobOffer.objects.filter(status__in=['IN_PROGRESS', 'CLOSED'])
gmv_total = sum([job.budget_base_ars for job in jobs_activos])

print(f"Trabajos activos (IN_PROGRESS + CLOSED): {jobs_activos.count()}")
print(f"GMV Total: ${gmv_total:,.2f} ARS")
print()

# ========== KPI 2: COMISIONES ACUMULADAS ==========
print("💰 KPI 2: COMISIONES ACUMULADAS (5% de trabajos finalizados)")
print("-" * 80)

jobs_finalizados = JobOffer.objects.filter(status='CLOSED')
total_finalizados = sum([job.budget_base_ars for job in jobs_finalizados])
comisiones = total_finalizados * Decimal('0.05')

comisiones_usdc = EscrowTransaction.objects.filter(
    transaction_type='PLATFORM_FEE',
    status='RELEASED'
).aggregate(total=sum)

print(f"Trabajos finalizados: {jobs_finalizados.count()}")
print(f"Total finalizados: ${total_finalizados:,.2f} ARS")
print(f"Comisiones (5%): ${comisiones:,.2f} ARS")

if comisiones_usdc:
    print(f"Comisiones en USDC: ${comisiones_usdc.get('amount_usdc__sum', 0) or 0:,.2f} USDC")
print()

# ========== KPI 3: FONDOS EN ESCROW ==========
print("🔒 KPI 3: FONDOS EN ESCROW (bloqueados)")
print("-" * 80)

fondos_bloqueados = EscrowTransaction.objects.filter(status='LOCKED')
total_bloqueado = sum([tx.amount_usdc for tx in fondos_bloqueados])

print(f"Transacciones bloqueadas: {fondos_bloqueados.count()}")
print(f"Total en garantía: ${total_bloqueado:,.2f} USDC")
print()

# ========== KPI 4: TASA DE ATRASO ==========
print("⏰ KPI 4: TASA DE ATRASO")
print("-" * 80)

jobs_en_progreso = JobOffer.objects.filter(status='IN_PROGRESS')
jobs_atrasados = jobs_en_progreso.filter(is_delayed=True)

if jobs_en_progreso.count() > 0:
    tasa_atraso = (jobs_atrasados.count() / jobs_en_progreso.count()) * 100
else:
    tasa_atraso = 0

print(f"Trabajos en progreso: {jobs_en_progreso.count()}")
print(f"Trabajos atrasados: {jobs_atrasados.count()}")
print(f"Tasa de atraso: {tasa_atraso:.2f}%")
print()

# ========== ESTADÍSTICAS ADICIONALES ==========
print("📈 ESTADÍSTICAS ADICIONALES")
print("-" * 80)

# Usuarios por rol
for rol in ['PERSONA', 'CONSORCIO', 'OFICIO']:
    count = UserProfile.objects.filter(tipo_rol=rol).count()
    print(f"Usuarios {rol}: {count}")

print()

# Transacciones por tipo
print("Transacciones Escrow por tipo:")
for tipo in ['INITIAL_DEPOSIT', 'REMAINING_DEPOSIT', 'INITIAL_RELEASE', 'FINAL_RELEASE', 'PLATFORM_FEE']:
    count = EscrowTransaction.objects.filter(transaction_type=tipo).count()
    if count > 0:
        print(f"  - {tipo}: {count}")

print()

# ========== ACCESO AL DASHBOARD ==========
print("="*80)
print("🌐 ACCESO AL DASHBOARD DE ANALYTICS")
print("="*80)
print()
print("URL del Dashboard: http://localhost:8000/analytics/dashboard/")
print()
print("⚠️  IMPORTANTE: Solo accesible para SUPERUSUARIOS")
print()
print("Para crear un superusuario:")
print("  python manage.py createsuperuser")
print()
print("O usar credenciales existentes de superadmin del sistema")
print()

# ========== DESCARGA DE REPORTES CSV ==========
print("="*80)
print("📥 REPORTES CSV DISPONIBLES")
print("="*80)
print()
print("1. Reporte de Todas las Transacciones:")
print("   URL: http://localhost:8000/analytics/reporte/transacciones/csv/")
print("   Incluye: CUIT, montos, fechas, cliente, profesional")
print()
print("2. Reporte de Comisiones:")
print("   URL: http://localhost:8000/analytics/reporte/comisiones/csv/")
print("   Incluye: Comisiones del 5%, datos fiscales")
print()

print("="*80)
print("✅ Demo completado - Revisa el dashboard para ver los KPIs en tiempo real")
print("="*80)
