"""
Script de demostración del Sistema de Cobro Blindado (Escrow)
"""

from django.contrib.auth.models import User
from usuarios.models import UserProfile, Wallet
from jobs.models import JobOffer, Bid, EscrowTransaction
from decimal import Decimal

print("="*60)
print("DEMOSTRACIÓN SISTEMA DE COBRO BLINDADO (ESCROW)")
print("="*60)

# Verificar usuarios
try:
    cliente = User.objects.get(username='cliente')
    profesional = User.objects.get(username='profesional')
    print(f"\n✓ Cliente: {cliente.username}")
    print(f"✓ Profesional: {profesional.username}")
except User.DoesNotExist:
    print("\n❌ Error: No se encontraron los usuarios de prueba")
    print("Ejecuta primero: python crear_usuarios_prueba.py")
    exit()

# Verificar wallets
cliente_wallet, created = Wallet.objects.get_or_create(
    user=cliente,
    defaults={'tipo_cuenta': 'USER', 'balance_usdc': Decimal('1000.00')}
)
profesional_wallet, created = Wallet.objects.get_or_create(
    user=profesional,
    defaults={'tipo_cuenta': 'USER', 'balance_usdc': Decimal('0.00')}
)

print(f"\n💰 Saldo Cliente: ${cliente_wallet.balance_usdc} USDC")
print(f"💰 Saldo Profesional: ${profesional_wallet.balance_usdc} USDC")

# Verificar trabajos en progreso
jobs_in_progress = JobOffer.objects.filter(status='IN_PROGRESS')
print(f"\n📋 Trabajos en progreso: {jobs_in_progress.count()}")

if jobs_in_progress.count() == 0:
    print("\n⚠️  No hay trabajos en progreso para demostrar el escrow")
    print("Pasos para probar:")
    print("1. Crea una oferta como PERSONA/CONSORCIO")
    print("2. Envía una propuesta como OFICIO")
    print("3. Acepta la propuesta (esto bloqueará el 30% en escrow)")
    print("4. Confirma inicio de obra (libera 30% al profesional)")
    print("5. Finaliza la obra (libera 70% - 5% comisión)")
else:
    for job in jobs_in_progress:
        print(f"\n📌 Trabajo: {job.title}")
        print(f"   Estado: {job.get_status_display()}")
        
        winning_bid = job.get_winning_bid()
        if winning_bid:
            print(f"   Profesional: {winning_bid.professional.nombre_completo}")
            print(f"   Monto total: ${winning_bid.amount_usdc} USDC")
            print(f"   30% inicial: ${winning_bid.amount_usdc * Decimal('0.30')} USDC")
            print(f"   70% final: ${winning_bid.amount_usdc * Decimal('0.70')} USDC")
            print(f"   Comisión 5%: ${winning_bid.amount_usdc * Decimal('0.05')} USDC")
            
            # Verificar transacciones de escrow
            escrow_txs = EscrowTransaction.objects.filter(job=job)
            print(f"\n   🔒 Transacciones de escrow: {escrow_txs.count()}")
            
            for tx in escrow_txs:
                status_emoji = {
                    'LOCKED': '🔒',
                    'RELEASED': '✅',
                    'REFUNDED': '🔄'
                }
                print(f"   {status_emoji.get(tx.status, '❓')} {tx.get_transaction_type_display()}")
                print(f"      Monto: ${tx.amount_usdc} USDC")
                print(f"      Estado: {tx.get_status_display()}")
            
            # Verificar qué acciones están disponibles
            initial_released = escrow_txs.filter(
                transaction_type='INITIAL_RELEASE',
                status='RELEASED'
            ).exists()
            
            final_released = escrow_txs.filter(
                transaction_type='FINAL_RELEASE',
                status='RELEASED'
            ).exists()
            
            print(f"\n   📊 Estado de pagos:")
            if not initial_released:
                print("   ⏳ Pendiente: Confirmar inicio de obra (libera 30%)")
            elif not final_released:
                print("   ✓ 30% liberado al profesional")
                print("   ⏳ Pendiente: Finalizar obra (libera 70% - 5%)")
            else:
                print("   ✅ Todos los pagos completados")

print("\n" + "="*60)
print("FLUJO DEL SISTEMA DE ESCROW")
print("="*60)
print("""
1. ACEPTAR PROPUESTA:
   - Cliente debe tener saldo suficiente (30% del total)
   - Se bloquea el 30% en cuenta de escrow
   - Estado: LOCKED

2. CONFIRMAR INICIO DE OBRA (Cliente):
   - Se libera el 30% al profesional
   - Se bloquea el 70% restante del cliente
   - Estados: 30% RELEASED, 70% LOCKED

3. FINALIZAR OBRA (Cliente):
   - Se libera el 70% menos 5% de comisión
   - Profesional recibe 65% del total
   - Plataforma retiene 5% de comisión
   - Trabajo cambia a CLOSED

URLS disponibles:
- Aceptar propuesta: POST /jobs/bid/<bid_id>/accept/
- Confirmar inicio: POST /jobs/<job_id>/confirm-start/
- Finalizar obra: POST /jobs/<job_id>/complete/
""")

print("="*60)
