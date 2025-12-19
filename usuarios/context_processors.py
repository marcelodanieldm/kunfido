"""
Context processors para agregar información global a todos los templates.
"""

from .currency_service import CurrencyService
from decimal import Decimal


def currency_context(request):
    """
    Agrega información de cotización a todos los templates.
    """
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        wallet = getattr(request.user.profile, 'wallet', None)
        if wallet:
            tasa = CurrencyService.get_usdc_to_ars_rate(tipo_cambio="blue")
            balance_ars = wallet.get_balance_ars(tipo_cambio="blue")
            
            return {
                'exchange_rate_blue': tasa,
                'wallet_balance_ars': balance_ars,
            }
    
    return {
        'exchange_rate_blue': CurrencyService.get_usdc_to_ars_rate(tipo_cambio="blue"),
        'wallet_balance_ars': Decimal('0.00'),
    }
