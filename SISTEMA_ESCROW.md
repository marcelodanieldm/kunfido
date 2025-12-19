# Sistema de Cobro Blindado (Escrow) - Documentación

## 📋 Resumen

Sistema de garantía que protege tanto a clientes como a profesionales en transacciones de trabajo. El dinero se mantiene en custodia (escrow) hasta que se cumplan las condiciones acordadas.

## 🔄 Flujo de Trabajo

### 1. Aceptación de Propuesta
**¿Qué sucede?**
- El cliente acepta una propuesta de un profesional
- Se verifica que el cliente tenga saldo suficiente (30% del monto total)
- Se bloquean $X USDC (30%) en la cuenta de escrow
- El trabajo cambia a estado `IN_PROGRESS`

**Verificaciones:**
```python
# Vista: accept_bid()
- Usuario debe ser dueño de la oferta
- Oferta debe estar en estado OPEN
- Cliente debe tener ≥ 30% del monto en su wallet
```

**Si falta saldo:**
- Se muestra mensaje de error
- Se redirige a la página de wallet para cargar fondos
- No se acepta la propuesta

**Modelo de datos:**
```python
EscrowTransaction:
    transaction_type: 'INITIAL_DEPOSIT'
    amount_usdc: monto_total * 0.30
    status: 'LOCKED'
    from_wallet: cliente_wallet
    to_wallet: escrow_wallet
```

---

### 2. Confirmación de Inicio de Obra
**¿Qué sucede?**
- El cliente confirma que la obra ha comenzado
- Se **libera el 30%** bloqueado al profesional
- Se **bloquea el 70% restante** del cliente en escrow

**Botón disponible:**
- Solo para el DUEÑO (cliente)
- Solo si no se ha confirmado el inicio previamente
- En la página de detalle del trabajo (`job_detail.html`)

**Transacciones creadas:**

1. **Release del 30% inicial:**
```python
EscrowTransaction:
    transaction_type: 'INITIAL_RELEASE'
    amount_usdc: monto_total * 0.30
    status: 'RELEASED'
    from_wallet: escrow_wallet
    to_wallet: profesional_wallet
    released_at: timezone.now()
```

2. **Lock del 70% restante:**
```python
EscrowTransaction:
    transaction_type: 'REMAINING_DEPOSIT'
    amount_usdc: monto_total * 0.70
    status: 'LOCKED'
    from_wallet: cliente_wallet
    to_wallet: escrow_wallet
```

**Vista:** `confirm_work_start(request, job_id)`
**URL:** `POST /jobs/<job_id>/confirm-start/`

---

### 3. Finalización de Obra
**¿Qué sucede?**
- El cliente confirma que la obra está finalizada
- Se **libera el 70%** bloqueado menos **5% de comisión**
- El profesional recibe el **65%** (70% - 5%)
- La plataforma retiene el **5%** como comisión
- El trabajo cambia a estado `CLOSED`

**Botón disponible:**
- Solo para el DUEÑO (cliente)
- Solo después de confirmar el inicio
- Solo si no se ha finalizado previamente

**Cálculos:**
```
Monto total:        100%  = $100 USDC
Ya liberado (30%):   30%  = $30 USDC
Bloqueado (70%):     70%  = $70 USDC

Al finalizar:
- Profesional recibe: 65% = $65 USDC (70% - 5%)
- Comisión plataforma: 5% = $5 USDC
```

**Transacciones creadas:**

1. **Release final al profesional:**
```python
EscrowTransaction:
    transaction_type: 'FINAL_RELEASE'
    amount_usdc: (monto_total * 0.70) - comision
    status: 'RELEASED'
    from_wallet: escrow_wallet
    to_wallet: profesional_wallet
    metadata: {'percentage': '65', 'fee_deducted': str(comision)}
```

2. **Comisión de plataforma:**
```python
EscrowTransaction:
    transaction_type: 'PLATFORM_FEE'
    amount_usdc: monto_total * 0.05
    status: 'RELEASED'
    from_wallet: escrow_wallet
    to_wallet: escrow_wallet  # Se queda en la plataforma
```

**Vista:** `complete_work(request, job_id)`
**URL:** `POST /jobs/<job_id>/complete/`

---

## 💰 Distribución de Pagos

### Ejemplo con $1000 USDC:

| Etapa | Acción | Cliente Paga | Profesional Recibe | Escrow | Plataforma |
|-------|--------|--------------|-------------------|---------|------------|
| 1. Aceptar propuesta | Bloquea 30% | -$300 | $0 | +$300 | $0 |
| 2. Inicio de obra | Libera 30% + bloquea 70% | -$700 | +$300 | +$400 | $0 |
| 3. Fin de obra | Libera 70% - 5% | $0 | +$650 | -$700 | +$50 |
| **TOTAL** | | **-$1000** | **+$950** | **$0** | **+$50** |

