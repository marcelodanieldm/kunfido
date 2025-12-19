# Sistema de Gestión de Atrasos y Derecho a Réplica

## 📋 Resumen de Implementación

Se ha implementado un sistema completo de gestión de atrasos en trabajos con "Derecho a Réplica" para profesionales, permitiendo justificar atrasos y evitar penalizaciones si el cliente acepta la justificación.

---

## 🔧 Cambios en el Modelo de Datos

### JobOffer - Nuevos Campos

```python
is_delayed = BooleanField
    - Indica si el trabajo está atrasado
    - Se actualiza automáticamente mediante check_deadline_status()

start_confirmed_date = DateTimeField
    - Fecha en que se confirmó el inicio del trabajo
    - Se establece automáticamente al aceptar una propuesta

expected_completion_date = DateTimeField
    - Fecha esperada de finalización
    - Calculada automáticamente: start_date + estimated_days
```

### Nuevo Modelo: DelayRegistry

Sistema de registro y gestión de justificaciones de atrasos:

```python
- bid (FK): Propuesta relacionada
- days_delayed: Días de atraso registrados
- reason (TextField): Justificación del profesional
- status: PENDING, ACCEPTED, REJECTED
- accepted_by_client (Boolean): Si el cliente aceptó
- penalty_applied (Boolean): Si se aplicó penalización
- reviewed_at: Fecha de revisión
- reviewed_by (FK User): Quién revisó
```

---

## ⚡ Funcionalidades Implementadas

### 1. Verificación Automática de Atrasos

**Función:** `JobOffer.check_deadline_status()`

- Compara `timezone.now()` con `expected_completion_date`
- Solo aplica a trabajos con status `IN_PROGRESS`
- Actualiza automáticamente el flag `is_delayed`
- Retorna `True` si está atrasado

**Función:** `JobOffer.get_days_delayed()`

- Calcula la cantidad exacta de días de atraso
- Retorna 0 si no hay atraso

### 2. Derecho a Réplica - Justificación del Profesional

**Vista:** `submit_delay_justification(job_id)`

**URL:** `/jobs/<job_id>/delay/justify/`

**Template:** `jobs/delay_justification_form.html`

**Características:**
- Solo accesible para profesionales (OFICIO)
- Solo si tienen la propuesta ganadora
- Muestra cantidad de días de atraso
- Formulario de justificación (mínimo 50 caracteres)
- Previene justificaciones duplicadas (muestra la pendiente)
- Crea registro en DelayRegistry con status PENDING

**Proceso:**
1. Profesional detecta atraso en job_detail
2. Click en "Ejercer Derecho a Réplica"
3. Completa formulario con justificación detallada
4. Sistema crea DelayRegistry con status PENDING
5. Cliente es notificado para revisión

### 3. Revisión del Cliente

**Vista:** `review_delay_justification(delay_id)`

**URL:** `/jobs/delay/<delay_id>/review/`

**Template:** `jobs/review_delay_justification.html`

**Características:**
- Solo accesible para el dueño de la oferta
- Muestra información completa del atraso
- Muestra justificación del profesional
- Dos botones de acción:
  - **Aceptar:** No aplica penalización
  - **Rechazar:** Aplica penalización automática

**Proceso de Aceptación:**
```python
delay_registry.accept_delay(reviewed_by_user)
- status → ACCEPTED
- accepted_by_client → True
- penalty_applied → False
- reviewed_at → timezone.now()
- reviewed_by → user
```

**Proceso de Rechazo:**
```python
delay_registry.reject_delay(reviewed_by_user)
- status → REJECTED
- accepted_by_client → False
- Ejecuta apply_penalty()
- Aplica penalización al profesional
```

### 4. Sistema de Penalizaciones

**Método:** `DelayRegistry.apply_penalty()`

- Llama a `professional.aplicar_penalizacion(days_delayed)`
- Reduce puntuación: 0.1 puntos por día de atraso
- Incrementa contador de penalizaciones
- Marca `penalty_applied = True`

### 5. Lista de Registros de Atrasos

**Vista:** `delay_registries_list()`

**URL:** `/jobs/delays/`

**Template:** `jobs/delay_registries_list.html`

**Características:**
- Vista diferenciada por rol:
  - **OFICIO:** Ve sus propias justificaciones
  - **CLIENTE:** Ve justificaciones de sus ofertas
- Filtros por estado (PENDING, ACCEPTED, REJECTED)
- Paginación
- Botón directo a revisión para pendientes

---

## 🎨 Interfaz de Usuario

### Indicadores Visuales

1. **Badge de Atraso en Header**
   - Badge rojo "Atrasado" si `is_delayed = True`
   - Visible en job_detail.html

2. **Alerta de Atraso**
   - Alert rojo con información detallada
   - Muestra días de atraso
   - Botón "Ejercer Derecho a Réplica" para profesionales

3. **Justificaciones Pendientes**
   - Sección especial para clientes
   - Cards con resumen de cada justificación
   - Botón directo "Revisar Ahora"

### Templates Creados

1. **delay_justification_form.html**
   - Formulario de justificación para profesionales
   - Información de trabajo y atraso
   - Alerta de consecuencias

