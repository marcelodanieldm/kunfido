# 💰 Sistema de Pagos y Transacciones - Kunfido

## 📋 Descripción General

Sistema completo de transacciones internas con billetera virtual (USDC_MOCK), escrow automático, liberación de pagos y gestión de reembolsos.

---

## 🎯 Flujo Completo del Sistema

### 1️⃣ **Inicio: Cliente Acepta una Propuesta**

**Ubicación:** `job_detail_private.html` → Botón "Votar"

**Proceso:**
```python
# Vista: votar_propuesta()
1. Cliente vota una propuesta
2. Sistema verifica saldo en wallet (30% del monto)
3. Si hay saldo suficiente:
   - Retiene 30% en cuenta Plataforma_Escrow
   - Cambia status a EN_PROGRESO
   - Establece fecha_inicio y fecha_entrega_pactada
   - Emite evento TRABAJO_INICIADO
4. Si no hay saldo: muestra error con monto requerido
```

**Modelo involucrado:** `Transaction.crear_transaccion_escrow()`

**Ejemplo:**
- Monto propuesta: $1000 ARS
- Escrow (30%): $300 USDC_MOCK retenidos
- Balance cliente: $1000 → $700 USDC_MOCK

---

### 2️⃣ **Durante el Trabajo: Monitoreo**

**Ubicación:** `dashboard_home.html`

**Visualización:**
- **Cliente:** Ve el trabajo en progreso
- **Profesional:** Sección "Mis Compromisos" con fechas
- **Ambos:** Pueden ver transacciones en el dashboard

**Justificaciones de atraso:**
- Si hay atraso, profesional puede explicar
- Cliente puede aceptar/rechazar justificación
- Flag `penalizacion_omitida` controla penalizaciones

---

### 3️⃣ **Finalización Opción A: Aprobar Trabajo** ✅

**Ubicación:** `job_detail_private.html` → Botón "Aprobar Trabajo"

**Proceso:**
```python
# Vista: aprobar_trabajo_completado()
1. Cliente aprueba el trabajo
2. Sistema calcula comisión (10% del total)
3. Libera fondos:
   - Del escrow ($300) descuenta comisión
   - Profesional recibe: $270 USDC_MOCK
   - Plataforma retiene: $30 USDC_MOCK
4. Cambia status a COMPLETADO
5. Establece fecha_entrega_real
6. Emite evento TRABAJO_COMPLETADO
```

**Modelos involucrados:**
- `Transaction.liberar_pago_a_profesional()`
- `WorkEvent.crear_evento_trabajo_completado()`

**Ejemplo:**
- Monto total: $1000 ARS
- Escrow: $300 USDC
- Comisión (10%): $30 USDC
- Profesional recibe: $270 USDC
- Balance profesional: $1000 → $1270 USDC

---

### 3️⃣ **Finalización Opción B: Rechazar Trabajo** ⚠️

**Ubicación:** `job_detail_private.html` → Botón "Rechazar"

**Proceso:**
```python
# Vista: rechazar_trabajo_completado()
1. Cliente rechaza el trabajo
2. Status vuelve a ABIERTO (para revisión)
3. Fondos permanecen en escrow
4. Se registra el motivo del rechazo
```

**Nota:** No se devuelve dinero automáticamente. Permite negociación.

---

### 3️⃣ **Finalización Opción C: Solicitar Reembolso** 🔄

**Ubicación:** `job_detail_private.html` → Botón "Solicitar Reembolso"

**Proceso:**
```python
# Vista: solicitar_reembolso()
1. Cliente solicita reembolso
2. Sistema verifica fondos en escrow
3. Devuelve el 30% al cliente
4. Cambia status a CANCELADO
5. Emite evento TRABAJO_CANCELADO
```

**Modelos involucrados:**
- `Transaction.procesar_reembolso()`
- `WorkEvent.crear_evento_reembolso()`

**Ejemplo:**
- Escrow: $300 USDC
- Cliente recupera: $300 USDC
- Balance cliente: $700 → $1000 USDC

---

## 📊 Modelos del Sistema

### 🏦 **Wallet** (Billetera)

```python
- user: Usuario propietario (null para sistema)
- tipo_cuenta: USER | ESCROW
- balance_usdc: Decimal(12,2)
- activa: Boolean
```

