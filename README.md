# Kunfido - Plataforma de Gestión

Plataforma Django completa para la gestión de servicios, obras y consorcios con autenticación social mediante Google OAuth.

## 📋 Características

### Backend
- ✅ Django 4.2 con Python 3.10
- ✅ Autenticación con Google OAuth (django-allauth)
- ✅ Modelo UserProfile extendido con:
  - Tipo de rol (PERSONA, CONSORCIO, OFICIO)
  - Zona geográfica
  - Sistema de puntuación (0.0 - 5.0)
- ✅ Panel de administración personalizado con estadísticas
- ✅ Creación automática de perfiles mediante signals
- ✅ **Sistema de Ofertas y Propuestas**:
  - JobOffer: Ofertas de trabajo con estado y presupuesto
  - Proposal: Propuestas con sistema de contraofertas (versionado)
  - Sistema de votación para dueños de ofertas

### Frontend
- ✅ **Bootstrap 5.3.2** - Framework responsive moderno
- ✅ **Layout base** completo con navbar y footer
- ✅ **Onboarding interactivo** con 3 tarjetas de selección de rol
- ✅ **Dashboards personalizados** según tipo de usuario:
  - 👤 **PERSONA**: Servicios solicitados, favoritos
  - 🏢 **CONSORCIO**: Obras en el edificio, proveedores
  - 🔧 **OFICIO**: Trabajos ganados, propuestas
- ✅ Sistema de métricas y estadísticas visuales
- ✅ Diseño responsive con animaciones y efectos hover
- ✅ **Feed Público de Trabajos**:
  - Accesible sin login
  - Vista pública de detalles con botón "Ingresa para ofertar"
  - Vista privada para dueños con tabla comparativa de propuestas
  - Sistema de votación/selección de propuestas

## 🚀 Instalación

### 1. Crear entorno virtual (Python 3.10)

```bash
python -m venv venv
```

### 2. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo `.env.example` a `.env` y configura las variables:

```bash
copy .env.example .env
```

Edita el archivo `.env` con tus credenciales:

```env
SECRET_KEY=tu-clave-secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Credenciales de Google OAuth
GOOGLE_CLIENT_ID=tu-google-client-id
GOOGLE_CLIENT_SECRET=tu-google-client-secret
```

### 5. Configurar Google OAuth

