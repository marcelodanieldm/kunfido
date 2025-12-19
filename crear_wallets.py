#!/usr/bin/env python
"""
Script para crear wallets para usuarios existentes.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kunfido.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Wallet
from decimal import Decimal

def crear_wallets():
    """Crea wallets para todos los usuarios que no tengan una."""
    usuarios = User.objects.all()
    creadas = 0
    existentes = 0
    
    for usuario in usuarios:
        wallet, created = Wallet.objects.get_or_create(
            user=usuario,
            defaults={
                'tipo_cuenta': 'USER',
                'balance_usdc': Decimal('1000.00')
            }
        )
        
        if created:
            creadas += 1
            print(f"✓ Wallet creada para {usuario.username} con 1000 USDC_MOCK")
        else:
            existentes += 1
            print(f"  Wallet ya existía para {usuario.username} (saldo: {wallet.balance_usdc} USDC_MOCK)")
    
    print(f"\n📊 Resumen:")
    print(f"   Wallets creadas: {creadas}")
    print(f"   Wallets existentes: {existentes}")
    print(f"   Total: {creadas + existentes}")

if __name__ == '__main__':
    crear_wallets()