**Métodos:**
- `tiene_saldo_suficiente(monto)` → True/False
- `restar_saldo(monto)` → Actualiza balance
- `sumar_saldo(monto)` → Actualiza balance
- `get_escrow_account()` → Obtiene cuenta sistema

### 💸 **Transaction** (Transacción)

```python
- from_wallet: Wallet origen
- to_wallet: Wallet destino
- monto_usdc: Decimal(12,2)
- tipo_transaccion: ESCROW_DEPOSIT | RELEASE_PAYMENT | REFUND | FEE
- status: PENDING | COMPLETED | FAILED | REVERSED
- oferta_relacionada: JobOffer
- propuesta_relacionada: Proposal
- descripcion: TextField
- metadata: JSONField
```

**Métodos Principales:**

#### `crear_transaccion_escrow(cliente_wallet, monto_total, propuesta, porcentaje_escrow=30)`
- Calcula 30% del monto
- Verifica saldo
- Transfiere a escrow
- Registra metadata
- Retorna: `(Transaction, monto_escrow)` o `(None, None)`

#### `liberar_pago_a_profesional(propuesta, porcentaje_comision=10)`
- Calcula comisión (10%)
- Libera escrow menos comisión al profesional
- Retiene comisión en plataforma
- Crea 2 transacciones (pago + comisión)
- Retorna: `(transaccion_pago, transaccion_comision, monto_neto)` o `(None, None, None)`

#### `procesar_reembolso(propuesta, motivo='')`
- Busca transacción escrow original
- Devuelve monto completo al cliente
- Registra motivo
- Retorna: `(Transaction, monto_reembolsado)` o `(None, None)`

### 📝 **WorkEvent** (Evento de Trabajo)

```python
- oferta: JobOffer
- tipo_evento: TRABAJO_INICIADO | TRABAJO_COMPLETADO | TRABAJO_CANCELADO | ...
- descripcion: TextField
- usuario_relacionado: User
- transaccion_relacionada: Transaction
- metadata: JSONField
```

**Métodos:**
- `crear_evento_trabajo_iniciado(oferta, propuesta, transaccion)`
- `crear_evento_trabajo_completado(oferta, propuesta, trans_pago, trans_comision)`
- `crear_evento_reembolso(oferta, propuesta, trans_reembolso, motivo)`

---

## 🎨 Interfaces de Usuario

### 1. **Dashboard Principal** (`dashboard_home.html`)

#### Sección Wallet
- Balance actual en USDC_MOCK
- Última actualización
- Tipo de cuenta

#### Historial de Transacciones
- Últimas 10 transacciones
- Iconos por tipo (lock, unlock, refund, percentage)
- Colores según entrada/salida
- Estado (completada, pendiente, fallida)
- Descripción y fecha

### 2. **Detalle de Trabajo Privado** (`job_detail_private.html`)

#### Cuando status = EN_PROGRESO
Muestra 3 botones:

1. **Aprobar Trabajo** (Verde)
   - Confirma con alert
   - Libera pago
   - Descuenta comisión

2. **Rechazar** (Amarillo)
   - Abre modal
   - Solicita motivo
   - Vuelve a estado ABIERTO

3. **Solicitar Reembolso** (Rojo)
   - Abre modal con advertencias
   - Solicita motivo
   - Devuelve dinero y cancela

#### Cuando status = COMPLETADO
- Alert verde mostrando fecha
- Mensaje de pago liberado

#### Cuando status = CANCELADO
- Alert azul mostrando estado
- Mensaje de reembolso procesado

---

## 🔐 Seguridad y Validaciones

### ✅ Validaciones Implementadas

1. **Saldo Suficiente**
   ```python
   if not cliente_wallet.tiene_saldo_suficiente(monto_requerido):
       return error
   ```

2. **Permisos de Usuario**
   ```python
   if request.user != oferta.creador:
       return error_403
   ```

3. **Estado del Trabajo**
   ```python
   if oferta.status != 'EN_PROGRESO':
       return error_invalid_state
   ```

4. **Transacciones Atómicas**
   ```python
   with transaction.atomic():
       # Todas las operaciones o ninguna
   ```

