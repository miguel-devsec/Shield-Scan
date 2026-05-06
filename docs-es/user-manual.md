# Manual de Usuario — ShieldScan v2.0

## ¿Qué es ShieldScan?

ShieldScan es una herramienta de auditoría de seguridad web que analiza sitios automáticamente en busca de malas configuraciones de seguridad comunes. Introduces una URL y en segundos ShieldScan inspecciona las cabeceras HTTP del sitio, la configuración de WordPress, la configuración SSL/TLS y la exposición de archivos sensibles — luego presenta un informe estructurado con los hallazgos.

---

## 1. Primeros Pasos

### 1.1 Acceder a la aplicación

Abre tu navegador y navega a:

```
http://localhost:3000
```

Verás la página principal de ShieldScan con opciones para **Registrarse** o **Iniciar sesión**.

---

## 2. Crear una Cuenta

### 2.1 Registro

Haz clic en **Registrarse** (o navega a `/register`).

Completa el formulario de registro:

| Campo | Requisitos |
|-------|-----------|
| **Email** | Una dirección de correo válida; se usa como nombre de usuario |
| **Contraseña** | Mínimo 8 caracteres; almacenada con hash bcrypt |

![Formulario de registro](../images/creating_account.png)

Haz clic en **Crear cuenta**. Si tiene éxito, serás redirigido a la página de inicio de sesión.

> **Nota:** Las cuentas nuevas comienzan con el rol `user`. El acceso de administrador debe ser otorgado manualmente por un administrador.

### 2.2 Inicio de Sesión

Haz clic en **Iniciar sesión** (o navega a `/login`).

Introduce tu email y contraseña, luego haz clic en **Entrar**.

![Página de inicio de sesión](../images/login.png)

Si tiene éxito, un token JWT se almacena en el localStorage de tu navegador y serás redirigido al **Dashboard**.

> **Nota de seguridad:** El token expira después de 24 horas. Si ves un mensaje de "sesión expirada", simplemente vuelve a iniciar sesión.

---

## 3. Dashboard

El Dashboard es tu pantalla de inicio después de iniciar sesión. Muestra:

- Un resumen de tus auditorías recientes
- Un botón para iniciar una nueva auditoría
- Indicadores de estado para cada auditoría (Pendiente, En progreso, Completada, Fallida)

![Dashboard de nuevo usuario — sin auditorías aún](../images/new_user_dashboard.png)

### Columnas del Dashboard

| Columna | Descripción |
|---------|-------------|
| **ID** | Identificador único de la auditoría |
| **URL** | La URL objetivo que fue auditada |
| **Empresa** | La etiqueta que asignaste a la auditoría |
| **Estado** | Estado actual de la auditoría |
| **Creada** | Fecha y hora en que se inició la auditoría |
| **Acción** | Enlace para ver el informe completo de auditoría |

![Dashboard con auditorías existentes](../images/user_registered_dashboard.png)

---

## 4. Ejecutar una Auditoría de Seguridad

### 4.1 Iniciar una auditoría

Desde el Dashboard, haz clic en **Nueva auditoría** (o navega a `/audit/new`).

Completa el formulario:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **URL** | El sitio web a auditar | `https://ejemplo.com` |
| **Empresa / Etiqueta** | Un nombre para identificar esta auditoría | `Cliente ACME Corp` |

![Formulario de nueva auditoría](../images/new_scanning.png)

Haz clic en **Iniciar auditoría**.

ShieldScan:
1. Crea un registro de auditoría con estado `pending`
2. Encola la tarea de auditoría para el worker en segundo plano
3. Te redirige a la página de detalle de la auditoría

### 4.2 Ejecución de la auditoría

La auditoría se ejecuta de forma asíncrona — la página mostrará un indicador de carga mientras el worker procesa la solicitud. Una auditoría típica tarda **5–20 segundos** dependiendo del tiempo de respuesta del sitio objetivo.

![Auditoría en progreso](../images/scanning_in_proccess.png)

Ciclo de vida del estado:

```
pending → running → completed
                 ↘ failed
```

La página se actualiza automáticamente hasta que la auditoría alcanza un estado final.

---

## 5. Leer los Resultados de la Auditoría

Cuando la auditoría se completa, la página de resultados muestra un informe estructurado dividido en secciones.

![Informe de resultados de auditoría](../images/scanning_results.png)

### 5.1 Puntuación de Seguridad

La parte superior del informe muestra una puntuación general y un resumen de riesgos indicando cuántos problemas se encontraron en cada nivel de severidad.

### 5.2 Cabeceras HTTP de Seguridad

ShieldScan verifica la presencia y correcta configuración de estas cabeceras:

| Cabecera | Propósito | Resultado |
|----------|-----------|-----------|
| `Strict-Transport-Security` | Fuerza conexiones HTTPS | Presente / Ausente |
| `Content-Security-Policy` | Previene ataques XSS | Presente / Ausente |
| `X-Frame-Options` | Previene clickjacking | Presente / Ausente |
| `X-Content-Type-Options` | Previene MIME-type sniffing | Presente / Ausente |
| `Referrer-Policy` | Controla la información del referrer | Presente / Ausente |
| `Permissions-Policy` | Restringe el acceso a funciones del navegador | Presente / Ausente |

**Cómo leer el resultado:** Una marca verde significa que la cabecera está presente y configurada. Una X roja significa que la cabecera está ausente, lo que representa una mala configuración de seguridad.

