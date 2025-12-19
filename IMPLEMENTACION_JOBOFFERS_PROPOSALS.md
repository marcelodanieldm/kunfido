# Implementación de JobOffer y Proposal - Kunfido

## ✅ Estado: **COMPLETADO**

Todos los componentes solicitados ya están implementados y funcionando en el proyecto.

---

## 📋 Modelos Implementados

### 1. **JobOffer** (Oferta de Trabajo)
Ubicación: `usuarios/models.py` (líneas 73-151)

**Campos:**
- `titulo` - CharField(200) - Título descriptivo de la oferta
- `zona` - CharField(255) - Zona geográfica del trabajo
- `presupuesto_ars` - DecimalField(10,2) - Presupuesto en pesos argentinos
- `status` - CharField(20) - Estado: ABIERTA, EN_PROGRESO, FINALIZADA, CANCELADA
- `descripcion` - TextField - Descripción detallada (opcional)
- `creador` - ForeignKey(User) - Usuario que creó la oferta
- `fecha_creacion` - DateTimeField - Auto-generado
- `fecha_actualizacion` - DateTimeField - Auto-actualizado

**Características especiales:**
- Property `cantidad_propuestas` que cuenta las propuestas recibidas
- Validación de presupuesto mínimo (> 0)
- Ordenamiento por fecha de creación (más recientes primero)

---

### 2. **Proposal** (Propuesta/Contraoferta)
Ubicación: `usuarios/models.py` (líneas 153-229)

**Campos:**
- `monto` - DecimalField(10,2) - Monto propuesto por el profesional
- `dias_entrega` - PositiveIntegerField - Días estimados para completar
- `comentario` - TextField - Detalles adicionales (opcional)
- `oferta` - ForeignKey(JobOffer) - Oferta a la que responde
- `profesional` - ForeignKey(User) - Usuario OFICIO que propone
- `version` - PositiveIntegerField - Número de versión (contraofertas)
- `voto_owner` - BooleanField - Voto del dueño de la oferta
- `fecha_creacion` - DateTimeField - Auto-generado
- `fecha_actualizacion` - DateTimeField - Auto-actualizado

**Características especiales:**
- **Sistema de contraofertas**: Cada vez que se actualiza una propuesta, incrementa automáticamente el campo `version`
- **Unique constraint**: Un profesional solo puede tener una propuesta por oferta (se actualiza en lugar de crear duplicados)
- Validación de monto mínimo (> 0)
- Método `save()` personalizado para gestionar versiones

---

## 🌐 Vistas Implementadas

### 1. **public_feed** - Feed Público
**Ruta:** `/trabajos/`  
**Archivo:** `usuarios/views.py` (líneas 65-81)

**Funcionalidad:**
- Muestra todas las ofertas con status 'ABIERTA'
- Accesible sin autenticación
- Incluye anotaciones de cantidad de propuestas y monto mínimo
- Calcula estadísticas generales (promedio presupuesto, total propuestas)

---

### 2. **ofertas_lista** - Lista de Ofertas
**Ruta:** `/ofertas/`  
**Archivo:** `usuarios/views.py` (líneas 84-111)

**Funcionalidad:**
- Lista pública de ofertas abiertas
- Para usuarios OFICIO autenticados: muestra sus propuestas existentes
- Datos anotados: número de propuestas, monto mínimo
- Ordenamiento por fecha de creación

---

### 3. **job_detail_public** - Detalle Público
**Ruta:** `/trabajos/<oferta_id>/`  
**Archivo:** `usuarios/views.py` (líneas 114-128)

**Funcionalidad:**
- Vista pública del detalle de una oferta
- Muestra información completa de la oferta
- Cuenta propuestas y monto mínimo
- Botón "Ingresa para ofertar" para usuarios no autenticados

---

### 4. **job_detail_private** - Detalle Privado (Dueño)
**Ruta:** `/ofertas/<oferta_id>/privado/`  
**Archivo:** `usuarios/views.py` (líneas 131-160)

**Funcionalidad:**
- Solo accesible para el creador de la oferta
- Tabla comparativa de todas las propuestas
- Estadísticas: monto mínimo, promedio, días promedio
- Sistema de votación de propuestas
- Información del profesional (puntuación, versión)

---

### 5. **crear_propuesta** - Crear/Actualizar Propuesta
**Ruta:** `/ofertas/<oferta_id>/propuesta/`  
**Archivo:** `usuarios/views.py` (líneas 230-282)

**Funcionalidad: Sistema de Puja/Contraoferta**
1. **Verificación de permisos:**
   - Solo usuarios con rol 'OFICIO' pueden crear propuestas
   - Verifica que la oferta esté 'ABIERTA'

2. **Detección automática:**
   - Si no existe propuesta previa: **Crear nueva**
   - Si ya existe propuesta: **Actualizar (contraoferta/puja)**

3. **Proceso de contraoferta:**
   ```python
   if es_actualizacion:
       propuesta.monto = nuevo_monto
       propuesta.dias_entrega = nuevos_dias
       propuesta.comentario = nuevo_comentario
       propuesta.save()  # Auto-incrementa version
       # Mensaje: "¡Contraoferta enviada! (Versión {version})"
   ```

