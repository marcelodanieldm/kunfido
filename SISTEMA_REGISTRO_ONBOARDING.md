# Sistema de Registro y Onboarding - Kunfido

## Documentación Técnica Completa

### 📋 Resumen

Se ha implementado un sistema completo de registro y onboarding para Kunfido que incluye:

- ✅ Autenticación con Google (OAuth)
- ✅ Autenticación tradicional con Email/Password
- ✅ Middleware de onboarding automático
- ✅ Flujo de selección de roles personalizado
- ✅ Formularios dinámicos según el tipo de usuario
- ✅ Validación en tiempo real con JavaScript
- ✅ Diseño moderno con Tailwind CSS
- ✅ Barra de progreso visual
- ✅ Redirección inteligente según el rol

---

## 🎯 Componentes Implementados

### 1. Configuración de Django-Allauth

**Archivo modificado:** `kunfido/settings.py`

```python
# Configuración de allauth
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# Redirect URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/role-selection/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/role-selection/'

# Proveedor de Google OAuth
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID', default=''),
            'secret': config('GOOGLE_CLIENT_SECRET', default=''),
            'key': ''
        }
    }
}
```

**Configuración requerida en archivo `.env`:**
```
GOOGLE_CLIENT_ID=tu_client_id_de_google
GOOGLE_CLIENT_SECRET=tu_client_secret_de_google
```

### 2. Middleware de Onboarding

**Archivo modificado:** `usuarios/middleware.py`

El middleware verifica automáticamente si un usuario autenticado ha completado su perfil:

- Si el usuario no tiene `tipo_rol` asignado → redirige a `/role-selection/`
- Excepciones: rutas de administración, cuentas y assets estáticos
- Crea el perfil automáticamente si no existe

**Rutas exentas:**
- `/role-selection/`
- `/onboarding-form/`
- `/logout/`
- `/admin/*`
- `/accounts/*`
- `/static/*`
- `/media/*`

### 3. Vistas Implementadas

**Archivo modificado:** `usuarios/views.py`

#### a) `signup_choice(request)`
- Vista pública para mostrar opciones de registro
- Redirige a dashboard si ya está autenticado
- Template: `usuarios/signup_choice.html`

#### b) `role_selection(request)` [MEJORADA]
- Vista para seleccionar el tipo de rol (Persona, Consorcio, Oficio)
- Verifica si ya completó el onboarding
- Crea perfil si no existe
- Template: `usuarios/role_selection.html`

#### c) `onboarding_form(request)` [MEJORADA]
- Formulario dinámico según el rol seleccionado
- Validación de campos requeridos por rol
- Crea wallet inicial al completar el perfil
- Lista de rubros para profesionales de oficio
- Template: `usuarios/onboarding_form.html`

#### d) `get_dashboard_url(user)` [EXISTENTE]
- Función auxiliar que retorna la URL del dashboard según el rol
- Redirige a:
  - `/dashboard/persona/` para PERSONA
  - `/dashboard/consorcio/` para CONSORCIO
  - `/dashboard/oficio/` para OFICIO

### 4. URLs Configuradas

**Archivo modificado:** `usuarios/urls.py`

```python
# Nueva ruta agregada
path('signup/', views.signup_choice, name='signup_choice'),

# Rutas existentes de onboarding
path('role-selection/', views.role_selection, name='role_selection'),
path('onboarding-form/', views.onboarding_form, name='onboarding_form'),
```

---

## 🎨 Templates Implementados

### 1. signup_choice.html

**Ubicación:** `templates/usuarios/signup_choice.html`

