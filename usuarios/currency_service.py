"""
Servicio para obtener cotizaciones de divisas en tiempo real.
Consume API externa para convertir USDC a ARS.
"""

import requests
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CurrencyService:
    """
    Servicio para gestionar cotizaciones de divisas.
    Usa caché para evitar llamadas excesivas a la API.
    """
    
    # APIs disponibles (con fallback)
    DOLAR_API_URL = "https://dolarapi.com/v1/dolares/blue"  # Dólar Blue Argentina
    DOLAR_API_OFICIAL_URL = "https://dolarapi.com/v1/dolares/oficial"  # Dólar Oficial
    BACKUP_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
    
    CACHE_KEY = "usdc_to_ars_rate"
    CACHE_TIMEOUT = 300  # 5 minutos
    
    # Tasa de respaldo en caso de fallo de API
    DEFAULT_RATE = Decimal("1000.00")
    
    @classmethod
    def get_usdc_to_ars_rate(cls, tipo_cambio="blue"):
        """
        Obtiene la tasa de conversión USDC a ARS.
        
        Args:
            tipo_cambio: "blue" (default), "oficial"
        
        Returns:
            Decimal: Tasa de conversión USDC a ARS
        """
        # Intentar obtener de caché
        cache_key = f"{cls.CACHE_KEY}_{tipo_cambio}"
        cached_rate = cache.get(cache_key)
        
        if cached_rate:
            logger.info(f"Tasa de cambio obtenida de caché: {cached_rate} ARS/USDC")
            return Decimal(str(cached_rate))
        
        # Obtener de API
        try:
            rate = cls._fetch_rate_from_api(tipo_cambio)
            
            # Guardar en caché
            cache.set(cache_key, float(rate), cls.CACHE_TIMEOUT)
            logger.info(f"Tasa de cambio obtenida de API: {rate} ARS/USDC")
            
            return rate
            
        except Exception as e:
            logger.error(f"Error al obtener tasa de cambio: {e}")
            return cls.DEFAULT_RATE
    
    @classmethod
    def _fetch_rate_from_api(cls, tipo_cambio="blue"):
        """
        Obtiene la tasa desde la API de DolarAPI.
        Usa dólar blue por defecto (más relevante para crypto).
        """
        try:
            # Seleccionar URL según tipo de cambio
            url = cls.DOLAR_API_URL if tipo_cambio == "blue" else cls.DOLAR_API_OFICIAL_URL
            
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # DolarAPI retorna { "venta": 1050.0, "compra": 1030.0 }
            # Usamos el precio de venta (lo que pagarías por 1 USD)
            tasa = Decimal(str(data.get("venta", data.get("compra", cls.DEFAULT_RATE))))
            
            if tasa <= 0:
                raise ValueError("Tasa inválida recibida de la API")
            
            return tasa
            
        except requests.RequestException as e:
            logger.warning(f"Error en DolarAPI, intentando API de respaldo: {e}")
            return cls._fetch_from_backup_api()
        except (KeyError, ValueError) as e:
            logger.error(f"Error al parsear respuesta de API: {e}")
            return cls._fetch_from_backup_api()
    
    @classmethod
    def _fetch_from_backup_api(cls):
        """
        API de respaldo usando ExchangeRate-API.
        """
        try:
            response = requests.get(cls.BACKUP_API_URL, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Esta API retorna rates["ARS"] que es cuántos ARS por 1 USD
            usd_to_ars = Decimal(str(data["rates"]["ARS"]))
            
            logger.info(f"Tasa obtenida de API de respaldo: {usd_to_ars}")
            return usd_to_ars
            
        except Exception as e:
            logger.error(f"Error en API de respaldo: {e}, usando tasa por defecto")
            return cls.DEFAULT_RATE
    
    @classmethod
    def convert_usdc_to_ars(cls, monto_usdc, tipo_cambio="blue"):
        """
        Convierte un monto de USDC a ARS.
        
        Args:
            monto_usdc: Decimal o float con el monto en USDC
            tipo_cambio: "blue" o "oficial"
        
        Returns:
            Decimal: Monto equivalente en ARS
        """
        if not monto_usdc:
            return Decimal("0.00")
        
        monto = Decimal(str(monto_usdc))
        tasa = cls.get_usdc_to_ars_rate(tipo_cambio)
        
        return (monto * tasa).quantize(Decimal("0.01"))
    
    @classmethod
    def convert_ars_to_usdc(cls, monto_ars, tipo_cambio="blue"):
        """
        Convierte un monto de ARS a USDC.
        
        Args:
            monto_ars: Decimal o float con el monto en ARS
            tipo_cambio: "blue" o "oficial"
        
        Returns:
            Decimal: Monto equivalente en USDC
        """
        if not monto_ars:
            return Decimal("0.00")
        
        monto = Decimal(str(monto_ars))
        tasa = cls.get_usdc_to_ars_rate(tipo_cambio)
        
        if tasa == 0:
            return Decimal("0.00")
        
        return (monto / tasa).quantize(Decimal("0.01"))
    
    @classmethod
    def get_rate_info(cls, tipo_cambio="blue"):
        """
        Obtiene información completa sobre la tasa actual.
        
        Returns:
            dict: {
                "tasa": Decimal,
                "tipo": str ("blue" o "oficial"),
                "timestamp": datetime
            }
        """
        from django.utils import timezone
        
        return {
            "tasa": cls.get_usdc_to_ars_rate(tipo_cambio),
            "tipo": tipo_cambio,
            "timestamp": timezone.now()
        }
    
    @classmethod
    def clear_cache(cls):
        """
        Limpia el caché de tasas de cambio.
        Útil para forzar actualización.
        """
        cache.delete(f"{cls.CACHE_KEY}_blue")
        cache.delete(f"{cls.CACHE_KEY}_oficial")
        logger.info("Caché de tasas de cambio limpiado")
