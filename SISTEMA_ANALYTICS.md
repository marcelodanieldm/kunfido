# 📊 SISTEMA DE ANALYTICS - DOCUMENTACIÓN COMPLETA

## 📋 Descripción General

Sistema de análisis y reportes para superadministradores con KPIs del negocio, métricas en tiempo real y exportación de datos para facturación.

---

## 🎯 Características Principales

### 1. **Dashboard de KPIs**
Dashboard ejecutivo con métricas clave del negocio en tiempo real.

### 2. **Sistema de Facturación CSV**
Exportación de reportes descargables con información fiscal completa.

### 3. **Protección por Roles**
Acceso exclusivo para superusuarios mediante `@user_passes_test(lambda u: u.is_superuser)`.

---

## 📊 KPIs Implementados

### 🏆 KPI 1: GMV Total (Gross Merchandise Value)
**Definición:** Suma de todos los presupuestos de trabajos activos y finalizados.

**Cálculo:**
```python
gmv_data = JobOffer.objects.filter(
    Q(status='IN_PROGRESS') | Q(status='CLOSED')
).aggregate(
    total_ars=Sum('budget_base_ars')
)

gmv_total_ars = gmv_data['total_ars'] or Decimal('0.00')
```

**Estados incluidos:**
- `IN_PROGRESS`: Trabajos en ejecución
- `CLOSED`: Trabajos finalizados

**Monedas:**
- ARS (Pesos Argentinos)
- USDC (Dólares Stablecoin)

---

### 💰 KPI 2: Comisiones Acumuladas
**Definición:** 5% de comisión sobre todos los trabajos finalizados.

**Cálculo (ARS):**
```python
comisiones_data = JobOffer.objects.filter(
    status='CLOSED'
).aggregate(
    total_finalizados_ars=Sum('budget_base_ars')
)

total_finalizados_ars = comisiones_data['total_finalizados_ars'] or Decimal('0.00')
comision_tasa = Decimal('0.05')  # 5%
comisiones_ars = (total_finalizados_ars * comision_tasa).quantize(
    Decimal('0.01'), 
    rounding=ROUND_HALF_UP
)
```

**Cálculo (USDC):**
```python
comisiones_usdc_data = EscrowTransaction.objects.filter(
    transaction_type='PLATFORM_FEE',
    status='RELEASED'
).aggregate(
    total_comision_usdc=Sum('amount_usdc')
)

comisiones_usdc = comisiones_usdc_data['total_comision_usdc'] or Decimal('0.00')
```

**Fuentes:**
- ARS: Calculado sobre `budget_base_ars` de trabajos CLOSED
- USDC: Transacciones escrow tipo `PLATFORM_FEE` ya liberadas

---

### 🔒 KPI 3: Fondos en Escrow
**Definición:** Suma de todo el dinero bloqueado en garantía actualmente.

**Cálculo:**
```python
fondos_escrow_data = EscrowTransaction.objects.filter(
    status='LOCKED'
).aggregate(
    total_bloqueado=Sum('amount_usdc')
)

fondos_en_escrow = fondos_escrow_data['total_bloqueado'] or Decimal('0.00')
```

**Incluye:**
- Señas del 30% bloqueadas
- Saldos del 70% bloqueados
- Todas las transacciones con `status='LOCKED'`

---

### ⏰ KPI 4: Tasa de Atraso
**Definición:** Porcentaje de trabajos en progreso que tienen retraso.

**Cálculo:**
```python
trabajos_en_progreso = JobOffer.objects.filter(status='IN_PROGRESS').count()
trabajos_atrasados = JobOffer.objects.filter(
    status='IN_PROGRESS',
    is_delayed=True
).count()

if trabajos_en_progreso > 0:
    tasa_atraso = (trabajos_atrasados / trabajos_en_progreso) * 100
else:
    tasa_atraso = 0.0
```

**Fórmula:**
```
Tasa de Atraso = (Trabajos Atrasados / Trabajos en Progreso) × 100
```

**Flag de atraso:**
- Campo: `JobOffer.is_delayed`
- Actualizado automáticamente al verificar fecha de entrega

---

## 📥 Sistema de Facturación CSV

### 📄 Reporte 1: Todas las Transacciones
**URL:** `/analytics/reporte/transacciones/csv/`

**Columnas incluidas:**
1. ID Transacción
2. Fecha
3. Tipo de Transacción
4. Estado
5. ID Trabajo
6. Título Trabajo
7. Cliente
8. CUIT/DNI Cliente
9. Email Cliente
10. Profesional
11. CUIT/DNI Profesional
12. Email Profesional
13. Monto (USDC)
14. Comisión Plataforma (USDC)
15. Comisión %
16. Wallet Origen
17. Wallet Destino
18. Descripción

**Formato:**
- Separador: punto y coma (`;`)
- Encoding: UTF-8 con BOM (compatible con Excel)
- Quoting: Todas las celdas entrecomilladas

