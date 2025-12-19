"""
Script para actualizar perfiles de usuarios de prueba existentes en Kunfido
Ejecutar con: python actualizar_usuarios_prueba.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kunfido.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import UserProfile, Wallet
from decimal import Decimal

def actualizar_usuarios():
    print("🔄 Actualizando usuarios de prueba para Kunfido...\n")
    
    # Superusuario Admin
    print("👑 Verificando SUPERUSUARIO ADMIN...")
    try:
        admin = User.objects.get(username='admin@kunfido.com')
        if not admin.is_superuser:
            admin.is_superuser = True
            admin.is_staff = True
            admin.save()
            print(f"   ✅ Permisos de superusuario activados")
        
        print(f"   ✅ Email: admin@kunfido.com")
        print(f"   ✅ Password: admin123")
        print(f"   ✅ Rol: SUPERUSUARIO (Admin)")
        print(f"   ✅ URL: http://127.0.0.1:8000/admin/\n")
        
    except User.DoesNotExist:
        print(f"   ⚠️  Usuario admin no existe, creando...")
        admin = User.objects.create_superuser(
            username='admin@kunfido.com',
            email='admin@kunfido.com',
            password='admin123',
            first_name='Admin',
            last_name='Kunfido'
        )
        print(f"   ✅ Superusuario creado\n")
    
    # Usuario 1: Cliente (Persona)
    print("👤 Actualizando usuario CLIENTE (Persona)...")
    try:
        user_cliente = User.objects.get(username='cliente@kunfido.com')
        profile_cliente = UserProfile.objects.get(user=user_cliente)
        profile_cliente.tipo_rol = 'PERSONA'
        profile_cliente.zona = 'Palermo, CABA'
        profile_cliente.telefono = '+54 9 11 1234-5678'
        profile_cliente.puntuacion = 4.8
        profile_cliente.save()
        
        wallet_cliente, created = Wallet.objects.get_or_create(
            user=user_cliente,
            defaults={
                'tipo_cuenta': 'USER',
                'balance_usdc': Decimal('5000.00')
            }
        )
        if not created and wallet_cliente.balance_usdc == 0:
            wallet_cliente.balance_usdc = Decimal('5000.00')
            wallet_cliente.save()
        
        print(f"   ✅ Email: cliente@kunfido.com")
        print(f"   ✅ Rol: PERSONA actualizado")
        print(f"   ✅ Zona: {profile_cliente.zona}")
        print(f"   ✅ Balance: {wallet_cliente.balance_usdc} USDC\n")
        
    except User.DoesNotExist:
        print(f"   ⚠️  Usuario cliente no existe, creando...")
        user_cliente = User.objects.create_user(
            username='cliente@kunfido.com',
            email='cliente@kunfido.com',
            password='cliente123',
            first_name='María',
            last_name='González'
        )
        profile_cliente = UserProfile.objects.get(user=user_cliente)
        profile_cliente.tipo_rol = 'PERSONA'
        profile_cliente.zona = 'Palermo, CABA'
        profile_cliente.telefono = '+54 9 11 1234-5678'
        profile_cliente.puntuacion = 4.8
        profile_cliente.save()
        
        Wallet.objects.create(
            user=user_cliente,
            tipo_cuenta='USER',
            balance_usdc=Decimal('5000.00')
        )
        print(f"   ✅ Usuario cliente creado\n")
    
    # Usuario 2: Profesional (Oficio)
    print("🔧 Actualizando usuario PROFESIONAL (Oficio)...")
    try:
        user_oficio = User.objects.get(username='profesional@kunfido.com')
        profile_oficio = UserProfile.objects.get(user=user_oficio)
        profile_oficio.tipo_rol = 'OFICIO'
        profile_oficio.rubro = 'PLOMERIA'
        profile_oficio.zona = 'Recoleta, CABA'
        profile_oficio.cuit = '20-12345678-9'
        profile_oficio.puntuacion = 4.9
        profile_oficio.save()
        
        wallet_oficio, created = Wallet.objects.get_or_create(
            user=user_oficio,
            defaults={
                'tipo_cuenta': 'USER',
                'balance_usdc': Decimal('2500.00')
            }
        )
        if not created and wallet_oficio.balance_usdc == 0:
            wallet_oficio.balance_usdc = Decimal('2500.00')
            wallet_oficio.save()
        
        print(f"   ✅ Email: profesional@kunfido.com")
        print(f"   ✅ Rol: OFICIO actualizado")
        print(f"   ✅ Rubro: {profile_oficio.rubro}")
        print(f"   ✅ Balance: {wallet_oficio.balance_usdc} USDC\n")
        
    except User.DoesNotExist:
        print(f"   ⚠️  Usuario profesional no existe, creando...")
        user_oficio = User.objects.create_user(
            username='profesional@kunfido.com',
            email='profesional@kunfido.com',
            password='profesional123',
            first_name='Juan',
            last_name='Pérez'
        )
        profile_oficio = UserProfile.objects.get(user=user_oficio)
        profile_oficio.tipo_rol = 'OFICIO'
        profile_oficio.rubro = 'PLOMERIA'
        profile_oficio.zona = 'Recoleta, CABA'
        profile_oficio.cuit = '20-12345678-9'
        profile_oficio.puntuacion = 4.9
        profile_oficio.save()
        
        Wallet.objects.create(
            user=user_oficio,
            tipo_cuenta='USER',
            balance_usdc=Decimal('2500.00')
        )
        print(f"   ✅ Usuario profesional creado\n")
    
    # Usuario 3: Consorcio
    print("🏢 Actualizando usuario CONSORCIO...")
    try:
        user_consorcio = User.objects.get(username='consorcio@kunfido.com')
        profile_consorcio = UserProfile.objects.get(user=user_consorcio)
        profile_consorcio.tipo_rol = 'CONSORCIO'
        profile_consorcio.direccion = 'Av. Belgrano 1234, CABA'
        profile_consorcio.matricula = 'MAT-12345'
        profile_consorcio.zona = 'Belgrano, CABA'
        profile_consorcio.puntuacion = 4.7
        profile_consorcio.save()
        
        wallet_consorcio, created = Wallet.objects.get_or_create(
            user=user_consorcio,
            defaults={
                'tipo_cuenta': 'USER',
                'balance_usdc': Decimal('10000.00')
            }
        )
        if not created and wallet_consorcio.balance_usdc == 0:
            wallet_consorcio.balance_usdc = Decimal('10000.00')
            wallet_consorcio.save()
        
        print(f"   ✅ Email: consorcio@kunfido.com")
        print(f"   ✅ Rol: CONSORCIO actualizado")
        print(f"   ✅ Dirección: {profile_consorcio.direccion}")
        print(f"   ✅ Balance: {wallet_consorcio.balance_usdc} USDC\n")
        
    except User.DoesNotExist:
        print(f"   ⚠️  Usuario consorcio no existe, creando...")
        user_consorcio = User.objects.create_user(
            username='consorcio@kunfido.com',
            email='consorcio@kunfido.com',
            password='consorcio123',
            first_name='Consorcio',
            last_name='Belgrano Tower'
        )
        profile_consorcio = UserProfile.objects.get(user=user_consorcio)
        profile_consorcio.tipo_rol = 'CONSORCIO'
        profile_consorcio.direccion = 'Av. Belgrano 1234, CABA'
        profile_consorcio.matricula = 'MAT-12345'
        profile_consorcio.zona = 'Belgrano, CABA'
        profile_consorcio.puntuacion = 4.7
        profile_consorcio.save()
        
        Wallet.objects.create(
            user=user_consorcio,
            tipo_cuenta='USER',
            balance_usdc=Decimal('10000.00')
        )
        print(f"   ✅ Usuario consorcio creado\n")
    
    print("=" * 70)
    print("📋 USUARIOS DE PRUEBA ACTUALIZADOS")
    print("=" * 70)
    
    print("\n👑 SUPERUSUARIO ADMIN")
    print("   Email:    admin@kunfido.com")
    print("   Password: admin123")
    print("   Acceso:   Footer landing page (ícono escudo) o /admin/")
    print("   URL:      http://127.0.0.1:8000/admin/\n")
    
    print("1️⃣  CLIENTE (Persona)")
    print("   Email:    cliente@kunfido.com")
    print("   Password: cliente123")
    print("   Zona:     Palermo, CABA")
    print("   Login:    http://127.0.0.1:8000/accounts/login/\n")
    
    print("2️⃣  PROFESIONAL (Oficio)")
    print("   Email:    profesional@kunfido.com")
    print("   Password: profesional123")
    print("   Rubro:    Plomería")
    print("   Login:    http://127.0.0.1:8000/accounts/login/\n")
    
    print("3️⃣  CONSORCIO")
    print("   Email:    consorcio@kunfido.com")
    print("   Password: consorcio123")
    print("   Edificio: Av. Belgrano 1234, CABA")
    print("   Login:    http://127.0.0.1:8000/accounts/login/\n")
    
    print("=" * 70)
    print("💡 FORMAS DE INICIAR SESIÓN:")
    print("=" * 70)
    print("\n📱 USUARIOS REGULARES:")
    print("   • Landing Page: Botón 'Iniciar Sesión' en navbar (modal azul)")
    print("   • URL Directa:  http://127.0.0.1:8000/accounts/login/")
    print("   • Usa Email + Password (no necesitas Google Account)")
    print("\n👑 SUPERUSUARIO ADMIN:")
    print("   • Landing Page: Ícono escudo en footer (modal rojo)")
    print("   • URL Directa:  http://127.0.0.1:8000/admin/")
    print("=" * 70)
    print("\n✅ ¡Listo! Usuarios actualizados y listos para login.\n")

if __name__ == '__main__':
    actualizar_usuarios()
