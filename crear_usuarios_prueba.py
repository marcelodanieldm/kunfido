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
    print("🚀 Creando usuarios de prueba...\n")
    
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
        profile_oficio.zona = 'Recoleta, CABA'
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
        print(f"   ✅ Balance: {wallet_consorcio.balance_usdc} USDC")
        print(f"   ✅ URL: http://127.0.0.1:8000/dashboard/\n")
        
    except Exception as e:
        print(f"   ⚠️  Usuario 'consorcio' ya existe o error: {e}\n")
    
    print("=" * 60)
    print("📋 RESUMEN DE USUARIOS CREADOS")
    print("=" * 60)
    print("\n1️⃣  CLIENTE (Persona)")
    print("   Email: cliente@kunfido.com")
    print("   Password: cliente123")
    print("   Ver: http://127.0.0.1:8000/\n")
    
    print("2️⃣  PROFESIONAL (Oficio)")
    print("   Email: profesional@kunfido.com")
    print("   Password: profesional123")
    print("   Ver: http://127.0.0.1:8000/\n")
    
    print("3️⃣  CONSORCIO")
    print("   Email: consorcio@kunfido.com")
    print("   Password: consorcio123")
    print("   Ver: http://127.0.0.1:8000/\n")
    
    print("=" * 60)
    print("💡 Para iniciar sesión:")
    print("   1. Ve a: http://127.0.0.1:8000/accounts/login/")
    print("   2. Usa cualquiera de las credenciales de arriba")
    print("   3. Navega al Dashboard para ver las diferencias")
    print("=" * 60)
    print("\n✅ ¡Listo! Usuarios de prueba creados exitosamente.\n")

if __name__ == '__main__':
    crear_usuarios()
