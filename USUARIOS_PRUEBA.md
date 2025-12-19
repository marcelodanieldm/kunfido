# 🔐 Usuarios de Prueba - Kunfido

## Credenciales para Login (Email + Password)

Todos los usuarios ya están creados y tienen sus perfiles configurados. **No necesitas Google Account** para hacer login.

---

### 👑 **SUPERUSUARIO ADMIN**

```
Email:    admin@kunfido.com
Password: admin123
```

**Acceso:**
- 🌐 Landing Page: Haz clic en el ícono de escudo en el footer (modal rojo)
- 🔗 URL Directa: http://127.0.0.1:8000/admin/

**Permisos:** Acceso completo al panel de administración de Django

---

### 1️⃣ **CLIENTE (Persona)**

```
Email:    cliente@kunfido.com
Password: cliente123
```

**Detalles:**
- 👤 Rol: PERSONA (Usuario cliente)
- 📍 Zona: Palermo, CABA
- 📞 Teléfono: +54 9 11 1234-5678
- 💰 Balance: 1000.00 USDC
- ⭐ Puntuación: 4.8/5.0

**Dashboard:** http://127.0.0.1:8000/dashboard/

---

### 2️⃣ **PROFESIONAL (Oficio)**

```
Email:    profesional@kunfido.com
Password: profesional123
```

**Detalles:**
- 🔧 Rol: OFICIO (Profesional)
- 🛠️ Rubro: PLOMERIA
- 📍 Zona: Recoleta, CABA
- 🆔 CUIT: 20-12345678-9
- 💰 Balance: 1000.00 USDC
- ⭐ Puntuación: 4.9/5.0

**Dashboard:** http://127.0.0.1:8000/dashboard/

---

### 3️⃣ **CONSORCIO**

```
Email:    consorcio@kunfido.com
Password: consorcio123
```

**Detalles:**
- 🏢 Rol: CONSORCIO (Administrador de edificio)
- 🏠 Dirección: Av. Belgrano 1234, CABA
- 📍 Zona: Belgrano, CABA
- 📜 Matrícula: MAT-12345
- 💰 Balance: 1000.00 USDC
- ⭐ Puntuación: 4.7/5.0

**Dashboard:** http://127.0.0.1:8000/dashboard/

---

## 🚀 Formas de Iniciar Sesión

### 📱 **Usuarios Regulares (Cliente, Profesional, Consorcio)**

**Opción 1: Desde la Landing Page**
1. Ve a: http://127.0.0.1:8000/
2. Haz clic en el botón **"Iniciar Sesión"** en la barra de navegación superior
3. Se abrirá un modal azul con dos opciones:
   - 🔵 Login con Google
   - 📧 Login con Email + Password ← **Usa esta opción**
4. Ingresa las credenciales de cualquiera de los 3 usuarios regulares
5. Serás redirigido a tu dashboard personalizado según tu rol

**Opción 2: URL Directa**
1. Ve directamente a: http://127.0.0.1:8000/accounts/login/
2. Ingresa Email + Password
3. Haz clic en "Iniciar Sesión"

---

### 👑 **Superusuario Admin**

**Opción 1: Acceso Discreto desde Landing Page**
1. Ve a: http://127.0.0.1:8000/
2. Baja hasta el **footer** de la página
3. Busca el ícono de escudo pequeño (muy discreto, opacidad 30%)
4. Haz hover sobre el ícono para verlo mejor
5. Haz clic en el ícono de escudo
6. Se abrirá un modal rojo exclusivo para administradores
7. Ingresa: admin@kunfido.com / admin123
8. Serás redirigido al panel de administración de Django

**Opción 2: URL Directa**
1. Ve directamente a: http://127.0.0.1:8000/admin/
2. Ingresa las credenciales de admin
3. Acceso inmediato al admin panel

---

## 🔄 Scripts de Gestión

### Crear usuarios nuevos (si no existen)
```bash
python crear_usuarios_prueba.py
```

### Actualizar usuarios existentes
```bash
python actualizar_usuarios_prueba.py
```

Ambos scripts configuran automáticamente:
- ✅ Roles correctos para cada usuario
- ✅ Perfiles con todos los campos requeridos
- ✅ Wallets con balance inicial de 1000 USDC
- ✅ Puntuaciones iniciales

---

## ⚠️ Notas Importantes

1. **Contraseñas:** Todas las contraseñas son simples (usuario123) para facilitar las pruebas. En producción usa contraseñas seguras.

2. **No requiere Google:** Todos los usuarios funcionan con email/password. Google OAuth es opcional.

3. **Onboarding completado:** Todos los usuarios ya tienen sus perfiles configurados, por lo que no pasarán por el flujo de onboarding al hacer login.

4. **Wallets creados:** Cada usuario tiene su wallet con 1000 USDC de saldo inicial.

5. **Diferencias entre roles:**
   - **PERSONA:** Ve el dashboard de cliente (puede contratar servicios)
   - **OFICIO:** Ve el dashboard de profesional (puede ofrecer servicios)
   - **CONSORCIO:** Ve el dashboard de consorcio (puede gestionar edificios)
   - **ADMIN:** Acceso completo al panel de administración de Django

---

## 🧪 Flujo de Prueba Recomendado

1. **Prueba el login de Admin:**
   - Usa el modal discreto del footer o ve directo a /admin/
   - Verifica que tienes acceso al panel de Django

2. **Prueba cada rol de usuario:**
   - Login con cliente@kunfido.com
   - Observa el dashboard de PERSONA
   - Logout y login con profesional@kunfido.com
   - Observa el dashboard de OFICIO
   - Logout y login con consorcio@kunfido.com
   - Observa el dashboard de CONSORCIO

3. **Verifica las diferencias:**
   - Cada dashboard debe mostrar contenido diferente según el rol
   - Verifica que los wallets muestran el balance correcto
   - Verifica que la navegación se adapta al rol del usuario

---

## 🐛 Solución de Problemas

**No puedo hacer login:**
- Verifica que estés usando el email completo (con @kunfido.com)
- Las contraseñas son case-sensitive
- Ejecuta `python actualizar_usuarios_prueba.py` para resetear los usuarios

**Usuario no tiene perfil completo:**
- Ejecuta `python actualizar_usuarios_prueba.py` para actualizar perfiles

**Admin no tiene permisos:**
- El usuario admin debe tener is_superuser=True e is_staff=True
- Ejecuta el script de actualización para corregir

---

**¡Todo listo para probar el sistema sin necesidad de Google Account!** 🎉
