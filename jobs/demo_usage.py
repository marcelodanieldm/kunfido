"""
Script de prueba para la app jobs.
Demuestra el uso de JobOffer, Bid y Vote con conversión ARS → USDC.

Ejecutar desde Django shell:
python manage.py shell < jobs/demo_usage.py

O importar en shell interactiva:
python manage.py shell
>>> exec(open('jobs/demo_usage.py').read())
"""

from django.contrib.auth.models import User
from usuarios.models import UserProfile
from jobs.models import JobOffer, Bid, Vote
from decimal import Decimal

print("\n" + "="*80)
print("DEMO: Sistema de Ofertas, Pujas y Votación - App Jobs")
print("="*80 + "\n")

# ============================================================================
# 1. CREAR USUARIOS Y PERFILES
# ============================================================================
print("📋 1. CREANDO USUARIOS Y PERFILES")
print("-" * 80)

# Cliente (Consorcio)
cliente_user, created = User.objects.get_or_create(
    username='consorcio_demo',
    defaults={
        'email': 'consorcio@demo.com',
        'first_name': 'Consorcio',
        'last_name': 'Torre Norte'
    }
)
if created:
    cliente_user.set_password('demo123')
    cliente_user.save()

cliente_profile, created = UserProfile.objects.get_or_create(
    user=cliente_user,
    defaults={
        'tipo_rol': 'CONSORCIO',
        'puntuacion': 95.0
    }
)
print(f"✓ Cliente: {cliente_user.get_full_name()} ({cliente_profile.tipo_rol})")

# Profesional 1 (Plomero)
prof1_user, created = User.objects.get_or_create(
    username='plomero_demo',
    defaults={
        'email': 'plomero@demo.com',
        'first_name': 'Juan',
        'last_name': 'Pérez'
    }
)
if created:
    prof1_user.set_password('demo123')
    prof1_user.save()

prof1_profile, created = UserProfile.objects.get_or_create(
    user=prof1_user,
    defaults={
        'tipo_rol': 'OFICIO',
        'puntuacion': 88.5
    }
)
print(f"✓ Profesional 1: {prof1_user.get_full_name()} ({prof1_profile.tipo_rol})")

# Profesional 2 (Plomero)
prof2_user, created = User.objects.get_or_create(
    username='plomero2_demo',
    defaults={
        'email': 'plomero2@demo.com',
        'first_name': 'Carlos',
        'last_name': 'González'
    }
)
if created:
    prof2_user.set_password('demo123')
    prof2_user.save()

prof2_profile, created = UserProfile.objects.get_or_create(
    user=prof2_user,
    defaults={
        'tipo_rol': 'OFICIO',
        'puntuacion': 92.0
    }
)
print(f"✓ Profesional 2: {prof2_user.get_full_name()} ({prof2_profile.tipo_rol})")

# Votantes
votante1, _ = User.objects.get_or_create(username='votante1', defaults={'email': 'v1@demo.com'})
votante2, _ = User.objects.get_or_create(username='votante2', defaults={'email': 'v2@demo.com'})
votante3, _ = User.objects.get_or_create(username='votante3', defaults={'email': 'v3@demo.com'})
print(f"✓ Votantes: {votante1.username}, {votante2.username}, {votante3.username}")

# ============================================================================
# 2. CREAR OFERTA DE TRABAJO
# ============================================================================
print("\n💼 2. CREANDO OFERTA DE TRABAJO")
print("-" * 80)

offer = JobOffer.objects.create(
    creator=cliente_profile,
    title='Reparación de Sistema de Cañerías',
    description='Se requiere reparar sistema de cañerías del edificio. '
                'Incluye diagnóstico, reparación de fugas y reemplazo de tuberías dañadas.',
    budget_base_ars=Decimal('150000.00'),
    is_consorcio=True,
    status='OPEN'
)

print(f"✓ Oferta creada: {offer.title}")
print(f"  - ID: {offer.id}")
print(f"  - Cliente: {offer.creator.user.get_full_name()}")
print(f"  - Presupuesto: ${offer.budget_base_ars:,.2f} ARS")
print(f"  - Presupuesto USDC: ${offer.budget_base_usdc} USDC")
print(f"  - Tasa de conversión: 1 USDC = 1200 ARS")
print(f"  - Estado: {offer.get_status_display()}")
print(f"  - ¿Puede recibir pujas? {'Sí' if offer.can_receive_bids() else 'No'}")

# ============================================================================
# 3. CREAR PUJAS
# ============================================================================
print("\n💰 3. PROFESIONALES ENVIANDO PUJAS")
print("-" * 80)

bid1 = Bid.objects.create(
    job_offer=offer,
    professional=prof1_profile,
    amount_ars=Decimal('135000.00'),
    estimated_days=7,
    pitch_text='Tengo 15 años de experiencia en plomería. '
                'Equipo completo de 3 personas. Referencias verificables. '
                'Garantía de 2 años en todos los trabajos.'
)

