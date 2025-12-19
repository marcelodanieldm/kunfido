# 💱 Sistema de Conversión USDC a ARS

## Descripción

Sistema que permite visualizar todos los balances en USDC con su equivalente en pesos argentinos (ARS) según la cotización en tiempo real del dólar blue.

---

## 🎯 Características Implementadas

### ✅ API de Cotización en Tiempo Real

- **API Principal:** [DolarAPI](https://dolarapi.com/) - Dólar Blue Argentina
- **API de Respaldo:** [ExchangeRate-API](https://www.exchangerate-api.com/) - USD/ARS
- **Caché:** 5 minutos para evitar llamadas excesivas
- **Fallback:** Tasa por defecto de 1000 ARS en caso de fallo

### ✅ Conversión Automática

Todos los balances en USDC se muestran con su equivalente en ARS:

1. **Navbar:** Muestra balance en USDC y ARS
2. **Dashboard Home:** Card de billetera con conversión
3. **Página de Wallet:** Balance principal con conversión destacada
4. **Cargar Fondos:** Usa tasa en tiempo real para conversión ARS → USDC

---

## 📁 Archivos Creados/Modificados

### Nuevos Archivos

1. **`usuarios/currency_service.py`**
   - Servicio principal de conversión
   - Consume APIs de cotización
   - Sistema de caché (5 minutos)
   - Métodos de conversión USDC ↔ ARS

2. **`usuarios/context_processors.py`**
   - Context processor para templates
   - Agrega `exchange_rate_blue` y `wallet_balance_ars` globalmente

3. **`usuarios/templatetags/currency_tags.py`**
   - Template tags personalizados
   - Filtros: `to_ars`, `format_ars`
   - Tag: `get_exchange_rate`

4. **`templates/usuarios/currency_display.html`**
   - Template parcial para mostrar balance dual
   - Componente reutilizable

### Archivos Modificados

1. **`usuarios/models.py` - Modelo Wallet**
   ```python
   def get_balance_ars(self, tipo_cambio="blue"):
       """Obtiene el balance convertido a ARS"""
       
   def get_exchange_rate(self, tipo_cambio="blue"):
       """Obtiene la tasa de cambio actual"""
   ```

2. **`usuarios/views.py`**
   - Importa `CurrencyService`
   - `wallet_detalle()`: Pasa `tasa_conversion` y `balance_ars` al contexto
   - `cargar_fondos()`: Usa tasa en tiempo real para conversión

3. **`kunfido/settings.py`**
   - Agregado context processor: `usuarios.context_processors.currency_context`

4. **`templates/includes/navbar.html`**
   - Muestra balance en USDC y ARS
   - Tooltip con cotización del dólar blue

5. **`templates/usuarios/dashboard_home.html`**
   - Card de billetera con conversión a ARS
   - Muestra cotización actual del dólar blue

6. **`templates/usuarios/wallet.html`**
   - Balance principal con conversión destacada
   - Estadística de cotización actual
   - Estilos CSS para balance en ARS

7. **`requirements.txt`**
   - Agregado: `requests==2.31.0`

---

## 🔧 Uso del Sistema

### En Python (Views/Models)

```python
from usuarios.currency_service import CurrencyService

# Obtener tasa actual
tasa = CurrencyService.get_usdc_to_ars_rate(tipo_cambio="blue")
# Retorna: Decimal("1485.00")

# Convertir USDC a ARS
monto_ars = CurrencyService.convert_usdc_to_ars(100)
# Retorna: Decimal("148500.00")

# Convertir ARS a USDC
monto_usdc = CurrencyService.convert_ars_to_usdc(148500)
# Retorna: Decimal("100.00")

# Desde el modelo Wallet
balance_ars = wallet.get_balance_ars(tipo_cambio="blue")
tasa = wallet.get_exchange_rate(tipo_cambio="blue")
```

### En Templates

```django
{% load currency_tags %}

<!-- Mostrar balance convertido a ARS -->
{{ wallet.balance_usdc|to_ars }}

<!-- Formatear ARS con separadores -->
{{ balance_ars|format_ars }}

<!-- Obtener tasa de cambio -->
{% get_exchange_rate "blue" as tasa %}
1 USDC = ${{ tasa }} ARS

<!-- Componente de balance dual -->
{% show_balance_dual wallet.balance_usdc %}
```

---

## 🌐 APIs Utilizadas

### 1. DolarAPI (Principal)

**URL:** https://dolarapi.com/v1/dolares/blue

**Respuesta:**
```json
{
  "moneda": "USD",
  "casa": "blue",
  "nombre": "Blue",
  "compra": 1480.00,
  "venta": 1485.00,
  "fechaActualizacion": "2025-12-19T14:30:00.000Z"
}
```

**Uso:** Cotización del dólar blue (paralelo) en Argentina

### 2. ExchangeRate-API (Respaldo)

**URL:** https://api.exchangerate-api.com/v4/latest/USD

**Respuesta:**
```json
{
  "base": "USD",
  "date": "2025-12-19",
  "rates": {
    "ARS": 1485.50,
    "EUR": 0.85,
    ...
  }
}
```

**Uso:** Tasa oficial USD/ARS como respaldo

---

## ⚡ Sistema de Caché

```python
# Configuración
CACHE_KEY = "usdc_to_ars_rate"
CACHE_TIMEOUT = 300  # 5 minutos

# La tasa se guarda en caché para:
# - Reducir llamadas a API externa
# - Mejorar rendimiento
# - Evitar límites de rate limiting
```

### Limpiar Caché Manualmente

```python
from usuarios.currency_service import CurrencyService

# Forzar actualización de cotización
CurrencyService.clear_cache()
```

---

## 🎨 Visualización en Templates

### Navbar
```
💰 1000.00 USDC ≈ $1,485,000 ARS
```

### Dashboard - Card de Billetera
```
┌──────────────────────┐
│   Mi Billetera       │
│                      │
│    1000.00          │
│    USDC_MOCK        │
│                      │
│  ↔ ≈ $1,485,000 ARS │
│  Dólar Blue: $1,485 │
└──────────────────────┘
```

### Página de Wallet
```
Balance Disponible
   1000.00
   Dólar Cripto (USDC_MOCK)
   ↔ ≈ $1,485,000.00 ARS 🛈

Estadísticas:
- Total Enviado: -500.00 USDC
- Total Recibido: +250.00 USDC
- Cotización Actual: 1 USDC = $1,485.00 ARS
  📈 Dólar Blue
```

---

## 🔒 Manejo de Errores

El sistema maneja todos los posibles errores:

1. **API no disponible:** Usa API de respaldo
2. **Ambas APIs fallan:** Usa tasa por defecto (1000 ARS)
3. **Timeout de red:** Timeout de 5 segundos
4. **Respuesta inválida:** Usa tasa por defecto
5. **Tasa = 0:** Previene división por cero

```python
try:
    tasa = CurrencyService.get_usdc_to_ars_rate()
except Exception as e:
    logger.error(f"Error: {e}")
    tasa = Decimal("1000.00")  # Fallback
```

---

## 📊 Ejemplo de Flujo Completo

### Usuario carga $100,000 ARS

1. **Usuario ingresa:** `$100,000 ARS`

2. **Sistema consulta API:**
   ```python
   tasa = CurrencyService.get_usdc_to_ars_rate()
   # Retorna: 1485.00 ARS
   ```

3. **Sistema convierte:**
   ```python
   usdc = CurrencyService.convert_ars_to_usdc(100000)
   # Retorna: 67.34 USDC
   ```

4. **Sistema muestra:**
   ```
   ✓ Fondos cargados exitosamente!
   $100,000 ARS = 67.34 USDC_MOCK
   Nuevo balance: 1067.34 USDC
   ```

5. **En navbar se actualiza:**
   ```
   💰 1067.34 USDC ≈ $1,585,000 ARS
   ```

---

## 🧪 Testing

### Probar el servicio

```bash
python manage.py shell
```

```python
from usuarios.currency_service import CurrencyService

# Obtener tasa actual
tasa = CurrencyService.get_usdc_to_ars_rate()
print(f"Tasa actual: {tasa}")

# Convertir 1000 USDC a ARS
ars = CurrencyService.convert_usdc_to_ars(1000)
print(f"1000 USDC = {ars} ARS")

# Convertir 1,000,000 ARS a USDC
usdc = CurrencyService.convert_ars_to_usdc(1000000)
print(f"1,000,000 ARS = {usdc} USDC")

# Limpiar caché
CurrencyService.clear_cache()
print("Caché limpiado")
```

### Probar template tags

```bash
python manage.py shell
```

```python
from usuarios.templatetags.currency_tags import to_ars, format_ars
from decimal import Decimal

# Probar conversión
resultado = to_ars(100)
print(f"100 USDC = {resultado} ARS")

# Probar formateo
formateado = format_ars(1485000.50)
print(f"Formato ARS: {formateado}")
# Output: $ 1.485.000,50
```

---

## 📈 Monitoreo

### Ver logs de conversión

Los logs incluyen información sobre:
- Tasas obtenidas de API
- Tasas obtenidas de caché
- Errores al consumir APIs
- Uso de tasas de respaldo

```python
import logging
logger = logging.getLogger(__name__)

# Mensajes típicos:
# INFO: Tasa de cambio obtenida de caché: 1485.00 ARS/USDC
# INFO: Tasa de cambio obtenida de API: 1485.00 ARS/USDC
# WARNING: Error en DolarAPI, intentando API de respaldo
# ERROR: Error al obtener tasa de cambio, usando tasa por defecto
```

---

## 🚀 Mejoras Futuras

1. **Dashboard de cotización:** Gráfico histórico de la cotización
2. **Alertas de cambio:** Notificar cuando la cotización cambia significativamente
3. **Múltiples monedas:** Agregar EUR, BTC, ETH
4. **Selector de dólar:** Permitir elegir entre Blue, Oficial, MEP, CCL
5. **API propia:** Cache más persistente en base de datos
6. **WebSockets:** Actualización en tiempo real sin refresh

---

## 💡 Notas Importantes

1. **Caché de 5 minutos:** La cotización se actualiza cada 5 minutos máximo
2. **Dólar Blue:** Se usa el dólar blue por defecto (más relevante para crypto)
3. **Precio de venta:** Se usa el precio de venta de la API (lo que pagarías por USD)
4. **Context processor:** Todas las páginas tienen acceso a `exchange_rate_blue` y `wallet_balance_ars`
5. **Rendimiento:** El sistema usa caché para no impactar la velocidad de carga

---

## ✅ Checklist de Implementación

- ✅ Servicio de conversión (`currency_service.py`)
- ✅ Métodos en modelo Wallet
- ✅ Context processor global
- ✅ Template tags personalizados
- ✅ Actualización de navbar
- ✅ Actualización de dashboard
- ✅ Actualización de wallet.html
- ✅ Conversión en tiempo real para carga de fondos
- ✅ Sistema de caché (5 minutos)
- ✅ Manejo de errores robusto
- ✅ APIs con fallback
- ✅ Documentación completa

---

**¡Sistema de conversión USDC → ARS completamente funcional!** 🎉

Cotización en tiempo real consumiendo API de DolarAPI con respaldo en ExchangeRate-API.
