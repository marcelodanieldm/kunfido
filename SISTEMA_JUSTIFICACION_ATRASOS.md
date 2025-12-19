# Sistema de Justificación de Atrasos - Kunfido

## ✅ Estado: COMPLETAMENTE IMPLEMENTADO

Se ha implementado un sistema completo para gestionar atrasos en entregas y sus justificaciones.

---

## 📋 Cambios en el Modelo JobOffer

### Nuevos Campos Añadidos:

```python
fecha_inicio = DateTimeField(null=True, blank=True)
# Fecha en que se inició el trabajo

fecha_entrega_pactada = DateTimeField(null=True, blank=True)
# Fecha comprometida para entregar el trabajo

fecha_entrega_real = DateTimeField(null=True, blank=True)
# Fecha en que se entregó el trabajo
```

### Property `dias_atraso` Implementado:

**Ubicación:** [usuarios/models.py](usuarios/models.py#L155-L177)

```python
@property
def dias_atraso(self):
    """
    Calcula los días de atraso del trabajo.
    
    Retorna:
    - None: si no hay fecha de entrega pactada
    - 0: si se entregó a tiempo o antes
    - >0: cantidad de días de atraso
    """
```

**Lógica implementada:**
1. Si no hay `fecha_entrega_pactada` → retorna `None`
2. Si el trabajo está `FINALIZADA` → compara `fecha_entrega_real` vs `fecha_entrega_pactada`
3. Si el trabajo está en progreso → compara fecha actual vs `fecha_entrega_pactada`
4. Retorna 0 si se entregó a tiempo, o los días de atraso si es positivo

**Ejemplos de uso:**
```python
oferta = JobOffer.objects.get(id=1)

# Caso 1: Sin fecha pactada
oferta.dias_atraso  # None

# Caso 2: Entregado a tiempo
oferta.fecha_entrega_pactada = datetime(2025, 12, 20)
oferta.fecha_entrega_real = datetime(2025, 12, 18)
oferta.dias_atraso  # 0 (entregó 2 días antes)

# Caso 3: Con atraso
oferta.fecha_entrega_pactada = datetime(2025, 12, 15)
oferta.fecha_entrega_real = datetime(2025, 12, 20)
oferta.dias_atraso  # 5 (entregó 5 días tarde)

# Caso 4: En progreso con atraso
# Si hoy es 20/12/2025 y la entrega era el 15/12/2025
oferta.dias_atraso  # 5 (lleva 5 días de atraso)
```

---

## 🆕 Nuevo Modelo: DelayJustification

**Ubicación:** [usuarios/models.py](usuarios/models.py#L232-L312)

### Campos Implementados:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `oferta` | ForeignKey(JobOffer) | Oferta de trabajo relacionada |
| `profesional` | ForeignKey(User) | Profesional que envía la justificación |
| `replica` | TextField | Explicación del profesional sobre el atraso |
| `dias_atraso_justificados` | PositiveIntegerField | Cantidad de días que se justifican |
| **`penalizacion_omitida`** | **BooleanField** | **Flag que indica si el cliente aceptó la réplica** |
| `fecha_aceptacion` | DateTimeField | Cuándo fue aceptada |
| `aceptada_por` | ForeignKey(User) | Cliente que aceptó |
| `fecha_creacion` | DateTimeField | Auto-generado |
| `fecha_actualizacion` | DateTimeField | Auto-actualizado |

### Constraint Único:
```python
unique_together = ['oferta', 'profesional']
```
Un profesional solo puede tener una justificación por oferta (puede actualizarla).

### Método Especial:

```python
def aceptar_justificacion(self, aceptado_por):
    """
    Marca la justificación como aceptada y omite la penalización.
    """
    self.penalizacion_omitida = True
    self.fecha_aceptacion = timezone.now()
    self.aceptada_por = aceptado_por
    self.save()
```

---

## 🌐 Vistas Implementadas

### 1. **crear_justificacion_atraso** - Crear/Actualizar Justificación

**Ruta:** `/ofertas/<oferta_id>/justificar-atraso/`  
**Archivo:** [usuarios/views.py](usuarios/views.py#L287-L341)  
**Acceso:** Login required, solo OFICIO

**Funcionalidad:**
- Calcula automáticamente los días de atraso con `oferta.dias_atraso`
- Detecta si ya existe una justificación (permite actualizar)
- Guarda la réplica del profesional
- Registra los días de atraso justificados
- Renderiza formulario con template personalizado

**Validaciones:**
- Solo usuarios con rol OFICIO pueden acceder
- Verifica que exista atraso real (dias_atraso > 0)
- Requiere texto en la réplica

**Flujo:**
```
Profesional OFICIO → Ver oferta con atraso → 
Botón "Justificar Atraso" → Formulario → 
Enviar réplica → DelayJustification creada
```

---

### 2. **aceptar_replica_atraso** - Aceptar Justificación ⭐

**Ruta:** `/justificaciones/<justificacion_id>/aceptar/`  
**Archivo:** [usuarios/views.py](usuarios/views.py#L344-L368)  
**Acceso:** Login required, POST only, solo dueño de la oferta

**Funcionalidad:**
- ✅ **Setea `penalizacion_omitida=True`** (requisito principal)
- Registra fecha de aceptación
- Guarda quién aceptó la justificación
- Muestra mensaje de confirmación
- Redirige a vista privada del trabajo

**Validaciones:**
- Solo el dueño de la oferta puede aceptar
- Método POST únicamente
- Previene aceptar dos veces

**Código clave:**
```python
justificacion.aceptar_justificacion(aceptado_por=request.user)
# Esto setea penalizacion_omitida=True automáticamente
```

**Mensaje mostrado:**
```
"Has aceptado la justificación de [Profesional]. 
La penalización por X días de atraso ha sido omitida."
```

---

### 3. **rechazar_replica_atraso** - Rechazar Justificación

**Ruta:** `/justificaciones/<justificacion_id>/rechazar/`  
**Archivo:** [usuarios/views.py](usuarios/views.py#L371-L388)  
**Acceso:** Login required, POST only, solo dueño de la oferta

**Funcionalidad:**
- No modifica el flag `penalizacion_omitida` (se mantiene en False)
- Informa al usuario que la penalización se mantiene
- Redirige a vista privada

---

## 🔗 URLs Configuradas

**Archivo:** [usuarios/urls.py](usuarios/urls.py)

```python
# Justificaciones de Atraso
path('ofertas/<int:oferta_id>/justificar-atraso/', 
     views.crear_justificacion_atraso, 
     name='crear_justificacion_atraso'),

path('justificaciones/<int:justificacion_id>/aceptar/', 
     views.aceptar_replica_atraso, 
     name='aceptar_replica_atraso'),

path('justificaciones/<int:justificacion_id>/rechazar/', 
     views.rechazar_replica_atraso, 
     name='rechazar_replica_atraso'),
```

---

## 🎨 Template Creado

**Archivo:** [templates/usuarios/crear_justificacion_atraso.html](templates/usuarios/crear_justificacion_atraso.html)

### Características:
- ✅ Hero section con días de atraso destacados
- ✅ Alert informativo sobre importancia de justificar
- ✅ Formulario de texto largo para la réplica
- ✅ Información del trabajo en sidebar
- ✅ Consejos para escribir una buena justificación
- ✅ Estado de la justificación (pendiente/aceptada)
- ✅ Diseño responsive y profesional

### Secciones principales:
1. **Hero**: Muestra título y días de atraso en grande
2. **Alert**: Explica por qué es importante justificar
3. **Formulario**: Textarea para la réplica del profesional
4. **Sidebar**: Info del trabajo, consejos, estado

---

## 👨‍💼 Panel de Admin

**Archivo:** [usuarios/admin.py](usuarios/admin.py)

### DelayJustificationAdmin implementado:

**List Display:**
- Profesional
- Título de la oferta
- Días de atraso justificados
- ✅ Penalización omitida (destacado)
- Aceptada por
- Fecha de creación

**Filtros:**
- Por `penalizacion_omitida` (Sí/No)
- Por fecha de creación
- Por fecha de aceptación

**Búsqueda:**
- Username del profesional
- Email del profesional
- Título de la oferta
- Texto de la réplica

**Fieldsets organizados:**
1. Información Principal (oferta, profesional)
2. Justificación (réplica, días)
3. Estado de Aceptación (flag, aceptada_por, fecha)
4. Fechas (metadata)

---

## 🗄️ Migraciones

**Archivo:** `usuarios/migrations/0003_joboffer_fecha_entrega_pactada_and_more.py`

**Cambios aplicados:**
- ✅ Añadido `fecha_entrega_pactada` a JobOffer
- ✅ Añadido `fecha_entrega_real` a JobOffer
- ✅ Añadido `fecha_inicio` a JobOffer
- ✅ Creado modelo completo `DelayJustification`

**Estado:** ✅ Migraciones aplicadas correctamente

---

## 🎯 Flujo Completo del Sistema

### Escenario: Trabajo con Atraso

#### 1️⃣ Detección del Atraso

```python
# En cualquier momento, el sistema puede calcular:
oferta = JobOffer.objects.get(id=123)
dias_atraso = oferta.dias_atraso

if dias_atraso and dias_atraso > 0:
    print(f"⚠️ Trabajo con {dias_atraso} días de atraso")
```

#### 2️⃣ Profesional Justifica

```
Profesional ve el trabajo con atraso →
Click en "Justificar Atraso" →
/ofertas/123/justificar-atraso/ →
Completa formulario con explicación →
Submit →
DelayJustification creada con penalizacion_omitida=False
```

#### 3️⃣ Cliente Revisa en Vista Privada

```html
<!-- En job_detail_private.html -->
{% if oferta.justificaciones_atraso.exists %}
    <div class="alert alert-warning">
        <strong>⚠️ Justificación de Atraso Pendiente</strong>
        <p>{{ justificacion.replica }}</p>
        <form method="post" action="{% url 'usuarios:aceptar_replica_atraso' justificacion.id %}">
            {% csrf_token %}
            <button class="btn btn-success">✓ Aceptar</button>
        </form>
        <form method="post" action="{% url 'usuarios:rechazar_replica_atraso' justificacion.id %}">
            {% csrf_token %}
            <button class="btn btn-danger">✗ Rechazar</button>
        </form>
    </div>
{% endif %}
```

#### 4️⃣ Cliente Acepta la Réplica

```
Cliente → Vista privada →
Ve justificación del profesional →
Click en "Aceptar" →
POST /justificaciones/456/aceptar/ →
justificacion.penalizacion_omitida = True ✅
justificacion.fecha_aceptacion = now()
justificacion.aceptada_por = cliente
```

#### 5️⃣ Resultado

```python
# Consulta final:
justificacion = DelayJustification.objects.get(id=456)
print(justificacion.penalizacion_omitida)  # True ✅
print(justificacion.aceptada_por)  # <User: cliente123>
print(justificacion.fecha_aceptacion)  # 2025-12-19 15:30:00

# El profesional NO recibirá penalización en su puntuación
```

---

## 📊 Integración con Sistema de Reputación (Futuro)

El flag `penalizacion_omitida` está listo para integrarse con un sistema de reputación:

```python
def calcular_penalizacion_reputacion(oferta):
    """
    Calcula si debe aplicarse penalización por atraso.
    """
    dias_atraso = oferta.dias_atraso
    
    if not dias_atraso or dias_atraso == 0:
        return 0  # Sin atraso
    
    # Verificar si hay justificación aceptada
    try:
        justificacion = oferta.justificaciones_atraso.get(
            profesional=oferta.profesional_asignado
        )
        if justificacion.penalizacion_omitida:
            return 0  # ✅ Penalización omitida por aceptación del cliente
    except DelayJustification.DoesNotExist:
        pass
    
    # Calcular penalización según días de atraso
    if dias_atraso <= 3:
        return 0.1  # Penalización leve
    elif dias_atraso <= 7:
        return 0.3  # Penalización media
    else:
        return 0.5  # Penalización severa
```

---

## 🔐 Permisos y Seguridad

### Verificaciones Implementadas:

1. **crear_justificacion_atraso:**
   - ✅ Usuario autenticado
   - ✅ Perfil existe
   - ✅ Rol = OFICIO
   - ✅ Existe atraso real

2. **aceptar_replica_atraso:**
   - ✅ Usuario autenticado
   - ✅ Usuario = dueño de la oferta
   - ✅ Método POST
   - ✅ CSRF token

3. **rechazar_replica_atraso:**
   - ✅ Usuario autenticado
   - ✅ Usuario = dueño de la oferta
   - ✅ Método POST
   - ✅ CSRF token

---

## 🧪 Casos de Prueba

### Caso 1: Crear Justificación
```python
# Setup
oferta = JobOffer.objects.create(
    titulo="Reparar baño",
    fecha_entrega_pactada=datetime(2025, 12, 15),
    fecha_entrega_real=datetime(2025, 12, 20)
)
profesional = User.objects.get(username="oficio1")

# Verificar atraso
assert oferta.dias_atraso == 5

# Crear justificación
justificacion = DelayJustification.objects.create(
    oferta=oferta,
    profesional=profesional,
    replica="Se retrasó por falta de materiales",
    dias_atraso_justificados=5
)

# Verificar estado inicial
assert justificacion.penalizacion_omitida == False
assert justificacion.fecha_aceptacion is None
```

### Caso 2: Aceptar Réplica
```python
# Setup
cliente = oferta.creador

# Aceptar justificación
justificacion.aceptar_justificacion(aceptado_por=cliente)

# Verificar
assert justificacion.penalizacion_omitida == True  # ✅
assert justificacion.fecha_aceptacion is not None
assert justificacion.aceptada_por == cliente
```

### Caso 3: Trabajo a Tiempo (Sin Atraso)
```python
oferta = JobOffer.objects.create(
    fecha_entrega_pactada=datetime(2025, 12, 20),
    fecha_entrega_real=datetime(2025, 12, 18)
)

# No hay atraso
assert oferta.dias_atraso == 0

# No se puede crear justificación
# La vista rechazaría con mensaje de error
```

---

## 📝 Resumen Ejecutivo

| Requisito | Estado | Implementación |
|-----------|--------|----------------|
| Añadir lógica `dias_atraso` en JobOffer | ✅ | Property con cálculo automático |
| Crear modelo DelayJustification | ✅ | Con todos los campos necesarios |
| Campo `replica` para la justificación | ✅ | TextField en el modelo |
| Endpoint para aceptar réplica | ✅ | `aceptar_replica_atraso` vista |
| Flag `penalizacion_omitida=True` | ✅ | Seteado al aceptar |
| Admin para gestión | ✅ | DelayJustificationAdmin completo |
| Template para crear justificación | ✅ | UI profesional y clara |
| Migraciones | ✅ | Aplicadas correctamente |
| Permisos y seguridad | ✅ | Validaciones completas |
| URLs configuradas | ✅ | 3 endpoints nuevos |

---

## 🚀 Próximos Pasos Sugeridos

1. **Integrar en job_detail_private.html:**
   - Mostrar justificaciones pendientes
   - Botones Aceptar/Rechazar inline

2. **Notificaciones:**
   - Email cuando se justifica atraso
   - Email cuando se acepta/rechaza

3. **Dashboard del profesional:**
   - Lista de justificaciones enviadas
   - Estado de cada una

4. **Métricas:**
   - % de justificaciones aceptadas
   - Tiempo promedio de respuesta

5. **Sistema de puntuación:**
   - Integrar `penalizacion_omitida` en cálculo
   - Restar puntos solo si no fue omitida

---

## ✨ Resultado Final

✅ **Sistema completamente funcional** para:
- Calcular atrasos automáticamente
- Permitir al OFICIO justificar atrasos
- Permitir al Cliente aceptar/rechazar justificaciones
- Omitir penalizaciones cuando se acepta la réplica
- Gestionar todo desde el admin

**El flag `penalizacion_omitida=True` se setea correctamente al aceptar la réplica** 🎯
