"""
Script de demostración del Wallet Escrow
Simula un flujo completo con fondos en garantía
"""

from django.contrib.auth.models import User
from usuarios.models import UserProfile, Wallet
from jobs.models import JobOffer, Bid, EscrowTransaction
from decimal import Decimal

print("="*70)
print("DEMOSTRACIÓN: INTERFAZ WALLET ESCROW")
print("="*70)

# Verificar usuarios
try:
    cliente = User.objects.get(username='cliente')
    profesional = User.objects.get(username='profesional')
    print(f"\n✓ Cliente: {cliente.username}")
    print(f"✓ Profesional: {profesional.username}")
except User.DoesNotExist:
    print("\n❌ Error: No se encontraron los usuarios de prueba")
    exit()

# Obtener wallets
cliente_wallet = Wallet.objects.get(user=cliente)
profesional_wallet = Wallet.objects.get(user=profesional)

print(f"\n💰 SALDOS INICIALES:")
print(f"   Cliente: ${cliente_wallet.balance_usdc} USDC")
print(f"   Profesional: ${profesional_wallet.balance_usdc} USDC")

# Obtener trabajo en progreso
job = JobOffer.objects.filter(status='IN_PROGRESS').first()

if not job:
    print("\n⚠️  No hay trabajos en progreso para demostrar")
    exit()

print(f"\n📌 TRABAJO EN PROGRESO:")
print(f"   ID: {job.id}")
print(f"   Título: {job.title}")
print(f"   Estado: {job.get_status_display()}")

winning_bid = job.get_winning_bid()
if not winning_bid:
    print("\n❌ No hay propuesta ganadora")
    exit()

print(f"\n💼 PROPUESTA ACEPTADA:")
print(f"   Profesional: {winning_bid.professional.nombre_completo}")
print(f"   Monto total: ${winning_bid.amount_usdc} USDC")
print(f"   30% inicial: ${winning_bid.amount_usdc * Decimal('0.30')} USDC")
print(f"   70% final: ${winning_bid.amount_usdc * Decimal('0.70')} USDC")

# Obtener transacciones de escrow
escrow_txs = EscrowTransaction.objects.filter(job=job).order_by('created_at')

print(f"\n🔒 TRANSACCIONES DE ESCROW:")
total_locked = Decimal('0.00')
total_released = Decimal('0.00')

for tx in escrow_txs:
    status_emoji = {
        'LOCKED': '🔒',
        'RELEASED': '✅',
        'REFUNDED': '🔄'
    }
    
    emoji = status_emoji.get(tx.status, '❓')
    print(f"\n   {emoji} {tx.get_transaction_type_display()}")
    print(f"      Monto: ${tx.amount_usdc} USDC")
    print(f"      Estado: {tx.get_status_display()}")
    print(f"      Fecha: {tx.created_at.strftime('%d/%m/%Y %H:%M')}")
    
    if tx.status == 'LOCKED':
        total_locked += tx.amount_usdc
    elif tx.status == 'RELEASED':
        total_released += tx.amount_usdc

print(f"\n📊 RESUMEN DE FONDOS:")
print(f"   💰 Total bloqueado (LOCKED): ${total_locked} USDC")
print(f"   ✅ Total liberado (RELEASED): ${total_released} USDC")

# Calcular saldo disponible
saldo_disponible_cliente = cliente_wallet.balance_usdc - total_locked
print(f"\n💵 SALDOS DISPONIBLES:")
print(f"   Cliente: ${saldo_disponible_cliente} USDC (${cliente_wallet.balance_usdc} - ${total_locked} bloqueado)")
print(f"   Profesional: ${profesional_wallet.balance_usdc} USDC")

print("\n" + "="*70)
print("ACCESO A LA INTERFAZ WALLET ESCROW")
print("="*70)
print("""
🌐 URL: http://localhost:8000/usuarios/wallet/escrow/

📋 CARACTERÍSTICAS DE LA INTERFAZ:

1. ✅ SALDO TOTAL
   - Muestra el balance completo de la cuenta
   - Animación de conteo al cargar

2. 🔒 FONDOS EN GARANTÍA
   - Dinero bloqueado que está trabajando
   - No se puede retirar hasta que se libere

3. 💵 SALDO DISPONIBLE
   - Balance total menos fondos bloqueados
   - Este es el monto que puedes retirar

4. 📄 RECIBOS DIGITALES TRANSPARENTES
   - Cada trabajo en escrow tiene su recibo
   - Formato: "Seña del Trabajo #102: [Monto] - Estado: Protegido por Escrow"
   - Muestra profesional, porcentaje (30% o 70%), tipo de transacción

5. ▶️ BOTÓN "CONFIRMAR INICIO"
   - Solo visible para clientes con fondos bloqueados
   - Al hacer click: "Liberando Seña al Profesional..."
   - Libera el 30% y bloquea el 70% restante

6. 📜 HISTORIAL DE GARANTÍAS
   - Transacciones de escrow completadas
   - Fecha, trabajo, monto

🎨 DISEÑO DE ALTA SEGURIDAD:
   - Fondo oscuro (negro/azul oscuro)
   - Bordes definidos con glow effect
   - Colores:
     * Azul (#00d4ff) para elementos de seguridad
     * Dorado (#ffd700) para fondos bloqueados
     * Verde (#00ff88) para saldo disponible
   - Animaciones suaves y profesionales
   - Estilo de aplicación bancaria segura

🔐 ICONOS Y BADGES:
   - 🛡️ "PROTEGIDO" badge pulsante
   - 🔒 Candado para fondos en garantía
   - ✓ Check para disponibles
   - ⚡ Rayo para acciones rápidas

Login como cliente:
   Email: cliente@kunfido.com
   Password: cliente123

Login como profesional:
   Email: profesional@kunfido.com
   Password: profesional123
""")

print("="*70)