print(f"✓ Puja #1 - {prof1_user.get_full_name()}")
print(f"  - Monto: ${bid1.amount_ars:,.2f} ARS = ${bid1.amount_usdc} USDC")
print(f"  - Días estimados: {bid1.estimated_days}")
print(f"  - Propuesta: {bid1.pitch_text[:70]}...")

bid2 = Bid.objects.create(
    job_offer=offer,
    professional=prof2_profile,
    amount_ars=Decimal('128000.00'),
    estimated_days=5,
    pitch_text='Trabajo express. Puedo empezar mañana mismo. '
                'Equipo de 5 personas con experiencia en consorcios. '
                'Materiales de primera calidad incluidos.'
)

print(f"\n✓ Puja #2 - {prof2_user.get_full_name()}")
print(f"  - Monto: ${bid2.amount_ars:,.2f} ARS = ${bid2.amount_usdc} USDC")
print(f"  - Días estimados: {bid2.estimated_days}")
print(f"  - Propuesta: {bid2.pitch_text[:70]}...")

# ============================================================================
# 4. SISTEMA DE VOTACIÓN
# ============================================================================
print("\n🗳️  4. SISTEMA DE VOTACIÓN")
print("-" * 80)

# Votar por puja 1
voted1, vote1 = Vote.toggle_vote(votante1, bid1)
print(f"{'✓' if voted1 else '✗'} {votante1.username} votó por Puja #1")

voted2, vote2 = Vote.toggle_vote(votante2, bid1)
print(f"{'✓' if voted2 else '✗'} {votante2.username} votó por Puja #1")

# Votar por puja 2
voted3, vote3 = Vote.toggle_vote(votante3, bid2)
print(f"{'✓' if voted3 else '✗'} {votante3.username} votó por Puja #2")

print(f"\n📊 Resultados:")
print(f"  - Puja #1: {bid1.total_votes} voto(s)")
print(f"  - Puja #2: {bid2.total_votes} voto(s)")

# Verificar si ya votaron
print(f"\n🔍 Verificaciones:")
print(f"  - ¿{votante1.username} ya votó por Puja #1? {Vote.user_has_voted(votante1, bid1)}")
print(f"  - ¿{votante3.username} ya votó por Puja #1? {Vote.user_has_voted(votante3, bid1)}")

# ============================================================================
# 5. SELECCIONAR GANADOR
# ============================================================================
print("\n🏆 5. SELECCIONANDO PUJA GANADORA")
print("-" * 80)

# Obtener puja con más votos
from django.db.models import Count
winning_bid = offer.get_active_bids().annotate(
    vote_count=Count('votes')
).order_by('-vote_count').first()

print(f"Puja ganadora: Puja #{winning_bid.id}")
print(f"  - Profesional: {winning_bid.professional.user.get_full_name()}")
print(f"  - Monto: ${winning_bid.amount_ars:,.2f} ARS (${winning_bid.amount_usdc} USDC)")
print(f"  - Votos: {winning_bid.total_votes}")

# Marcar como ganadora
print(f"\n⚙️  Marcando como ganadora...")
winning_bid.mark_as_winner()

# Refrescar estado
offer.refresh_from_db()
winning_bid.refresh_from_db()

print(f"✓ Puja marcada como ganadora")
print(f"  - Estado de la oferta: {offer.get_status_display()}")
print(f"  - ¿Es ganadora? {winning_bid.is_winner}")

# ============================================================================
# 6. RESUMEN FINAL
# ============================================================================
print("\n" + "="*80)
print("📈 RESUMEN FINAL")
print("="*80 + "\n")

print(f"Oferta: {offer.title}")
print(f"  - Estado: {offer.get_status_display()}")
print(f"  - Presupuesto cliente: ${offer.budget_base_ars:,.2f} ARS (${offer.budget_base_usdc} USDC)")
print(f"  - Total de pujas: {offer.bids.count()}")

print(f"\nPuja ganadora:")
final_winner = offer.get_winning_bid()
if final_winner:
    print(f"  - Profesional: {final_winner.professional.user.get_full_name()}")
    print(f"  - Monto acordado: ${final_winner.amount_ars:,.2f} ARS (${final_winner.amount_usdc} USDC)")
    print(f"  - Ahorro para el cliente: ${offer.budget_base_ars - final_winner.amount_ars:,.2f} ARS")
    print(f"  - Días de trabajo: {final_winner.estimated_days}")
    print(f"  - Total de votos: {final_winner.total_votes}")

print("\n" + "="*80)
print("✅ DEMO COMPLETADO EXITOSAMENTE")
print("="*80 + "\n")

print("💡 Comandos útiles para explorar:")
print("   JobOffer.objects.all()")
print("   Bid.objects.filter(is_winner=True)")
print("   Vote.objects.count()")
print("   offer.get_active_bids()")
print("   bid.amount_usdc  # Ver conversión ARS → USDC")
print()