**Resumen:**
- Cliente pagó: **$1000 USDC** (100%)
- Profesional recibió: **$950 USDC** (95%)
- Plataforma cobró: **$50 USDC** (5%)

---

## 🔐 Modelo EscrowTransaction

### Campos principales:

```python
class EscrowTransaction(models.Model):
    # Relaciones
    job = ForeignKey(JobOffer)
    bid = ForeignKey(Bid)
    
    # Montos y tipo
    amount_usdc = DecimalField(max_digits=12, decimal_places=2)
    transaction_type = CharField(choices=TRANSACTION_TYPE_CHOICES)
    
    # Estado
    status = CharField(choices=STATUS_CHOICES)  # LOCKED, RELEASED, REFUNDED
    
    # Wallets involucradas
    from_wallet = ForeignKey(Wallet, related_name='escrow_debits')
    to_wallet = ForeignKey(Wallet, related_name='escrow_credits')
    
    # Metadata
    description = TextField()
    metadata = JSONField()
    
    # Fechas
    created_at = DateTimeField(auto_now_add=True)
    released_at = DateTimeField(null=True, blank=True)
```

### Estados (status):
- **LOCKED**: Dinero bloqueado en escrow, esperando liberación
- **RELEASED**: Dinero liberado y transferido al destinatario
- **REFUNDED**: Dinero devuelto al cliente (en caso de cancelación)

### Tipos de transacción (transaction_type):
- **INITIAL_DEPOSIT**: Depósito inicial del 30%
- **REMAINING_DEPOSIT**: Depósito restante del 70%
- **INITIAL_RELEASE**: Liberación inicial del 30% al profesional
- **FINAL_RELEASE**: Liberación final del 65% al profesional (70% - 5%)
- **PLATFORM_FEE**: Comisión del 5% para la plataforma
- **REFUND**: Reembolso al cliente

---

## 🎯 Métodos de Clase

### 1. `lock_initial_deposit(job, bid, client_wallet)`
Bloquea el 30% cuando se acepta una propuesta.

**Returns:** `(EscrowTransaction, success: bool, error_msg: str)`

**Ejemplo:**
```python
transaction, success, error = EscrowTransaction.lock_initial_deposit(
    job=job_offer,
    bid=winning_bid,
    client_wallet=cliente.wallet
)

if success:
    print(f"✓ Bloqueados ${transaction.amount_usdc} USDC")
else:
    print(f"✗ Error: {error}")
```

---

### 2. `release_initial_payment(job, bid)`
Libera el 30% inicial al profesional.

**Returns:** `(EscrowTransaction, success: bool, error_msg: str)`

---

### 3. `lock_remaining_amount(job, bid, client_wallet)`
Bloquea el 70% restante cuando se confirma el inicio.

**Returns:** `(EscrowTransaction, success: bool, error_msg: str)`

---

### 4. `release_final_payment(job, bid)`
Libera el 70% menos la comisión del 5%.

**Returns:** `(release_tx, fee_tx, success: bool, error_msg: str)`

**Ejemplo:**
```python
release_tx, fee_tx, success, error = EscrowTransaction.release_final_payment(
    job=job_offer,
    bid=winning_bid
)

if success:
    print(f"✓ Profesional recibió: ${release_tx.amount_usdc} USDC")
    print(f"✓ Comisión plataforma: ${fee_tx.amount_usdc} USDC")
```

---

### 5. `refund_to_client(job, bid, reason='')`
Reembolsa fondos bloqueados al cliente (cancelación).

**Returns:** `(refund_transactions: list, success: bool, error_msg: str)`

---

## 🛡️ Seguridad y Validaciones

### En accept_bid():
1. ✅ Verificar que el usuario sea el dueño de la oferta
2. ✅ Verificar que la oferta esté en estado `OPEN`
3. ✅ Verificar saldo suficiente en wallet del cliente
4. ✅ Transacción atómica (rollback si falla)

### En confirm_work_start():
1. ✅ Solo el dueño puede confirmar
2. ✅ Trabajo debe estar en `IN_PROGRESS`
3. ✅ No se puede confirmar dos veces
4. ✅ Cliente debe tener saldo para el 70%

### En complete_work():
1. ✅ Solo el dueño puede finalizar
2. ✅ Debe haberse confirmado el inicio primero
3. ✅ No se puede finalizar dos veces
4. ✅ Cambia el trabajo a `CLOSED`

---

## 📊 Consultas Útiles