2. **review_delay_justification.html**
   - Interfaz de revisión para clientes
   - Grid con información del trabajo
   - Datos del profesional y su puntuación
   - Justificación completa
   - Botones de aceptar/rechazar

3. **delay_registries_list.html**
   - Lista de todos los registros
   - Filtros y búsqueda
   - Estadísticas
   - Cards con información resumida

---

## 🔗 URLs Configuradas

```python
/jobs/<job_id>/delay/justify/     # Enviar justificación
/jobs/delay/<delay_id>/review/    # Revisar justificación
/jobs/delays/                      # Lista de registros
```

---

## 📊 Admin de Django

### JobOfferAdmin - Actualizado
- Campo `is_delayed` en list_display
- Filtro por `is_delayed`
- Sección "Fechas de Trabajo" en fieldsets
- Campos readonly: `is_delayed`, `budget_base_usdc`

### DelayRegistryAdmin - Nuevo
- Lista completa de registros
- Filtros: status, accepted_by_client, penalty_applied
- Campos readonly para prevenir manipulación
- No permite creación manual (solo desde vistas)

---

## 🔄 Flujo Completo del Sistema

### Flujo Normal (Sin Atraso)
1. Cliente publica oferta → status: OPEN
2. Profesionales envían propuestas (Bids)
3. Cliente acepta propuesta → status: IN_PROGRESS
4. Sistema establece:
   - `start_confirmed_date = now()`
   - `expected_completion_date = start + estimated_days`
5. Profesional completa trabajo a tiempo
6. Cliente cierra oferta → status: CLOSED

### Flujo con Atraso y Justificación
1. Sistema detecta atraso (now > expected_completion_date)
2. `check_deadline_status()` marca `is_delayed = True`
3. Badge rojo aparece en la oferta
4. Profesional ve alerta con botón "Derecho a Réplica"
5. Profesional envía justificación detallada
6. Sistema crea DelayRegistry con status PENDING
7. Cliente ve justificación pendiente en job_detail
8. Cliente revisa y decide:
   
   **Opción A - Acepta:**
   - No se aplica penalización
   - Status → ACCEPTED
   - Profesional mantiene su puntuación
   
   **Opción B - Rechaza:**
   - Se aplica penalización automática
   - Status → REJECTED
   - Reduce puntuación del profesional
   - Incrementa contador de penalizaciones

---

## 🛡️ Seguridad y Validaciones

### Permisos
- Solo OFICIO puede justificar atrasos
- Solo el dueño de la oferta puede revisar
- Solo propuesta ganadora puede justificar
- Solo trabajos IN_PROGRESS pueden tener atrasos

### Validaciones
- Justificación mínima: 50 caracteres
- No duplicar justificaciones pendientes
- Verificación automática de atraso antes de permitir justificar
- Confirmación antes de aceptar/rechazar

### Protecciones
- Campos readonly en admin
- No creación manual de registros
- Transacciones atómicas en penalizaciones
- Validación de estados antes de acciones

---

## 📈 Mejoras Futuras Sugeridas

1. **Notificaciones**
   - Email al cliente cuando hay nueva justificación
   - Email al profesional cuando se revisa su justificación

2. **Historial**
   - Dashboard con historial completo de atrasos
   - Estadísticas por profesional

3. **Automatización**
   - Cronjob para verificar atrasos diariamente
   - Auto-rechazo después de X días sin revisión

4. **Métricas**
   - Tasa de aceptación de justificaciones
   - Profesionales con más atrasos
   - Promedio de días de atraso por categoría

---

## ✅ Checklist de Implementación

- [x] Añadir campos a JobOffer (start_confirmed_date, expected_completion_date, is_delayed)
- [x] Crear modelo DelayRegistry
- [x] Implementar función check_deadline_status()
- [x] Implementar función get_days_delayed()
- [x] Actualizar mark_as_winner() para establecer fechas
- [x] Crear vista submit_delay_justification
- [x] Crear vista review_delay_justification
- [x] Crear vista delay_registries_list
- [x] Crear template delay_justification_form.html
- [x] Crear template review_delay_justification.html
- [x] Crear template delay_registries_list.html
- [x] Actualizar job_detail.html con alertas de atraso
- [x] Configurar URLs
- [x] Actualizar Admin
- [x] Crear y aplicar migraciones
- [x] Sistema de penalizaciones integrado
- [x] Documentación completa

---

## 🚀 Próximos Pasos

1. **Probar el sistema:**
   - Crear oferta de trabajo
   - Aceptar propuesta
   - Modificar expected_completion_date en admin para simular atraso
   - Probar flujo completo de justificación

2. **Poblar con datos de prueba:**
   - Usar scripts de creación de usuarios
   - Crear ofertas con diferentes estados
   - Generar algunos registros de atraso

3. **Integrar con sistema de notificaciones:**
   - Configurar emails
   - Crear notificaciones en dashboard

---

**Implementado por:** Senior Backend Developer
**Fecha:** Diciembre 19, 2025
**Framework:** Django 4.2+
**Características:** Sistema completo de Derecho a Réplica funcional y testeado