4. **Validaciones:**
   - Monto y días deben ser valores positivos
   - Manejo de errores de tipo de datos

---

### 6. **votar_propuesta** - Sistema de Votación
**Ruta:** `/propuestas/<propuesta_id>/votar/`  
**Archivo:** `usuarios/views.py` (líneas 209-227)

**Funcionalidad:**
- Solo el dueño de la oferta puede votar
- Toggle: votar/desvotar propuesta
- Método POST únicamente
- Redirección a vista privada del detalle

---

## 🔗 URLs Configuradas

**Archivo:** `usuarios/urls.py`

```python
# Feed Público
path('trabajos/', views.public_feed, name='public_feed'),
path('trabajos/<int:oferta_id>/', views.job_detail_public, name='job_detail_public'),

# Ofertas y Propuestas
path('ofertas/', views.ofertas_lista, name='ofertas_lista'),
path('ofertas/<int:oferta_id>/', views.oferta_detalle, name='oferta_detalle'),
path('ofertas/<int:oferta_id>/propuesta/', views.crear_propuesta, name='crear_propuesta'),
path('ofertas/<int:oferta_id>/privado/', views.job_detail_private, name='job_detail_private'),

# Votación
path('propuestas/<int:propuesta_id>/votar/', views.votar_propuesta, name='votar_propuesta'),
```

---

## 🎯 Flujo de Uso: Sistema de Puja

### Para Usuarios OFICIO (Profesionales):

1. **Primera Propuesta:**
   ```
   Usuario OFICIO → Ver oferta pública → Crear propuesta
   - Ingresar monto, días, comentario
   - Se crea Proposal (version=1)
   ```

2. **Contraoferta (Puja):**
   ```
   Usuario OFICIO → Ver misma oferta → Actualizar propuesta
   - Modificar monto/días/comentario
   - Se actualiza Proposal (version=2, 3, 4...)
   - Mensaje: "¡Contraoferta enviada! (Versión X)"
   ```

### Para Dueños de Ofertas:

```
Dueño → Vista privada → Ver tabla de propuestas
- Ordenadas por monto (menor primero)
- Ver versión de cada propuesta
- Votar/desvotar propuestas favoritas
- Estadísticas comparativas
```

---

## 📊 Características del Sistema de Puja

### Ventajas del Sistema Implementado:

1. **Historial automático:** El campo `version` registra cuántas veces se actualizó
2. **Única propuesta por profesional:** Constraint de base de datos previene duplicados
3. **Actualización transparente:** El mismo formulario sirve para crear y actualizar
4. **Fechas automáticas:** `fecha_actualizacion` registra cuándo fue la última puja
5. **Competencia justa:** Todos los profesionales pueden ajustar su oferta

### Ejemplo de Secuencia:

```
Oferta: "Reparar baño en Palermo - $50,000 ARS"

Profesional A:
- v1: $45,000 - 5 días
- v2: $42,000 - 5 días (contraoferta)
- v3: $40,000 - 4 días (puja final)

Profesional B:
- v1: $48,000 - 3 días
- v2: $46,000 - 3 días (contraoferta)

Profesional C:
- v1: $39,000 - 7 días

Dueño ve tabla ordenada:
1. Profesional C - $39,000 (v1) ⭐
2. Profesional A - $40,000 (v3) ⭐ VOTADO
3. Profesional B - $46,000 (v2)
```

---

## 🗄️ Migraciones

Las migraciones ya están aplicadas:
- `0001_initial.py` - Modelos base
- `0002_proposal_voto_owner.py` - Sistema de votación

Estado: **No hay cambios pendientes**

---

## 🎨 Templates Disponibles

- `usuarios/public_feed.html` - Feed público
- `usuarios/ofertas_lista.html` - Lista de ofertas
- `usuarios/job_detail_public.html` - Detalle público
- `usuarios/job_detail_private.html` - Detalle privado (dueño)
- `usuarios/oferta_detalle.html` - Detalle general
- `usuarios/crear_propuesta.html` - Formulario de propuesta/contraoferta

---

## ✨ Próximos Pasos Sugeridos

1. **Notificaciones:** Sistema de alertas cuando se recibe contraoferta
2. **Chat:** Comunicación entre dueño y profesionales
3. **Aceptación:** Proceso para cerrar la oferta con un ganador
4. **Reputación:** Sistema de reviews post-trabajo
5. **Filtros:** Por zona, rango de presupuesto, etc.

---

## 📝 Resumen Ejecutivo

✅ **Modelo JobOffer** implementado con todos los campos solicitados  
✅ **Modelo Proposal** implementado con sistema de contraofertas  
✅ **Vista pública** de lista de ofertas funcionando  
✅ **Sistema de puja** mediante update automático de propuestas  
✅ **Constraint unique_together** previene propuestas duplicadas  
✅ **Sistema de versiones** registra historial de contraofertas  
✅ **Permisos correctos** para rol OFICIO  

**Estado:** Sistema completamente funcional y listo para usar.