### Ver transacciones de un trabajo:
```python
escrow_txs = EscrowTransaction.objects.filter(job=job_offer)
for tx in escrow_txs:
    print(f"{tx.get_transaction_type_display()}: ${tx.amount_usdc} - {tx.status}")
```

### Verificar si se liberó el 30%:
```python
initial_released = EscrowTransaction.objects.filter(
    job=job_offer,
    transaction_type='INITIAL_RELEASE',
    status='RELEASED'
).exists()
```

### Calcular comisiones totales de la plataforma:
```python
from django.db.models import Sum
total_fees = EscrowTransaction.objects.filter(
    transaction_type='PLATFORM_FEE',
    status='RELEASED'
).aggregate(Sum('amount_usdc'))['amount_usdc__sum']
```

---

## 🖥️ Frontend (Templates)

### Botón "Confirmar Inicio de Obra":
```django
{% if is_owner and not job.escrow_transactions.filter(transaction_type='INITIAL_RELEASE', status='RELEASED').exists %}
<form method="post" action="{% url 'confirm_work_start' job.id %}">
    {% csrf_token %}
    <button type="submit" class="btn btn-success">
        Confirmar Inicio de Obra (Libera 30%)
    </button>
</form>
{% endif %}
```

### Botón "Finalizar Obra":
```django
{% if is_owner and not job.escrow_transactions.filter(transaction_type='FINAL_RELEASE', status='RELEASED').exists %}
<form method="post" action="{% url 'complete_work' job.id %}">
    {% csrf_token %}
    <button type="submit" class="btn btn-primary">
        Finalizar Obra (Libera 70% - 5% comisión)
    </button>
</form>
{% endif %}
```

---

## 🔗 URLs Configuradas

```python
# jobs/urls.py
urlpatterns = [
    path('bid/<int:bid_id>/accept/', views.accept_bid, name='accept_bid'),
    path('<int:job_id>/confirm-start/', views.confirm_work_start, name='confirm_work_start'),
    path('<int:job_id>/complete/', views.complete_work, name='complete_work'),
]
```

---

## 📝 Admin

El modelo `EscrowTransaction` está registrado en el admin con permisos de **solo lectura**:
- ❌ No se puede crear manualmente
- ❌ No se puede editar
- ❌ No se puede eliminar
- ✅ Solo se puede visualizar

Esto garantiza que todas las transacciones se creen únicamente a través de las vistas validadas.

---

## 🧪 Pruebas

### Script de demostración:
```bash
python manage.py shell < demo_escrow.py
```

### Flujo de prueba manual:
1. **Login como cliente** (`cliente@kunfido.com` / `cliente123`)
2. **Ver trabajo en progreso:** `/jobs/1/`
3. **Confirmar inicio:** Click en "Confirmar Inicio de Obra"
4. **Verificar wallet del profesional:** Debe tener +30%
5. **Finalizar obra:** Click en "Finalizar Obra"
6. **Verificar:**
   - Wallet profesional: +65% adicional (total 95%)
   - Wallet escrow (plataforma): +5%
   - Estado del trabajo: `CLOSED`

---

## 🚨 Casos de Error

### Error: "Saldo insuficiente"
**Causa:** Cliente no tiene suficiente USDC para bloquear el 30%
**Solución:** Cargar fondos en `/wallet/` antes de aceptar propuesta

### Error: "No se encontró depósito inicial bloqueado"
**Causa:** Se intentó confirmar inicio sin haber aceptado propuesta
**Solución:** Primero aceptar propuesta, luego confirmar inicio

### Error: "No se encontró depósito restante bloqueado"
**Causa:** Se intentó finalizar sin haber confirmado inicio
**Solución:** Primero confirmar inicio, luego finalizar

---

## ✅ Estado de Implementación

- [x] Modelo `EscrowTransaction` creado
- [x] Método `lock_initial_deposit()` - Bloquea 30%
- [x] Método `release_initial_payment()` - Libera 30%
- [x] Método `lock_remaining_amount()` - Bloquea 70%
- [x] Método `release_final_payment()` - Libera 70% - 5%
- [x] Método `refund_to_client()` - Reembolsa fondos
- [x] Vista `accept_bid()` - Integrada con escrow
- [x] Vista `confirm_work_start()` - Confirma inicio
- [x] Vista `complete_work()` - Finaliza obra
- [x] URLs configuradas
- [x] Templates actualizados con botones
- [x] Admin registrado (solo lectura)
- [x] Migraciones aplicadas
- [x] Script de demostración

---

## 📞 Soporte

Para dudas o problemas con el sistema de escrow, revisar:
1. Logs del servidor Django
2. Transacciones en admin: `/admin/jobs/escrowtransaction/`
3. Wallets en admin: `/admin/usuarios/wallet/`
4. Script de demostración: `demo_escrow.py`
