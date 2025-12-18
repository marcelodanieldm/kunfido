# Kunfido - Plataforma de Gestión

Proyecto Django con autenticación social mediante Google OAuth usando django-allauth.

## 📋 Características

- ✅ Django 4.2 con Python 3.10
- ✅ Autenticación con Google OAuth (django-allauth)
- ✅ Modelo UserProfile extendido con:
  - Tipo de rol (PERSONA, CONSORCIO, OFICIO)
  - Zona geográfica
  - Sistema de puntuación (0.0 - 5.0)
- ✅ Panel de administración personalizado con estadísticas
- ✅ Creación automática de perfiles mediante signals

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
- **Admin:** `http://localhost:8000/admin/`
- **Login con Google:** `http://localhost:8000/accounts/google/login/`

## 📁 Estructura del Proyecto

```
kunfido/
├── kunfido/                 # Configuración del proyecto
│   ├── __init__.py
│   ├── settings.py         # Configuración principal
│   ├── urls.py             # URLs principales
│   ├── asgi.py
│   └── wsgi.py
├── usuarios/                # App de usuarios
│   ├── models.py           # Modelo UserProfile
│   ├── admin.py            # Admin personalizado
│   ├── signals.py          # Señales para crear perfiles
│   ├── views.py
│   └── urls.py
├── templates/
│   ├── admin/
│   │   └── index.html      # Template personalizado del admin
│   └── usuarios/
│       └── home.html       # Página principal
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🔧 Tecnologías

- Python 3.10
- Django 4.2
- django-allauth 0.61.1
- python-decouple 3.8
- SQLite (desarrollo)

## 👥 Modelo de Usuario

El modelo `UserProfile` extiende el usuario de Django con:

- `tipo_rol`: PERSONA, CONSORCIO u OFICIO
- `zona`: Zona geográfica (texto libre)
- `puntuacion`: Float de 0.0 a 5.0
- `fecha_creacion`: Timestamp de creación
- `fecha_actualizacion`: Timestamp de última actualización

## 📝 Notas

- El perfil de usuario se crea automáticamente al registrar un nuevo usuario mediante signals
- La autenticación con email está habilitada por defecto
- El sistema usa email como método de autenticación principal
- En desarrollo, los emails se muestran en consola

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