**Ejemplo de código:**
```python
writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)

writer.writerow([
    tx.id,
    tx.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    tx.get_transaction_type_display(),
    tx.get_status_display(),
    tx.job.id if tx.job else '',
    tx.job.title if tx.job else '',
    cliente_nombre,
    cliente_cuit,
    cliente_email,
    profesional_nombre,
    profesional_cuit,
    profesional_email,
    f"{tx.amount_usdc:.2f}",
    f"{comision_monto:.2f}",
    comision_porcentaje,
    wallet_origen,
    wallet_destino,
    tx.description or '',
])
```

---

### 📄 Reporte 2: Comisiones (Específico para Facturación)
**URL:** `/analytics/reporte/comisiones/csv/`

**Columnas incluidas:**
1. Fecha de Facturación
2. ID Transacción
3. ID Trabajo
4. Título del Trabajo
5. Cliente - Razón Social
6. Cliente - CUIT/DNI
7. Cliente - Email
8. Profesional - Razón Social
9. Profesional - CUIT/DNI
10. Profesional - Email
11. Monto Base del Trabajo (USDC)
12. Comisión Plataforma (USDC)
13. Comisión %
14. Estado de Pago
15. Fecha de Pago
16. Observaciones

**Filtro aplicado:**
```python
comisiones = EscrowTransaction.objects.filter(
    transaction_type='PLATFORM_FEE'
).select_related(
    'job',
    'job__creator',
    'job__creator__user',
    'bid',
    'bid__professional',
    'bid__professional__user'
).order_by('-created_at')
```

**Solo incluye:**
- Transacciones de tipo `PLATFORM_FEE` (comisión del 5%)
- Ordenadas por fecha (más recientes primero)

**Estados de pago:**
- `PAGADO`: Si `status='RELEASED'`
- `PENDIENTE`: Si `status='LOCKED'` o cualquier otro

---

## 🔐 Seguridad y Acceso

### Protección de Vistas
Todas las vistas usan el decorador:
```python
@user_passes_test(lambda u: u.is_superuser)
```

**Validación:**
- Solo usuarios con `is_superuser=True` pueden acceder
- Redirige a login si el usuario no es superusuario
- Retorna 403 Forbidden si está autenticado pero no es superuser

### URLs Protegidas
```python
urlpatterns = [
    path('dashboard/', views.superuser_dashboard, name='superuser_dashboard'),
    path('reporte/transacciones/csv/', views.generar_reporte_csv, name='reporte_csv'),
    path('reporte/comisiones/csv/', views.generar_reporte_comisiones_csv, name='reporte_comisiones_csv'),
]
```

---

## 🎨 Diseño del Dashboard

### Paleta de Colores
```css
Fondo: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)
Cards: linear-gradient(135deg, #1e2a38 0%, #0f1620 100%)
Bordes: #2c3e50
Acentos: #00d4ff (cyan), #ffd700 (gold), #ff6b6b (red)
```

### Componentes Visuales
1. **Header con Badge Superadmin:** Animación pulse
2. **KPI Cards:** Gradientes animados, hover effects
3. **Tablas de Stats:** Badges de colores por estado
4. **Botones de Descarga:** Gradiente cyan con hover 3D

### Animaciones CSS
```css
@keyframes pulse-admin {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}
```

---

## 📈 Métricas Adicionales Incluidas

### 1. Usuarios por Tipo de Rol
```python
usuarios_stats = UserProfile.objects.values('tipo_rol').annotate(
    total=Count('id')
)
```

**Roles:**
- PERSONA
- CONSORCIO
- OFICIO

---

### 2. Trabajos por Estado
```python
trabajos_stats = JobOffer.objects.values('status').annotate(
    total=Count('id')
)
```

**Estados:**
- OPEN (Abierta)
- IN_PROGRESS (En Progreso)
- CLOSED (Cerrada)

---

### 3. Transacciones Escrow por Tipo
```python
escrow_stats = EscrowTransaction.objects.values('transaction_type').annotate(
    total=Count('id'),
    monto_total=Sum('amount_usdc')
)
```

**Tipos:**
- INITIAL_DEPOSIT (30%)
- REMAINING_DEPOSIT (70%)
- INITIAL_RELEASE (Liberar 30%)
- FINAL_RELEASE (Liberar 65%)
- PLATFORM_FEE (5%)
- REFUND (Reembolso)

---

### 4. Últimas 10 Transacciones
```python
ultimas_transacciones = EscrowTransaction.objects.select_related(
    'job', 'bid', 'from_wallet', 'to_wallet'
).order_by('-created_at')[:10]
```

**Información mostrada:**
- ID de transacción
- Fecha y hora
- Trabajo asociado (con link)
- Tipo de transacción
- Monto en USDC
- Estado (Bloqueado/Liberado/Reembolsado)

