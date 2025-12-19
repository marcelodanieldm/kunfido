"""
Template tags personalizados para conversión de monedas.
"""

from django import template
from decimal import Decimal
from usuarios.currency_service import CurrencyService

register = template.Library()


@register.filter
def to_ars(value, tipo_cambio="blue"):
    """
    Convierte un valor en USDC a ARS.
    
    Uso: {{ wallet.balance_usdc|to_ars }}
    Uso: {{ wallet.balance_usdc|to_ars:"oficial" }}
    """
    try:
        if not value:
            return "0.00"
        return CurrencyService.convert_usdc_to_ars(value, tipo_cambio)
    except:
        return value


@register.filter
def format_ars(value):
    """
    Formatea un valor ARS con separadores de miles.
    
    Uso: {{ balance_ars|format_ars }}
    """
    try:
        if not value:
            return "$ 0,00"
        
        valor = Decimal(str(value))
        # Formato: $ 1.234.567,89
        partes = str(valor).split('.')
        entero = partes[0]
        decimal = partes[1] if len(partes) > 1 else "00"
        
        # Agregar separadores de miles
        entero_formateado = ""
        for i, digit in enumerate(reversed(entero)):
            if i > 0 and i % 3 == 0:
                entero_formateado = "." + entero_formateado
            entero_formateado = digit + entero_formateado
        
        return f"$ {entero_formateado},{decimal[:2]}"
    except:
        return value


@register.simple_tag
def get_exchange_rate(tipo_cambio="blue"):
    """
    Obtiene la tasa de cambio actual.
    
    Uso: {% get_exchange_rate "blue" as tasa %}
    """
    return CurrencyService.get_usdc_to_ars_rate(tipo_cambio)


@register.inclusion_tag('usuarios/currency_display.html')
def show_balance_dual(balance_usdc, tipo_cambio="blue"):
    """
    Muestra un balance en USDC y ARS de forma elegante.
    
    Uso: {% show_balance_dual wallet.balance_usdc %}
    """
    balance_ars = CurrencyService.convert_usdc_to_ars(balance_usdc, tipo_cambio)
    tasa = CurrencyService.get_usdc_to_ars_rate(tipo_cambio)
    
    return {
        'balance_usdc': balance_usdc,
        'balance_ars': balance_ars,
        'tasa': tasa,
        'tipo_cambio': tipo_cambio
    }