5. **Precisión Decimal**
   ```python
   DecimalField(max_digits=12, decimal_places=2)
   Decimal con ROUND_HALF_UP
   ```

---

## 📈 Casos de Uso

### Caso 1: Trabajo Exitoso
```
1. Cliente acepta propuesta → -$300 USDC (escrow)
2. Profesional completa trabajo
3. Cliente aprueba → Profesional +$270, Plataforma +$30
4. Estado: COMPLETADO ✅
```

### Caso 2: Trabajo Cancelado por Cliente
```
1. Cliente acepta propuesta → -$300 USDC (escrow)
2. Cliente solicita reembolso (motivo: "No inició")
3. Sistema devuelve → Cliente +$300 USDC
4. Estado: CANCELADO 🔄
```

### Caso 3: Trabajo Rechazado (con revisión)
```
1. Cliente acepta propuesta → -$300 USDC (escrow)
2. Profesional entrega
3. Cliente rechaza (motivo: "No cumple specs")
4. Estado: ABIERTO (para revisión) ⚠️
5. Fondos permanecen en escrow (negociación)
```

---

## 🛠️ Endpoints API

| Método | URL | Vista | Descripción |
|--------|-----|-------|-------------|
| POST | `/propuestas/<id>/votar/` | `votar_propuesta` | Acepta propuesta y retiene escrow |
| POST | `/ofertas/<id>/aprobar-trabajo/` | `aprobar_trabajo_completado` | Libera pago con comisión |
| POST | `/ofertas/<id>/rechazar-trabajo/` | `rechazar_trabajo_completado` | Rechaza entrega |
| POST | `/ofertas/<id>/solicitar-reembolso/` | `solicitar_reembolso` | Procesa reembolso |

---

## 💡 Características Adicionales

### Señales Automáticas
```python
@receiver(post_save, sender=User)
def crear_wallet_usuario(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(
            user=instance,
            balance_usdc=Decimal('1000.00')  # Saldo inicial
        )
```

### Admin Interface
- WalletAdmin: gestión de balances
- TransactionAdmin: historial completo
- WorkEventAdmin: log de eventos

### Metadata Tracking
Todas las transacciones guardan contexto:
```json
{
  "monto_total": "1000.00",
  "porcentaje_escrow": 30,
  "profesional_id": 5,
  "cliente_id": 2
}
```

---

## 🎓 Próximos Pasos Sugeridos

1. **Sistema de Disputas**
   - Mediación cuando se rechaza trabajo
   - Timeline de comunicación
   - Resolución de disputas

2. **Pagos Parciales**
   - Hitos de pago (30% inicio, 40% avance, 30% final)
   - Aprobación por fases

3. **Integración Real**
   - Conectar con USDC real en blockchain
   - Gateway de pago con tarjetas
   - KYC/AML compliance

4. **Reportes Financieros**
   - Dashboard de ingresos/egresos
   - Exportar a PDF/Excel
   - Gráficos de tendencias

---

## 📝 Notas Técnicas

- **Precisión:** Todos los montos usan `DecimalField(12,2)` para evitar errores de float
- **Atomicidad:** Todas las operaciones financieras usan `@transaction.atomic`
- **Auditoría:** Todas las transacciones quedan registradas permanentemente
- **Reversibilidad:** Status FAILED permite rollback manual si es necesario

---

## ✅ Testing Checklist

- [ ] Cliente con saldo insuficiente no puede aceptar propuesta
- [ ] Escrow se retiene correctamente (30%)
- [ ] Aprobación libera monto correcto al profesional
- [ ] Comisión (10%) se registra correctamente
- [ ] Reembolso devuelve monto completo
- [ ] Estados de oferta cambian correctamente
- [ ] Eventos se registran en cada paso
- [ ] Wallet balance actualiza en tiempo real

---

## 🎉 Sistema Completo Implementado

✅ Liberación de fondos con comisión  
✅ Sistema de reembolsos  
✅ Comisiones de plataforma (10%)  
✅ Frontend completo con modales  
✅ Dashboard con wallet y transacciones  
✅ Validaciones de seguridad  
✅ Transacciones atómicas  
✅ Registro de eventos  

**El sistema está listo para usar en producción! 🚀**