### 5.3 Detección de WordPress

Si el sitio objetivo ejecuta WordPress, ShieldScan reporta:

- **Puntuación de confianza**: Qué tan segura es la detección (0–100%)
- **Señales de detección**: Qué indicadores se encontraron (página de login, archivo readme, meta tag generator, etc.)

### 5.4 Verificaciones Específicas de WordPress

Para los sitios WordPress detectados, ShieldScan verifica:

| Verificación | Riesgo si está expuesto | Qué hacer |
|-------------|------------------------|-----------|
| `/wp-admin/` accesible | Interfaz de administración expuesta | Restringir por IP o añadir 2FA |
| `xmlrpc.php` accesible | Fuerza bruta, amplificación DDoS | Deshabilitar si no se necesita |
| `wp-config.php` legible | Credenciales de base de datos expuestas | Corregir permisos de archivo |
| Listado de `wp-content/uploads/` | Contenido del directorio expuesto | Deshabilitar el listado de directorios |

### 5.5 Configuración SSL / HTTPS

| Verificación | Descripción |
|-------------|-------------|
| **HTTPS disponible** | El sitio responde en HTTPS |
| **Redirección HTTP→HTTPS** | Las solicitudes HTTP son redirigidas a HTTPS |
| **Certificado SSL válido** | El certificado es de confianza y no está expirado |

### 5.6 Archivos Sensibles Expuestos

ShieldScan sondea en busca de archivos sensibles comúnmente expuestos:

| Archivo | Riesgo |
|---------|--------|
| `.env` | Variables de entorno expuestas con secretos |
| `.git/config` | Configuración del repositorio git con URLs remotas |
| `composer.json` | Configuración de dependencias PHP |
| `package.json` | Configuración de dependencias Node.js |

Si alguno de estos archivos retorna una respuesta HTTP 200, se marca como **expuesto** — una vulnerabilidad grave.

### 5.7 Listado de Directorios

ShieldScan verifica si el servidor web devuelve un listado de directorio en lugar de un 403 o 404. El listado de directorios expone la estructura de archivos de la aplicación.

---

## 6. Historial de Auditorías

Todas tus auditorías pasadas son visibles en el Dashboard. Puedes:

- **Ver** cualquier auditoría pasada haciendo clic en su ID o en el botón "Ver"
- **Ordenar** por fecha de creación (más reciente primero)
- **Re-auditar** un sitio iniciando una nueva auditoría con la misma URL

Los resultados de auditoría se almacenan de forma permanente en la base de datos — puedes acceder a ellos en cualquier momento.

---

## 7. Funcionalidades de Administrador

Los usuarios con el rol `admin` tienen acceso a capacidades adicionales.

### 7.1 Ver todas las auditorías

Los administradores pueden ver las auditorías de **todos los usuarios** navegando al panel de administración o vía el API en `/audits/admin/all`.

### 7.2 Promover un usuario a administrador

Esto debe realizarlo un administrador existente vía la base de datos:

```bash
docker exec -it shieldscan-db psql -U shieldscan -d shieldscan \
  -c "UPDATE users SET role='admin' WHERE email='usuario@ejemplo.com';"
```

---

## 8. Cerrar Sesión

Haz clic en el botón **Cerrar sesión** en la barra de navegación (o borra el localStorage de tu navegador). Esto elimina tu token JWT del navegador — no se requiere invalidación de sesión en el servidor.

---

## 9. Preguntas Frecuentes

**P: ¿Cuánto tiempo tarda una auditoría?**
R: Típicamente entre 5–20 segundos, dependiendo del tiempo de respuesta del sitio objetivo y cuántas verificaciones se realizan.

**P: ¿Puedo auditar cualquier sitio web?**
R: ShieldScan envía solo solicitudes HTTP HEAD y GET pasivas — las mismas solicitudes que haría tu navegador. Solo audita sitios que sean de tu propiedad o para los que tengas permiso explícito de probar.

**P: ¿Por qué una auditoría aparece como "failed" (fallida)?**
R: Causas comunes: la URL objetivo no está disponible, la conexión excedió el tiempo de espera (> 10 segundos), o el servidor retornó un error. La auditoría se reintentará automáticamente hasta 2 veces antes de marcarse como fallida.

**P: ¿Son privados mis datos?**
R: Sí. Cada usuario solo puede ver sus propias auditorías. Los usuarios administradores pueden ver todas las auditorías.

**P: ¿Puedo exportar los resultados de auditoría?**
R: Actualmente, los resultados están disponibles vía el API en `GET /audits/{id}` en formato JSON. Descárgarlos visitando `http://localhost:8000/audits/{id}` con tu token JWT vía el explorador de API en `/docs`.

**P: La auditoría está atascada en "pending" — ¿qué está mal?**
R: Es posible que el worker de Celery no esté en ejecución. Verificar con:
```bash
docker compose ps worker
docker compose logs worker
```

---

## 10. Acceso a la API

Los usuarios avanzados pueden acceder al API directamente. La documentación interactiva está disponible en:

```
http://localhost:8000/docs
```

![Documentación interactiva del API](../images/api_docs.png)

Para autenticarse en la Swagger UI:
1. `POST /auth/login` con tus credenciales
2. Copiar el `access_token` de la respuesta
3. Hacer clic en **Authorize** en la parte superior derecha
4. Pegar el token en el campo `HTTPBearer`
5. Todas las solicitudes posteriores incluirán tu token