1. Ve a [Google Cloud Console](https://console.developers.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google+
4. Ve a "Credenciales" → "Crear credenciales" → "ID de cliente de OAuth 2.0"
5. Configura:
   - Tipo de aplicación: Aplicación web
   - URIs de redirección autorizados:
     - `http://localhost:8000/accounts/google/login/callback/`
     - `http://127.0.0.1:8000/accounts/google/login/callback/`
6. Copia el Client ID y Client Secret al archivo `.env`

### 6. Aplicar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Crear superusuario

```bash
python manage.py createsuperuser
```

### 8. Configurar Google Social App en Django Admin

```bash
python manage.py runserver
```

Luego ve a: `http://localhost:8000/admin/`

1. Inicia sesión con el superusuario
2. Ve a "Sites" y verifica que existe un site con domain `example.com` (ID=1)
3. Ve a "Social applications" → "Add social application"
4. Configura:
   - Provider: Google
   - Name: Google OAuth
   - Client ID: (de tu .env)
   - Secret key: (de tu .env)
   - Sites: Selecciona el site disponible
5. Guarda

## 📊 Panel de Administración

El panel de administración personalizado muestra:

- Total de usuarios registrados
- Usuarios activos e inactivos
- Distribución por tipo de rol (Persona, Consorcio, Oficio)
- Puntuación promedio general y por rol
- Estadísticas visuales con gráficos

Accede en: `http://localhost:8000/admin/`

## 🎯 Uso

### Iniciar el servidor

```bash
python manage.py runserver
```

### Acceder a la aplicación

- **Home:** `http://localhost:8000/`
- **Feed Público:** `http://localhost:8000/trabajos/` (sin login requerido)
- **Onboarding (selección de rol):** `http://localhost:8000/onboarding/`
- **Dashboard:** `http://localhost:8000/dashboard/`
- **Admin:** `http://localhost:8000/admin/`
- **Login con Google:** `http://localhost:8000/accounts/google/login/`

## 🎨 Vistas Disponibles

### 1. **Home** (`/`)
Página principal responsive con:
- Hero section con call-to-action
- 3 tarjetas de features (Personas, Consorcios, Oficios)
- Integración con autenticación

### 2. **Feed Público de Trabajos** (`/trabajos/`) ⭐ NUEVO
Feed público accesible sin autenticación con:
- Lista de ofertas de trabajo abiertas
- Estadísticas generales (trabajos activos, propuestas, presupuesto promedio)
- Información de propuestas y mejor oferta por trabajo
- CTA para login/registro para usuarios no autenticados
- Link directo a enviar propuesta para usuarios OFICIO

### 3. **Detalle Público de Trabajo** (`/trabajos/<id>/`) ⭐ NUEVO
Vista pública del detalle de una oferta con:
- Información completa del trabajo (título, descripción, zona, presupuesto)
- Datos del publicador (con puntuación si disponible)
- Contador de propuestas y mejor oferta
- **Botón "Ingresa para ofertar"** para usuarios no autenticados
- Botón "Ver Propuestas Recibidas" si eres el dueño de la oferta
- Botón "Enviar Propuesta" para profesionales (OFICIO)

### 4. **Vista Privada del Dueño** (`/ofertas/<id>/privado/`) ⭐ NUEVO
Vista exclusiva para el creador de la oferta con:
- **Tabla comparativa de propuestas** con columnas:
  - Profesional (con avatar y versión de propuesta)
  - Monto (destacando mejor oferta)
  - Tiempo de entrega (días)
  - Reputación (con badges de color según puntuación)
  - Fecha de envío
  - **Botón Votar/Votada** para seleccionar propuestas
- Estadísticas rápidas (total propuestas, mejor oferta, promedios)
- Highlight visual de mejor oferta y propuestas votadas
- Información adicional del trabajo y consejos

### 5. **Onboarding** (`/onboarding/`)
Sistema de selección de rol con:
- 3 tarjetas interactivas (PERSONA, CONSORCIO, OFICIO)
- Animaciones hover y efectos visuales
- Campo opcional para zona geográfica
- Diseño con gradientes personalizados por rol

### 6. **Dashboard** (`/dashboard/`)
Dashboard personalizado según el rol del usuario:

#### 👤 PERSONA
- Servicios Solicitados (7)
- En Proceso (3)
- Profesionales Favoritos (5)
- Gastos en Servicios ($8.5K)
- Actividad reciente

#### 🏢 CONSORCIO
- **Obras en el Edificio (15)**
- Obras Completadas (32)
- Proveedores Activos (48)
- Presupuesto Mensual ($125K)
- Gestión de obras del edificio

#### 🔧 OFICIO
- **Trabajos Ganados (24)**
- En Progreso (8)
- Propuestas Enviadas (12)
- Ingresos Totales ($45.8K)
- Historial de trabajos

## 📁 Estructura del Proyecto

```
kunfido/
├── kunfido/                 # Configuración del proyecto
│   ├── __init__.py
│   ├── settings.py         # Configuración principal + django-allauth
│   ├── urls.py             # URLs principales
│   ├── asgi.py
│   └── wsgi.py
├── usuarios/                # App de usuarios
│   ├── models.py           # UserProfile, JobOffer, Proposal
│   ├── admin.py            # Admin personalizado con estadísticas
│   ├── signals.py          # Señales para crear perfiles automáticamente
│   ├── views.py            # Vistas completas (public, private)
│   ├── urls.py             # URLs de la app
│   ├── templatetags/
│   │   └── usuarios_tags.py  # Filtros personalizados
│   └── apps.py
├── templates/
│   ├── base.html           # Layout base con Bootstrap 5
│   ├── admin/
│   │   └── index.html      # Admin con métricas personalizadas
│   └── usuarios/
│       ├── home.html                # Página principal
│       ├── onboarding_rol.html      # Selección de rol
│       ├── dashboard_home.html      # Dashboard condicional
│       ├── public_feed.html         # Feed público de trabajos ⭐
│       ├── job_detail_public.html   # Detalle público ⭐
│       ├── job_detail_private.html  # Vista dueño con tabla ⭐
│       ├── ofertas_lista.html       # Lista de ofertas
│       ├── oferta_detalle.html      # Detalle de oferta
│       └── crear_propuesta.html     # Crear/actualizar propuesta
├── manage.py
├── requirements.txt        # Django, django-allauth, python-decouple, Pillow
├── .env.example           # Template de variables de entorno
├── .gitignore
└── README.md
```

## 🔧 Tecnologías

### Backend
- Python 3.10
- Django 4.2.11
- django-allauth 0.61.1 (OAuth con Google)
- python-decouple 3.8 (Variables de entorno)
- Pillow 10.2.0 (Procesamiento de imágenes)
- SQLite (desarrollo)

### Frontend
- Bootstrap 5.3.2
- Bootstrap Icons 1.11.3
- Vanilla JavaScript (interactividad)

## 👥 Modelos de Datos

### UserProfile
Extiende el usuario de Django con:
- `tipo_rol`: PERSONA, CONSORCIO u OFICIO (choices)
- `zona`: Zona geográfica (texto libre, opcional)
- `puntuacion`: Float de 0.0 a 5.0 (con validadores)
- `fecha_creacion`: Timestamp de creación (auto)
- `fecha_actualizacion`: Timestamp de última actualización (auto)

#### Propiedades adicionales:
- `email`: Retorna el email del usuario
- `nombre_completo`: Retorna nombre completo o username

### JobOffer ⭐ NUEVO
Modelo para ofertas de trabajo:
- `creador`: Usuario que crea la oferta (ForeignKey)
- `titulo`: Título descriptivo
- `descripcion`: Descripción detallada (opcional)
- `zona`: Zona geográfica del trabajo
- `presupuesto_ars`: Presupuesto estimado en ARS
- `status`: ABIERTA, EN_PROGRESO, FINALIZADA, CANCELADA
- `fecha_creacion`, `fecha_actualizacion`

### Proposal ⭐ NUEVO
Modelo para propuestas de profesionales:
- `oferta`: Oferta de trabajo (ForeignKey)
- `profesional`: Usuario OFICIO que envía propuesta (ForeignKey)
- `monto`: Monto propuesto en ARS
- `dias_entrega`: Días estimados para completar
- `comentario`: Detalles adicionales (opcional)
- `version`: Número de versión (auto-incrementa en actualizaciones)
- `voto_owner`: Boolean si el dueño votó esta propuesta ⭐
- `fecha_creacion`, `fecha_actualizacion`
- **Constraint**: unique_together en (oferta, profesional) - solo 1 propuesta por profesional por oferta

## 🎨 Características del Frontend

- **Diseño responsive**: Mobile-first, adaptable a todos los dispositivos
- **Animaciones suaves**: Transiciones y efectos hover personalizados
- **Gradientes personalizados**: Identidad visual por tipo de rol
- **Tarjetas interactivas**: Selección visual con feedback inmediato
- **Sistema de badges**: Indicadores visuales de estado y selección
- **Navbar dinámica**: Menú que se adapta según el usuario autenticado
- **Mensajes toast**: Sistema de notificaciones integrado con Django

## 📝 Notas Importantes

- ✅ El perfil de usuario se crea automáticamente mediante Django signals
- ✅ La autenticación con email está habilitada por defecto
- ✅ Verificación de email obligatoria (configurable)
- ✅ En desarrollo, los emails se muestran en consola
- ✅ Las vistas protegidas requieren login (`@login_required`)
- ✅ Redirección automática a onboarding si falta el rol
- ✅ El admin personalizado muestra estadísticas en tiempo real

## 🔐 Seguridad

- Secret key mediante variables de entorno
- CSRF protection habilitado
- Validaciones en formularios
- Session management con django-allauth
- Password validators activos

## 🚧 Roadmap

- [ ] Sistema de solicitudes de servicio
- [ ] Chat en tiempo real entre usuarios
- [ ] Sistema de calificaciones y reviews
- [ ] Gestión de presupuestos y propuestas
- [ ] Panel de reportes y analytics
- [ ] Notificaciones push
- [ ] API REST con Django REST Framework
- [ ] App móvil (React Native)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

---

**Desarrollado con ❤️ usando Django y Bootstrap 5**
