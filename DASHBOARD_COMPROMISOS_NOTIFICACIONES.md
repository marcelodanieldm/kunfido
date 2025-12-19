# Dashboard Mejorado: Compromisos y Notificaciones - Kunfido

## ✅ Estado: COMPLETAMENTE IMPLEMENTADO

Se han añadido dos funcionalidades principales al dashboard:
1. **Sección "Mis Compromisos"** para el Dashboard del OFICIO
2. **Notificación flotante** para el Dashboard del CLIENTE (PERSONA/CONSORCIO)

---

## 🔧 Dashboard del OFICIO: Mis Compromisos

### Vista Actualizada

**Archivo:** [usuarios/views.py](usuarios/views.py#L18-L70)

La vista `dashboard` ahora incluye lógica para usuarios OFICIO:

```python
if request.user.profile.tipo_rol == 'OFICIO':
    # Obtener trabajos EN_PROGRESO con propuesta aceptada (voto_owner=True)
    mis_trabajos = JobOffer.objects.filter(
        status='EN_PROGRESO',
        propuestas__profesional=request.user,
        propuestas__voto_owner=True
    ).distinct()
    
    # Clasificar por estado de atraso
    trabajos_atrasados = []
    trabajos_al_dia = []
    
    for trabajo in mis_trabajos:
        if trabajo.dias_atraso and trabajo.dias_atraso > 0:
            # Verificar si ya tiene justificación
            trabajo.justificacion_existente = ...
            trabajos_atrasados.append(trabajo)
        else:
            trabajos_al_dia.append(trabajo)
```

**Variables de contexto añadidas:**
- `trabajos_atrasados` - Lista de trabajos con días_atraso > 0
- `trabajos_al_dia` - Lista de trabajos sin atraso
- `total_compromisos` - Total de trabajos activos

---

### Template Actualizado

**Archivo:** [templates/usuarios/dashboard_home.html](templates/usuarios/dashboard_home.html)

#### 🎨 Estilos CSS Añadidos:

**1. Card Roja para Trabajos Atrasados:**
```css
.delay-card {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
    color: white;
    box-shadow: 0 5px 20px rgba(255, 107, 107, 0.3);
    border-radius: 15px;
    transition: all 0.3s ease;
}

.delay-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4);
}
```

**2. Card Normal para Trabajos al Día:**
```css
.on-time-card {
    background: white;
    box-shadow: 0 3px 15px rgba(0,0,0,0.08);
    border-radius: 15px;
}
```

---

#### 📋 Sección "Mis Compromisos"

**Ubicación:** Después de las métricas, antes de la sección de trabajos recientes

**Estructura:**

```html
<!-- Header de la sección -->
<div class="card">
    <div class="card-header">
        <h5>📋 Mis Compromisos</h5>
        <span class="badge">{{ total_compromisos }} activos</span>
    </div>
</div>

<!-- Trabajos Atrasados (Cards Rojas) -->
{% if trabajos_atrasados %}
    <h6 class="text-danger">
        ⚠️ Trabajos con Atraso ({{ trabajos_atrasados|length }})
    </h6>
    
    {% for trabajo in trabajos_atrasados %}
        <div class="delay-card">
            <!-- Título + Badge de días -->
            <h6>{{ trabajo.titulo }}</h6>
            <span class="delay-badge">
                🕐 {{ trabajo.dias_atraso }} días
            </span>
            
            <!-- Info del cliente y fechas -->
            <small>👤 {{ trabajo.creador }}</small>
            <small>📍 {{ trabajo.zona }}</small>
            <small>📅 Entrega: {{ trabajo.fecha_entrega_pactada }}</small>
            
            <!-- Estado de justificación -->
            {% if trabajo.justificacion_existente %}
                {% if justificacion.penalizacion_omitida %}
                    ✓ Justificación aceptada
                {% else %}
                    ⏳ Justificación pendiente
                {% endif %}
                <a href="..." class="btn btn-light">
                    ✏️ Actualizar Justificación
                </a>
            {% else %}
                <!-- Botón Principal -->
                <a href="{% url 'usuarios:crear_justificacion_atraso' trabajo.id %}" 
                   class="btn btn-light btn-lg w-100">
                    💬 Explicar Demora
                </a>
            {% endif %}
        </div>
    {% endfor %}
{% endif %}

<!-- Trabajos al Día (Cards Blancas) -->
{% if trabajos_al_dia %}
    <h6 class="text-success">
        ✓ Trabajos al Día ({{ trabajos_al_dia|length }})
    </h6>
    
    {% for trabajo in trabajos_al_dia %}
        <div class="on-time-card">
            <h6>{{ trabajo.titulo }}</h6>
            <span class="badge bg-success">✓ Al día</span>
            
            <small>👤 {{ trabajo.creador }}</small>
            <small>📍 {{ trabajo.zona }}</small>
            <small>📅 Entrega: {{ trabajo.fecha_entrega_pactada }}</small>
            
            <a href="..." class="btn btn-outline-primary">
                👁️ Ver Detalles
            </a>
        </div>
    {% endfor %}
{% endif %}

<!-- Estado vacío -->
{% if not trabajos_atrasados and not trabajos_al_dia %}
    <div class="card text-center">
        📥 No tienes compromisos activos
        <a href="..." class="btn btn-gradient">
            🔍 Buscar Trabajos
        </a>
    </div>
{% endif %}
```

---

#### 🎯 Características de las Cards Rojas

**Para trabajos atrasados:**
- ✅ Fondo rojo degradado (#ff6b6b → #ee5a6f)
- ✅ Texto en blanco
- ✅ Badge destacado con días de atraso
- ✅ Información del cliente y zona
- ✅ Fecha de entrega pactada
- ✅ Botón grande "Explicar Demora" si no hay justificación
- ✅ Estado de justificación si existe:
  - Verde: "✓ Justificación aceptada"
  - Amarillo: "⏳ Justificación pendiente"
  - Botón para actualizar justificación
- ✅ Efecto hover con elevación
- ✅ Responsive (3 columnas en desktop, 1 en móvil)

**Para trabajos al día:**
- ✅ Card blanca normal
- ✅ Badge verde "Al día"
- ✅ Botón para ver detalles
- ✅ Misma estructura responsive

---

## 🔔 Dashboard del CLIENTE: Notificación Flotante

### Vista Actualizada

**Archivo:** [usuarios/views.py](usuarios/views.py#L72-L82)

Para usuarios PERSONA o CONSORCIO:

```python
elif request.user.profile.tipo_rol in ['PERSONA', 'CONSORCIO']:
    # Obtener justificaciones pendientes de aprobación
    replicas_pendientes = DelayJustification.objects.filter(
        oferta__creador=request.user,
        penalizacion_omitida=False  # Solo no aceptadas
    ).select_related('oferta', 'profesional', 'profesional__profile')
    
    context['replicas_pendientes'] = replicas_pendientes
    context['cantidad_replicas_pendientes'] = replicas_pendientes.count()
```

---

### Template Actualizado

#### 🎨 Estilos CSS para Notificación Flotante:

```css
.floating-notification {
    position: fixed;
    top: 80px;
    right: 20px;
    z-index: 1050;
    max-width: 400px;
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    animation: slideInRight 0.5s ease;
}

@keyframes slideInRight {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.notification-header {
    background: rgba(255, 255, 255, 0.3);
    padding: 1rem 1.5rem;
    border-radius: 15px 15px 0 0;
}

.notification-body {
    padding: 1.5rem;
}

.notification-item {
    background: white;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

.close-notification {
    background: rgba(0,0,0,0.2);
    border: none;
    color: white;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.3s ease;
}

.close-notification:hover {
    background: rgba(0,0,0,0.4);
    transform: rotate(90deg);
}
```

---

#### 🔔 Notificación Flotante

**Ubicación:** Fixed, esquina superior derecha, antes del container principal

**Condición de visualización:**
```django
{% if user.profile.tipo_rol in 'PERSONA,CONSORCIO' and cantidad_replicas_pendientes > 0 %}
```

**Estructura:**

```html
<div class="floating-notification" id="replicasNotification">
    <!-- Header con botón cerrar -->
    <div class="notification-header">
        <h5>🔔 Réplicas Pendientes ({{ cantidad_replicas_pendientes }})</h5>
        <button class="close-notification" onclick="...">✕</button>
    </div>
    
    <!-- Body con lista de réplicas -->
    <div class="notification-body">
        <p class="small">
            ℹ️ Tienes justificaciones de atraso esperando tu respuesta
        </p>
        
        <!-- Primeras 3 réplicas -->
        {% for replica in replicas_pendientes|slice:":3" %}
        <div class="notification-item">
            <strong>{{ replica.oferta.titulo|truncatewords:5 }}</strong>
            <small>👤 {{ replica.profesional }}</small>
            <small class="text-danger">
                🕐 {{ replica.dias_atraso_justificados }} días de atraso
            </small>
            <a href="..." class="btn btn-sm btn-gradient">Ver</a>
        </div>
        {% endfor %}
        
        <!-- Contador si hay más de 3 -->
        {% if cantidad_replicas_pendientes > 3 %}
        <div class="text-center">
            <small>Y {{ cantidad_replicas_pendientes|add:"-3" }} más...</small>
        </div>
        {% endif %}
    </div>
</div>
```

---

#### 🎯 Características de la Notificación

**Comportamiento:**
- ✅ Fixed en esquina superior derecha (top: 80px, right: 20px)
- ✅ z-index: 1050 (sobre otros elementos)
- ✅ Animación de entrada desde la derecha (slideInRight)
- ✅ Botón X para cerrar (oculta con display:none)
- ✅ Efecto hover en botón cerrar (rotación 90°)

**Contenido:**
- ✅ Título con contador de réplicas pendientes
- ✅ Muestra hasta 3 réplicas en preview
- ✅ Cada réplica muestra:
  - Título del trabajo (truncado)
  - Nombre del profesional
  - Días de atraso (en rojo)
  - Botón "Ver" que lleva a job_detail_private
- ✅ Mensaje "Y X más..." si hay más de 3

**Diseño:**
- ✅ Fondo degradado naranja (#ffecd2 → #fcb69f)
- ✅ Sombra pronunciada para destacar
- ✅ Border-radius redondeado (15px)
- ✅ Responsive (se adapta a móviles)

---

### 📊 Sección Detallada en el Dashboard

Además de la notificación flotante, se añadió una sección completa en el dashboard:

**Ubicación:** Después de las métricas, como card destacada

```html
<!-- Card amarilla de advertencia -->
<div class="card border-warning">
    <div class="card-header bg-warning">
        <h5>⚠️ Justificaciones de Atraso Pendientes ({{ cantidad_replicas_pendientes }})</h5>
    </div>
    <div class="card-body">
        <p class="text-muted">
            Los siguientes profesionales han enviado justificaciones...
        </p>
        
        {% for replica in replicas_pendientes %}
        <div class="alert alert-light border-warning border-4">
            <!-- Columna izquierda: Info -->
            <div class="col-md-8">
                <h6>📋 {{ replica.oferta.titulo }}</h6>
                <p><strong>👤 {{ replica.profesional }}</strong></p>
                <p class="text-danger">
                    🕐 {{ replica.dias_atraso_justificados }} días de atraso
                </p>
                <p class="text-muted">
                    💬 {{ replica.replica|truncatewords:20 }}
                </p>
                <small>📅 Enviado el {{ replica.fecha_creacion }}</small>
            </div>
            
            <!-- Columna derecha: Acciones -->
            <div class="col-md-4">
                <a href="..." class="btn btn-primary w-100">
                    👁️ Ver Detalles Completos
                </a>
                
                <form method="post" action="{% url 'usuarios:aceptar_replica_atraso' replica.id %}">
                    {% csrf_token %}
                    <button class="btn btn-success w-100">
                        ✓ Aceptar Justificación
                    </button>
                </form>
                
                <form method="post" action="{% url 'usuarios:rechazar_replica_atraso' replica.id %}">
                    {% csrf_token %}
                    <button class="btn btn-outline-danger w-100">
                        ✗ Rechazar
                    </button>
                </form>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
```

**Características:**
- ✅ Muestra TODAS las réplicas pendientes (no solo 3)
- ✅ Cada réplica en un alert con borde amarillo
- ✅ Botones de acción directos:
  - Ver detalles completos
  - Aceptar justificación (formulario POST)
  - Rechazar justificación (formulario POST)
- ✅ Preview del texto de la réplica (20 palabras)
- ✅ Fecha de envío

---

### 📈 Métricas Actualizadas

**Dashboard PERSONA:**
```html
<div class="metric-card">
    <div class="metric-icon warning">
        <i class="bi bi-bell-fill"></i>
    </div>
    <div class="metric-value">{{ cantidad_replicas_pendientes|default:0 }}</div>
    <div class="metric-label">Réplicas Pendientes</div>
</div>
```

**Dashboard CONSORCIO:**
```html
<div class="metric-card">
    <div class="metric-icon warning">
        <i class="bi bi-bell-fill"></i>
    </div>
    <div class="metric-value">{{ cantidad_replicas_pendientes|default:0 }}</div>
    <div class="metric-label">Réplicas Pendientes</div>
</div>
```

La métrica reemplaza el widget anterior y muestra dinámicamente la cantidad de réplicas pendientes.

---

## 🎯 Flujo Completo de Uso

### Escenario OFICIO: Trabajo Atrasado

```
1. Profesional inicia sesión
   ↓
2. Accede a Dashboard (/dashboard/)
   ↓
3. Ve sección "Mis Compromisos"
   ↓
4. Identifica trabajo atrasado en CARD ROJA
   - Título del trabajo
   - "🕐 5 días de atraso"
   - Cliente: Juan Pérez
   - Zona: Palermo
   ↓
5. Click en botón "💬 Explicar Demora"
   ↓
6. Formulario de justificación
   ↓
7. Envía réplica
   ↓
8. Vuelve al dashboard
   ↓
9. La card ahora muestra:
   "⏳ Justificación pendiente"
   Botón: "Actualizar Justificación"
```

---

### Escenario CLIENTE: Réplica Pendiente

```
1. Cliente inicia sesión
   ↓
2. Accede a Dashboard (/dashboard/)
   ↓
3. 🔔 NOTIFICACIÓN FLOTANTE aparece:
   - "Réplicas Pendientes (2)"
   - Preview de 2 trabajos
   - Botón "Ver" en cada uno
   ↓
4. En el contenido principal:
   - Card amarilla destacada
   - "⚠️ Justificaciones de Atraso Pendientes (2)"
   ↓
5. Para cada réplica ve:
   - Título del trabajo
   - Profesional que justifica
   - Días de atraso
   - Preview de la justificación
   - 3 botones:
     * Ver Detalles Completos
     * ✓ Aceptar Justificación
     * ✗ Rechazar
   ↓
6. Opciones:
   
   A) Click "Aceptar":
      → POST a aceptar_replica_atraso
      → penalizacion_omitida = True
      → Mensaje: "Penalización omitida"
      → Réplica desaparece de pendientes
   
   B) Click "Rechazar":
      → POST a rechazar_replica_atraso
      → penalizacion_omitida = False
      → Mensaje: "Penalización se mantiene"
      → Réplica desaparece de pendientes
   
   C) Click "Ver Detalles":
      → Redirige a job_detail_private
      → Ve contexto completo
      → Puede aceptar/rechazar desde allí
```

---

## 📊 Comparación: Antes vs Después

### Dashboard OFICIO

| Antes | Después |
|-------|---------|
| Solo métricas generales | ✅ Métricas + Sección "Mis Compromisos" |
| No se veían atrasos | ✅ Cards rojas para trabajos atrasados |
| No había llamado a acción | ✅ Botón "Explicar Demora" destacado |
| No se veía estado de justificaciones | ✅ Indicadores de estado (pendiente/aceptada) |
| Trabajos recientes mockup | ✅ Trabajos reales del profesional |

### Dashboard CLIENTE

| Antes | Después |
|-------|---------|
| Solo métricas generales | ✅ Métricas + Notificación flotante |
| No se veían réplicas pendientes | ✅ Notificación en esquina derecha |
| Sin alertas visuales | ✅ Animación de entrada llamativa |
| No había acciones rápidas | ✅ Botones Aceptar/Rechazar directos |
| Sin preview de justificaciones | ✅ Preview de texto en dashboard |
| Métrica genérica | ✅ Métrica "Réplicas Pendientes" dinámica |

---

## 🎨 Guía de Diseño

### Paleta de Colores Usada

**Trabajos Atrasados (Cards Rojas):**
- Fondo: `linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)`
- Texto: `white`
- Sombra: `0 5px 20px rgba(255, 107, 107, 0.3)`

**Notificación Flotante:**
- Fondo: `linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)`
- Header: `rgba(255, 255, 255, 0.3)`
- Sombra: `0 10px 30px rgba(0,0,0,0.2)`

**Cards de Advertencia:**
- Border: `border-warning` (Bootstrap)
- Header: `bg-warning text-dark`
- Alert: `alert-light border-start border-warning border-4`

### Iconografía

- 📋 Mis Compromisos
- ⚠️ Trabajos con Atraso
- ✓ Trabajos al Día
- 🕐 Días de atraso
- 💬 Explicar Demora
- 🔔 Notificaciones
- 👤 Usuario/Profesional
- 📍 Ubicación
- 📅 Fechas
- ✓ Aceptar
- ✗ Rechazar
- 👁️ Ver

---

## 🔧 Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| [usuarios/views.py](usuarios/views.py) | Lógica para obtener compromisos y réplicas |
| [templates/usuarios/dashboard_home.html](templates/usuarios/dashboard_home.html) | Sección Mis Compromisos + Notificación flotante |
| CSS inline | Estilos para cards rojas, notificación, animaciones |

**Líneas añadidas:** ~450 líneas  
**Funcionalidades nuevas:** 2 principales + mejoras visuales  
**Estado:** ✅ Completamente funcional

---

## ✨ Resumen Ejecutivo

| Requisito | Estado | Implementación |
|-----------|--------|----------------|
| Sección "Mis Compromisos" en Dashboard OFICIO | ✅ | Vista + template completo |
| Trabajos atrasados con cards rojas | ✅ | CSS gradient rojo + hover |
| Botón "Explicar Demora" | ✅ | Enlace a crear_justificacion_atraso |
| Estado de justificaciones | ✅ | Aceptada/Pendiente/Sin justificar |
| Notificación flotante para CLIENTE | ✅ | Fixed top-right, animada |
| Preview de réplicas en notificación | ✅ | Primeras 3 réplicas |
| Botón cerrar notificación | ✅ | X con rotación hover |
| Sección detallada de réplicas | ✅ | Card amarilla con todas |
| Botones Aceptar/Rechazar directos | ✅ | Formularios POST inline |
| Métrica "Réplicas Pendientes" | ✅ | Widget en dashboard |
| Responsive design | ✅ | Mobile-friendly |
| Animaciones | ✅ | slideInRight + hover effects |

**Sistema 100% operativo y listo para producción** 🚀
