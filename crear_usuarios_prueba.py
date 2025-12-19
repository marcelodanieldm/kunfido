"""
Script para crear usuarios de prueba en Kunfido
Ejecutar con: python crear_usuarios_prueba.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kunfido.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import UserProfile, Wallet
from decimal import Decimal

def crear_usuarios():
    print("🚀 Creando usuarios de prueba para Kunfido...\n")
    
    # Superusuario Admin
    print("👑 Creando SUPERUSUARIO ADMIN...")
    try:
        admin = User.objects.create_superuser(
            username='admin@kunfido.com',
            email='admin@kunfido.com',
            password='admin123',
            first_name='Admin',
            last_name='Kunfido'
        )
        
        print(f"   ✅ Email: admin@kunfido.com")
        print(f"   ✅ Password: admin123")
        print(f"   ✅ Rol: SUPERUSUARIO (Admin)")
        print(f"   ✅ Acceso: Footer de landing page (ícono escudo) o /admin/")
        print(f"   ✅ URL: http://127.0.0.1:8000/admin/\n")
        
    except Exception as e:
        print(f"   ⚠️  Superusuario 'admin' ya existe o error: {e}\n")
    
    # Usuario 1: Cliente (Persona)
    print("👤 Creando usuario CLIENTE (Persona)...")
    try:
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
        
        # Crear wallet con saldo
        wallet_cliente, created = Wallet.objects.get_or_create(
            user=user_cliente,
            defaults={
                'tipo_cuenta': 'USER',
                'balance_usdc': Decimal('5000.00')
            }
        )
        
        print(f"   ✅ Email: cliente@kunfido.com")
        print(f"   ✅ Password: cliente123")
        print(f"   ✅ Rol: PERSONA (Cliente)")
        print(f"   ✅ Zona: {profile_cliente.zona}")
        print(f"   ✅ Balance: {wallet_cliente.balance_usdc} USDC")
        print(f"   ✅ URL: http://127.0.0.1:8000/dashboard/\n")
        
    except Exception as e:
        print(f"   ⚠️  Usuario 'cliente' ya existe o error: {e}\n")
    
    # Usuario 2: Profesional (Oficio)
    print("🔧 Creando usuario PROFESIONAL (Oficio)...")
    try:
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
        
        # Crear wallet con saldo
        wallet_oficio, created = Wallet.objects.get_or_create(
            user=user_oficio,
            defaults={
                'tipo_cuenta': 'USER',
                'balance_usdc': Decimal('2500.00')
            }
        )
        
        print(f"   ✅ Email: profesional@kunfido.com")
        print(f"   ✅ Password: profesional123")
        print(f"   ✅ Rol: OFICIO (Profesional)")
        print(f"   ✅ Rubro: {profile_oficio.rubro}")
        print(f"   ✅ Balance: {wallet_oficio.balance_usdc} USDC")
        print(f"   ✅ URL: http://127.0.0.1:8000/dashboard/\n")
        
    except Exception as e:
        print(f"   ⚠️  Usuario 'profesional' ya existe o error: {e}\n")
    
    # Usuario 3: Consorcio
    print("🏢 Creando usuario CONSORCIO...")
    try:
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
        
        # Crear wallet con saldo
        wallet_consorcio, created = Wallet.objects.get_or_create(
            user=user_consorcio,
            defaults={
                'tipo_cuenta': 'USER',
                'balance_usdc': Decimal('10000.00')
            }
        )
        
        print(f"   ✅ Email: consorcio@kunfido.com")
        print(f"   ✅ Password: consorcio123")
        print(f"   ✅ Rol: CONSORCIO")
        print(f"   ✅ Dirección: {profile_consorcio.direccion}")
        print(f"   ✅ Balance: {wallet_consorcio.balance_usdc} USDC")
        print(f"   ✅ URL: http://127.0.0.1:8000/dashboard/\n")
        
    except Exception as e:
        print(f"   ⚠️  Usuario 'consorcio' ya existe o error: {e}\n")
    
    print("=" * 70)
    print("📋 RESUMEN DE USUARIOS CREADOS")
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
    print("\n✅ ¡Listo! Usuarios de prueba creados exitosamente.")
    print("   Ahora puedes probar el login sin Google Account.\n")

if __name__ == '__main__':
    crear_usuarios()