---

## 🚀 Uso del Sistema

### 1. Acceso al Dashboard
```
URL: http://localhost:8000/analytics/dashboard/
```

**Requisitos:**
- Usuario con `is_superuser=True`
- Sesión activa

### 2. Descargar Reporte de Transacciones
```
URL: http://localhost:8000/analytics/reporte/transacciones/csv/
```

**Resultado:**
- Archivo: `reporte_transacciones_YYYYMMDD_HHMMSS.csv`
- Todas las transacciones del sistema
- Compatible con Excel

### 3. Descargar Reporte de Comisiones
```
URL: http://localhost:8000/analytics/reporte/comisiones/csv/
```

**Resultado:**
- Archivo: `reporte_comisiones_YYYYMMDD_HHMMSS.csv`
- Solo comisiones de plataforma (5%)
- Listo para contabilidad/facturación

---

## 🧪 Testing y Demo

### Ejecutar Demo
```bash
python manage.py shell < demo_analytics.py
```

**Muestra:**
- Valores actuales de cada KPI
- Estadísticas por rol y estado
- URLs de acceso
- Instrucciones de uso

### Crear Superusuario
```bash
python manage.py createsuperuser
```

---

## 📦 Dependencias

### Modelos Externos Usados
1. **jobs.models:**
   - `JobOffer`: Trabajos y presupuestos
   - `Bid`: Pujas de profesionales
   - `EscrowTransaction`: Transacciones blindadas

2. **usuarios.models:**
   - `UserProfile`: Perfiles y roles
   - `Wallet`: Billeteras digitales
   - `Transaction`: Historial de transacciones

### Módulos Python
```python
import csv  # Para generación de reportes
from decimal import Decimal, ROUND_HALF_UP  # Precisión financiera
from django.db.models import Sum, Q, Count, F  # Agregaciones
from django.utils import timezone  # Manejo de fechas
```

---

## 🔄 Actualizaciones en Tiempo Real

### Cálculo Dinámico
Todos los KPIs se calculan en tiempo real al cargar el dashboard:
- No hay caché
- Datos siempre actualizados
- Queries optimizados con `select_related` y `aggregate`

### Performance
```python
# Optimización con select_related
transacciones = EscrowTransaction.objects.select_related(
    'job',
    'job__creator',
    'job__creator__user',
    'bid',
    'bid__professional',
    'bid__professional__user'
)
```

---

## 📝 Notas de CUIT/DNI

### Estado Actual
El sistema usa `username` como identificador:
```python
cliente_cuit = f"Usuario: {tx.job.creator.user.username}"
```

### Mejora Futura
Agregar campo `cuit` al modelo `UserProfile`:
```python
class UserProfile(models.Model):
    cuit = models.CharField(max_length=13, blank=True, null=True)
```

Luego actualizar el CSV para usar:
```python
cliente_cuit = tx.job.creator.cuit or f"Usuario: {tx.job.creator.user.username}"
```

---

## ✅ Checklist de Implementación

- [x] App `analytics` creada
- [x] Vista `superuser_dashboard` con 4 KPIs
- [x] Vista `generar_reporte_csv` para todas las transacciones
- [x] Vista `generar_reporte_comisiones_csv` para facturación
- [x] Template `superuser_dashboard.html` con diseño de alta seguridad
- [x] Decorador `@user_passes_test(lambda u: u.is_superuser)` en todas las vistas
- [x] URLs configuradas en `analytics/urls.py`
- [x] App agregada a `INSTALLED_APPS`
- [x] URLs incluidas en proyecto principal
- [x] Script de demostración `demo_analytics.py`
- [x] Documentación completa

---

## 🎯 Casos de Uso

### 1. Monitoreo de Ingresos
**Acción:** Revisar dashboard diariamente  
**KPI:** GMV Total + Comisiones Acumuladas  
**Objetivo:** Seguimiento de crecimiento del negocio

### 2. Auditoría Fiscal
**Acción:** Descargar reporte de comisiones mensual  
**KPI:** Comisiones Acumuladas  
**Objetivo:** Declaración de ingresos para AFIP

### 3. Control de Riesgos
**Acción:** Revisar Fondos en Escrow  
**KPI:** Fondos en Escrow  
**Objetivo:** Verificar liquidez disponible

### 4. Gestión de Calidad
**Acción:** Monitorear Tasa de Atraso  
**KPI:** Tasa de Atraso  
**Objetivo:** Identificar problemas operacionales

---

## 🔗 Enlaces Rápidos

- Dashboard: `/analytics/dashboard/`
- Reporte Transacciones: `/analytics/reporte/transacciones/csv/`
- Reporte Comisiones: `/analytics/reporte/comisiones/csv/`

---

**Desarrollado por:** Senior Backend Developer  
**Fecha:** Diciembre 2025  
**Versión:** 1.0
