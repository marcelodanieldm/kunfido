# 🚀 Guía Rápida: Sistema de Registro y Onboarding

## Inicio Rápido

### 1. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Seguridad
SECRET_KEY=tu_secret_key_django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google OAuth (obtener en https://console.cloud.google.com/)
GOOGLE_CLIENT_ID=tu_client_id_de_google.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_client_secret_de_google

# Email (desarrollo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 2. Instalar Dependencias

```bash
pip install django-allauth python-decouple
```

### 3. Ejecutar Migraciones

```bash
python manage.py migrate
```

### 4. Crear Site en Django

```bash
python manage.py shell
```

Dentro del shell:
```python
from django.contrib.sites.models import Site
Site.objects.update_or_create(
    id=1,
    defaults={'domain': 'localhost:8000', 'name': 'Kunfido Local'}
)
exit()
```

### 5. Ejecutar Servidor

```bash
python manage.py runserver
```

---

## 🔗 URLs Disponibles

| URL | Descripción |
|-----|-------------|
| `/` | Landing page |
| `/signup/` | Página de registro (Google o Email) |
| `/accounts/login/` | Login (django-allauth) |
| `/accounts/signup/` | Registro directo (alternativo) |
| `/role-selection/` | Selección de rol (automático después de registro) |
| `/onboarding-form/` | Formulario de onboarding dinámico |
| `/dashboard-home/` | Dashboard según rol |

---

## 👥 Roles Disponibles

### 1. **PERSONA** (Propietario/Inquilino)
- Campos: Barrio, Teléfono
- Dashboard: Vista de cliente
- Funciones: Contratar servicios

### 2. **CONSORCIO** (Administrador)
- Campos: Dirección del Edificio, Matrícula
- Dashboard: Vista administrativa
- Funciones: Gestión de múltiples servicios

### 3. **OFICIO** (Profesional)
- Campos: Rubro, Zona, CUIT
- Dashboard: Vista de profesional
- Funciones: Recibir trabajos, enviar propuestas

---

## 🧪 Testing

### Registrar Usuario de Prueba

**Opción 1: Email/Password**
1. Ir a `http://localhost:8000/signup/`
2. Completar email y contraseña (mín. 8 caracteres)
3. Click en "Crear Cuenta"
4. Seleccionar rol
5. Completar formulario

**Opción 2: Google OAuth**
1. Ir a `http://localhost:8000/signup/`
2. Click en "Continuar con Google"
3. Autorizar con cuenta de Google
4. Seleccionar rol
5. Completar formulario

---

## 🎨 Características UX

✅ Validación en tiempo real (JavaScript)  
✅ Mensajes de error sin recargar página  
✅ Barra de progreso visual (33% → 66% → 100%)  
✅ Efectos hover en tarjetas  
✅ Animaciones suaves  
✅ Diseño responsive (Tailwind CSS)  
✅ Colores de seguridad (Azul #1e3a8a)

---

## 🛡️ Seguridad

- Middleware automático verifica onboarding
- No se puede acceder al dashboard sin completar perfil
- Validaciones backend y frontend
- CSRF protection activado
- Emails únicos obligatorios

---

## 📝 Notas Importantes

1. **Google OAuth:** Requiere configurar credenciales en Google Cloud Console
2. **Site ID:** Debe ser exactamente `1` para que allauth funcione
3. **Middleware:** Redirige automáticamente a onboarding si falta información
4. **Wallet:** Se crea automáticamente al completar onboarding (1000 USDC inicial)

---

## 🐛 Problemas Comunes

### Error: "No module named 'allauth'"
```bash
pip install django-allauth
```

### Error: "Site matching query does not exist"
Ejecutar script de creación de Site (ver paso 4)

### Google OAuth no funciona
- Verificar variables en `.env`
- Verificar URLs de callback en Google Console
- Verificar que Site ID = 1

---

## 📚 Documentación Completa

Para documentación técnica detallada, ver:  
**→ `SISTEMA_REGISTRO_ONBOARDING.md`**

---

## ✨ Flujo Simplificado

```
Registro → Selección de Rol → Formulario Dinámico → Dashboard
```

**¡El sistema está listo para usar!** 🎉
