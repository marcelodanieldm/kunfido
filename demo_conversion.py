"""
Demo del sistema de conversión USDC a ARS en tiempo real.
Ejecutar con: python demo_conversion.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kunfido.settings')
django.setup()

from usuarios.currency_service import CurrencyService
from usuarios.models import Wallet
from django.contrib.auth.models import User
from decimal import Decimal


def separator():
    print("\n" + "=" * 70 + "\n")


def demo_api_cotizacion():
    """Demuestra el consumo de la API y obtención de cotización."""
    print("🌐 DEMO: Consumo de API de Cotización")
    separator()
    
    print("📡 Consultando DolarAPI (Dólar Blue Argentina)...")
    tasa = CurrencyService.get_usdc_to_ars_rate(tipo_cambio="blue")
    
    print(f"✅ Cotización obtenida: 1 USDC = ${tasa} ARS")
    print(f"   (Dólar Blue - Actualización automática cada 5 minutos)")
    
    separator()


def demo_conversiones():
    """Demuestra conversiones USDC ↔ ARS."""
    print("💱 DEMO: Conversiones USDC ↔ ARS")
    separator()
    
    tasa = CurrencyService.get_usdc_to_ars_rate()
    
    # USDC a ARS
    print("📤 USDC → ARS")
    montos_usdc = [10, 100, 1000, 5000]
    
    for monto in montos_usdc:
        ars = CurrencyService.convert_usdc_to_ars(monto)
        print(f"   {monto:,} USDC = ${ars:,.2f} ARS")
    
    print()
    
    # ARS a USDC
    print("📥 ARS → USDC")
    montos_ars = [10000, 100000, 500000, 1000000]
    
    for monto in montos_ars:
        usdc = CurrencyService.convert_ars_to_usdc(monto)
        print(f"   ${monto:,} ARS = {usdc:,.2f} USDC")
    
    separator()


def demo_wallet_conversion():
    """Demuestra la conversión de balance de wallets."""
    print("💰 DEMO: Conversión de Balances de Wallets")
    separator()
    
    # Buscar usuarios de prueba
    usuarios = User.objects.filter(
        username__in=['cliente@kunfido.com', 'profesional@kunfido.com', 'consorcio@kunfido.com']
    )
    
    if not usuarios.exists():
        print("⚠️  No se encontraron usuarios de prueba.")
        print("   Ejecuta: python actualizar_usuarios_prueba.py")
        return
    
    tasa = CurrencyService.get_usdc_to_ars_rate()
    print(f"📊 Cotización actual: 1 USDC = ${tasa} ARS")
    print()
    
    for user in usuarios:
        if hasattr(user, 'wallet'):
            wallet = user.wallet
            balance_ars = wallet.get_balance_ars()
            
            print(f"👤 {user.get_full_name() or user.username}")
            print(f"   Balance: {wallet.balance_usdc} USDC")
            print(f"   En ARS:  ${balance_ars:,.2f} ARS")
            print(f"   Rol:     {user.profile.tipo_rol}")
            print()
    
    separator()


def demo_cache():
    """Demuestra el sistema de caché."""
    print("⚡ DEMO: Sistema de Caché")
    separator()
    
    import time
    from django.core.cache import cache
    
    print("1️⃣  Primera consulta (llamada a API):")
    start = time.time()
    tasa1 = CurrencyService.get_usdc_to_ars_rate()
    tiempo1 = (time.time() - start) * 1000
    print(f"   Tasa: ${tasa1} ARS")
    print(f"   Tiempo: {tiempo1:.2f}ms")
    
    print("\n2️⃣  Segunda consulta (desde caché):")
    start = time.time()
    tasa2 = CurrencyService.get_usdc_to_ars_rate()
    tiempo2 = (time.time() - start) * 1000
    print(f"   Tasa: ${tasa2} ARS")
    print(f"   Tiempo: {tiempo2:.2f}ms")
    
    velocidad = tiempo1 / tiempo2 if tiempo2 > 0 else 0
    print(f"\n⚡ Caché es {velocidad:.1f}x más rápido que llamada a API")
    
    print("\n3️⃣  Limpiando caché...")
    CurrencyService.clear_cache()
    print("   ✅ Caché limpiado")
    
    print("\n4️⃣  Consulta después de limpiar caché (nueva llamada a API):")
    start = time.time()
    tasa3 = CurrencyService.get_usdc_to_ars_rate()
    tiempo3 = (time.time() - start) * 1000
    print(f"   Tasa: ${tasa3} ARS")
    print(f"   Tiempo: {tiempo3:.2f}ms")
    
    separator()


def demo_carga_fondos():
    """Simula el proceso de carga de fondos."""
    print("💸 DEMO: Carga de Fondos con Conversión Real")
    separator()
    
    tasa = CurrencyService.get_usdc_to_ars_rate()
    
    print(f"💰 Cotización actual: 1 USDC = ${tasa} ARS")
    print()
    
    # Simular diferentes cargas
    montos_ars = [50000, 100000, 250000, 500000]
    
    print("📝 Simulación de cargas de fondos:")
    print()
    
    for monto_ars in montos_ars:
        monto_usdc = CurrencyService.convert_ars_to_usdc(monto_ars)
        
        print(f"   Usuario deposita: ${monto_ars:,} ARS")
        print(f"   → Recibe: {monto_usdc:,.2f} USDC")
        print(f"   Conversión aplicada a tasa: ${tasa}")
        print()
    
    separator()


def demo_comparacion_dolares():
    """Compara diferentes tipos de dólar."""
    print("📊 DEMO: Comparación Dólar Blue vs Oficial")
    separator()
    
    try:
        tasa_blue = CurrencyService.get_usdc_to_ars_rate(tipo_cambio="blue")
        tasa_oficial = CurrencyService.get_usdc_to_ars_rate(tipo_cambio="oficial")
        
        print(f"💵 Dólar Blue:    ${tasa_blue} ARS")
        print(f"🏦 Dólar Oficial: ${tasa_oficial} ARS")
        
        diferencia = tasa_blue - tasa_oficial
        porcentaje = (diferencia / tasa_oficial) * 100
        
        print(f"\n📈 Diferencia: ${diferencia} ARS ({porcentaje:.1f}% brecha)")
        
        print("\n💡 Kunfido usa Dólar Blue por defecto:")
        print("   - Más relevante para mercado de criptomonedas")
        print("   - Refleja el valor real del mercado paralelo")
        print("   - Es el que la gente usa para comprar/vender USDC")
        
    except Exception as e:
        print(f"⚠️  Error al obtener cotizaciones: {e}")
    
    separator()


def main():
    """Ejecuta todas las demos."""
    print("\n" + "🎯" * 35)
    print("  DEMO: SISTEMA DE CONVERSIÓN USDC → ARS EN TIEMPO REAL")
    print("🎯" * 35)
    
    try:
        demo_api_cotizacion()
        demo_conversiones()
        demo_cache()
        demo_carga_fondos()
        demo_wallet_conversion()
        demo_comparacion_dolares()
        
        print("✅ DEMO COMPLETADA EXITOSAMENTE")
        print("\n💡 Próximos pasos:")
        print("   1. Ejecuta el servidor: python manage.py runserver")
        print("   2. Login con cualquier usuario de prueba")
        print("   3. Ve al dashboard y observa la conversión automática")
        print("   4. Ve a tu Wallet y verás el balance en USDC y ARS")
        print("\n📚 Documentación completa en: SISTEMA_CONVERSION_DIVISAS.md")
        print()
        
    except Exception as e:
        print(f"\n❌ Error durante la demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