**Características:**
- ✅ Diseño moderno con Tailwind CSS
- ✅ Botón grande "Continuar con Google" con logo
- ✅ Formulario minimalista para Email/Password
- ✅ Divisor visual "O con tu email"
- ✅ Validación en tiempo real con JavaScript
- ✅ Colores de seguridad: Azul (#1e3a8a) y Blanco
- ✅ Mensajes de error sin recargar página
- ✅ Animaciones suaves

**Validaciones JavaScript:**
- Email: formato válido en tiempo real
- Password: mínimo 8 caracteres
- Confirmación: contraseñas coincidentes

### 2. role_selection.html

**Ubicación:** `templates/usuarios/role_selection.html`

**Características:**
- ✅ 3 tarjetas interactivas con efectos hover
- ✅ Íconos diferenciados por rol:
  - 👤 Persona (Usuario individual)
  - 🏢 Consorcio (Edificio)
  - 🔧 Oficio (Herramientas)
- ✅ Animación de elevación al hacer hover
- ✅ Selección visual con borde destacado
- ✅ Checkmark al seleccionar
- ✅ Botón "Continuar" deshabilitado hasta seleccionar
- ✅ Barra de progreso: 33%

**Tarjetas incluyen:**
- Título del rol
- Descripción breve
- Lista de beneficios con íconos
- Efecto hover con transformación

### 3. onboarding_form.html

**Ubicación:** `templates/usuarios/onboarding_form.html`

**Características:**
- ✅ Formulario dinámico según rol seleccionado
- ✅ Validación en tiempo real con JavaScript
- ✅ Campos específicos por rol
- ✅ Barra de progreso: 66%
- ✅ Animaciones de entrada (fade-in)
- ✅ Validación de CUIT con formato automático
- ✅ Validación de teléfono
- ✅ Botón "Volver" para cambiar de rol

**Campos por Rol:**

**CONSORCIO:**
- Dirección del Edificio (texto)
- Matrícula de Administrador (texto)

**OFICIO:**
- Rubro/Especialidad (select dinámico)
  - Plomería
  - Electricidad
  - Pintura
  - Albañilería
  - Carpintería
  - Herrería
  - Gasista
  - Jardinería
  - Aire Acondicionado
  - Cerrajería
  - Techista
  - Otro
- Zona de Trabajo (texto)
- CUIT/CUIL (texto con formato automático)

**PERSONA:**
- Barrio (texto)
- Teléfono (texto)

### 4. base.html

**Archivo modificado:** `templates/base.html`

**Mejoras:**
- ✅ Tailwind CSS incluido vía CDN
- ✅ Estilos para barra de progreso
- ✅ Compatibilidad con Bootstrap existente
- ✅ CSS para validaciones y animaciones

---

## 🔄 Flujo de Usuario Completo

```
1. INICIO
   ├─ Usuario no autenticado
   │  └─ Landing Page (/)
   │     └─ Click "Registrarse"
   │        └─ signup_choice.html
   │           ├─ Opción A: Continuar con Google
   │           │  └─ OAuth Google → Login automático
   │           │     └─ Middleware detecta perfil vacío
   │           │        └─ Redirige a role_selection
   │           │
   │           └─ Opción B: Email/Password
   │              └─ Formulario de registro
   │                 └─ django-allauth procesa
   │                    └─ ACCOUNT_SIGNUP_REDIRECT_URL
   │                       └─ role_selection
   │
2. SELECCIÓN DE ROL
   └─ role_selection.html
      ├─ Usuario selecciona: PERSONA, CONSORCIO u OFICIO
      └─ Guarda tipo_rol en UserProfile
         └─ Redirige a onboarding_form
         
3. FORMULARIO DE ONBOARDING
   └─ onboarding_form.html
      ├─ Muestra campos dinámicos según rol
      ├─ Usuario completa información
      ├─ Validación en tiempo real
      └─ Al enviar:
         ├─ Guarda datos en UserProfile
         ├─ Crea Wallet inicial (1000 USDC)
         └─ get_dashboard_url(user)
            └─ Redirige al dashboard específico

4. DASHBOARD
   ├─ PERSONA → /dashboard-home/ (vista cliente)
   ├─ CONSORCIO → /dashboard-home/ (vista consorcio)
   └─ OFICIO → /dashboard-home/ (vista profesional)
```

---

## 🛡️ Seguridad y Validaciones

### Validaciones Backend (Django)

1. **Middleware OnboardingMiddleware:**
   - Verifica autenticación
   - Verifica existencia de perfil
   - Verifica tipo_rol asignado
   - Redirige automáticamente

2. **Vista role_selection:**
   - Valida rol en ['PERSONA', 'CONSORCIO', 'OFICIO']
   - Crea perfil si no existe
   - Verifica completitud del onboarding

3. **Vista onboarding_form:**
   - Campos requeridos según rol
   - Validación de campos no vacíos
   - Creación de wallet inicial

### Validaciones Frontend (JavaScript)

1. **signup_choice.html:**
   - Email: regex `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`
   - Password: mínimo 8 caracteres
   - Confirmación: passwords idénticas
   - Validación en eventos: `blur`, `input`

2. **role_selection.html:**
   - Obligatorio seleccionar un rol
   - Botón deshabilitado hasta selección
   - Prevención de submit sin selección

3. **onboarding_form.html:**
   - CUIT: formato automático `XX-XXXXXXXX-X`
   - Teléfono: mínimo 8 dígitos
   - Campos requeridos marcados visualmente
   - Animación de shake en errores

---

## 🎨 Diseño UX/UI

### Paleta de Colores

- **Azul Primario:** `#1e3a8a` (Seguridad, confianza)
- **Azul Claro:** `#3b82f6` (Accesibilidad)
- **Blanco:** `#ffffff` (Limpieza, profesionalismo)
- **Gris:** `#f8f9fa` (Fondo neutro)
- **Verde Acento:** `#10B981` (Éxito, confirmación)

### Efectos y Animaciones

1. **Hover Effects:**
   - Tarjetas: `translateY(-8px)`
   - Botones: `scale(1.05)`
   - Sombras dinámicas

2. **Validaciones:**
   - Shake animation en errores
   - Fade-in en mensajes
   - Cambio de color de borde

3. **Transiciones:**
   - Duración: 0.3s ease
   - Transform smooth
   - Opacity gradual

### Barra de Progreso

- Posición: Fixed top
- Alto: 4px
- Gradiente: `from-blue-900 to-blue-500`
- Animación: width transition 0.3s

**Estados:**
- Role Selection: 33.33%
- Onboarding Form: 66.67%
- Dashboard: 100% (completo)

---

## 🔧 Configuración Adicional Requerida

### 1. Google OAuth Setup

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un proyecto nuevo
3. Habilitar Google+ API
4. Crear credenciales OAuth 2.0
5. Configurar URLs autorizadas:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
6. Copiar Client ID y Client Secret al archivo `.env`

### 2. Archivo .env

Crear archivo `.env` en la raíz del proyecto:

```bash
SECRET_KEY=tu_secret_key_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google OAuth
GOOGLE_CLIENT_ID=tu_client_id_aqui
GOOGLE_CLIENT_SECRET=tu_client_secret_aqui

# Email (opcional para desarrollo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 3. Crear Site en Django Admin

```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site
Site.objects.update_or_create(
    id=1,
    defaults={'domain': 'localhost:8000', 'name': 'Kunfido Dev'}
)
```

---

## 📝 Testing Manual

### Test 1: Registro con Email/Password

1. Ir a `/signup/`
2. Completar email y contraseña
3. Verificar validación en tiempo real
4. Submit → Debería redirigir a `/role-selection/`
5. Seleccionar un rol
6. Completar formulario de onboarding
7. Verificar redirección al dashboard correcto

### Test 2: Registro con Google

1. Ir a `/signup/`
2. Click en "Continuar con Google"
3. Autorizar en Google
4. Debería redirigir a `/role-selection/`
5. Continuar proceso normal

### Test 3: Middleware de Onboarding

1. Registrarse pero NO completar rol
2. Intentar acceder a `/dashboard-home/`
3. Debería redirigir automáticamente a `/role-selection/`

### Test 4: Validaciones JavaScript

1. En signup: ingresar email inválido → ver error
2. En signup: contraseña < 8 caracteres → ver error
3. En onboarding (Oficio): CUIT sin formato → formateo automático
4. En role-selection: intentar continuar sin selección → botón deshabilitado

---

## 🚀 Comandos Útiles

```bash
# Crear migraciones si es necesario
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver

# Recopilar archivos estáticos
python manage.py collectstatic
```

---

## 📊 Estructura de Datos

### Modelo UserProfile

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tipo_rol = models.CharField(max_length=20, choices=TIPO_ROL_CHOICES, default='PERSONA')
    zona = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    rubro = models.CharField(max_length=100, blank=True, null=True)
    cuit = models.CharField(max_length=13, blank=True, null=True)
    matricula = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    puntuacion = models.FloatField(default=0.0)
    penalizaciones_acumuladas = models.PositiveIntegerField(default=0)
```

**Campos por Rol:**

| Rol | Campos Utilizados |
|-----|------------------|
| PERSONA | zona, telefono |
| CONSORCIO | direccion, matricula, zona |
| OFICIO | rubro, cuit, zona |

---

## 🐛 Troubleshooting

### Error: "Site matching query does not exist"

**Solución:**
```python
python manage.py shell
from django.contrib.sites.models import Site
Site.objects.create(id=1, domain='localhost:8000', name='Kunfido')
```

### Error: Google OAuth no funciona

**Verificar:**
1. GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET en .env
2. URLs de callback en Google Cloud Console
3. Google+ API habilitada
4. Site ID = 1 en Django Admin

### Middleware redirige en loop

**Verificar:**
1. Rutas exentas en `OnboardingMiddleware`
2. Usuario tiene perfil creado
3. tipo_rol no está vacío

---

## ✅ Checklist de Implementación

- [x] Django-allauth configurado
- [x] Google OAuth configurado
- [x] Middleware de onboarding implementado
- [x] Vista signup_choice creada
- [x] Vista role_selection mejorada
- [x] Vista onboarding_form mejorada
- [x] Template signup_choice.html con Tailwind
- [x] Template role_selection.html con efectos hover
- [x] Template onboarding_form.html dinámico
- [x] Validación JavaScript en tiempo real
- [x] Barra de progreso visual
- [x] Función get_dashboard_url(user)
- [x] Colores de seguridad (Azul #1e3a8a)
- [x] URLs configuradas
- [x] Documentación completa

---

## 📞 Contacto y Soporte

Para dudas o problemas con la implementación, revisar:

1. Logs de Django: `python manage.py runserver --verbosity=2`
2. Consola del navegador (F12) para errores JavaScript
3. Django Admin para verificar datos de usuarios

---

**Fecha de Implementación:** Diciembre 2025  
**Versión:** 1.0  
**Framework:** Django 4.2  
**Estilo:** Tailwind CSS + Bootstrap 5  
**Autor:** Senior Fullstack Developer

---

## 🎉 Sistema Listo para Producción

El sistema de registro y onboarding está completamente implementado y listo para usar. Todos los requerimientos técnicos y de UX han sido cumplidos.
