# 🔍 Verificaciones de Seguridad Manuales - ShieldScan

## 📋 Guía para Realizar Auditorías de Seguridad Manuales

Esta guía te explica cómo realizar las mismas verificaciones que hace ShieldScan de manera manual, sin utilizar la herramienta.

---

## 🛡️ 1. Verificación de Headers de Seguridad

### **Cómo lo hace ShieldScan:**
El código obtiene los headers HTTP de la respuesta y verifica la presencia de headers críticos de seguridad.

### **Cómo hacerlo manualmente:**

#### **Opción 1: Usando curl**
```bash
# Obtener headers de un sitio
curl -I https://ramguiflex.com

# Obtener headers con más detalle
curl -v -I https://ramguiflex.com
```

#### **Opción 2: Usando herramientas online**
- **Mozilla Observatory**: https://observatory.mozilla.org/
- **SecurityHeaders.com**: https://securityheaders.com/
- **SSL Labs**: https://www.ssllabs.com/ssltest/

#### **Opción 3: Usando navegador (DevTools)**
1. Abrir el sitio en el navegador
2. Presionar F12 para abrir DevTools
3. Ir a la pestaña "Network"
4. Recargar la página
5. Hacer clic en la primera petición
6. Ver la sección "Response Headers"

### **Headers que verificar:**
- `Strict-Transport-Security` (HSTS)
- `X-Content-Type-Options`
- `X-Frame-Options`
- `X-XSS-Protection`
- `Content-Security-Policy`
- `Referrer-Policy`
- `Permissions-Policy`

---

## 🔧 2. Verificación de Acceso a wp-admin

### **Cómo lo hace ShieldScan:**
Hace una petición GET a `/wp-admin/` y analiza la respuesta.

### **Cómo hacerlo manualmente:**

#### **Paso 1: Acceder a wp-admin**
```bash
# En el navegador, ir a:
https://ramguiflex.com/wp-admin/
```

#### **Paso 2: Analizar la respuesta**
- **Si redirige a login**: ✅ CORRECTO (protegido)
- **Si muestra página de login**: ❌ VULNERABILIDAD (accesible públicamente)
- **Si muestra contenido del admin**: ❌ CRÍTICO (sin autenticación)

#### **Paso 3: Verificar con curl**
```bash
curl -I https://ramguiflex.com/wp-admin/
# Verificar el código de respuesta y headers de redirección
```

### **¿Por qué es peligroso?**
- Permite ataques de fuerza bruta
- Identifica usuarios válidos
- Explota vulnerabilidades conocidas en wp-login.php

---

## 📡 3. Verificación de XML-RPC

### **Cómo lo hace ShieldScan:**
Hace una petición GET a `/xmlrpc.php` y analiza la respuesta.

### **Cómo hacerlo manualmente:**

#### **Paso 1: Acceder a xmlrpc.php**
```bash
# En el navegador, ir a:
https://ramguiflex.com/xmlrpc.php
```

#### **Paso 2: Analizar la respuesta**
- **Código 404**: ✅ CORRECTO (no existe/bloqueado)
- **Código 405**: ❌ VULNERABILIDAD (existe, solo acepta POST)
- **Código 200**: ❌ CRÍTICO (completamente accesible)

#### **Paso 3: Verificar con curl**
```bash
curl -I https://ramguiflex.com/xmlrpc.php
# Verificar el código de respuesta
```

### **¿Por qué es peligroso?**
- Ataques de fuerza bruta masivos
- Ataques DDoS amplificados
- Explotación de vulnerabilidades remotas
- Un atacante puede hacer miles de intentos de login por segundo

---

## 🔐 4. Verificación de wp-config.php

### **Cómo lo hace ShieldScan:**
Hace una petición GET a `/wp-config.php` y busca credenciales en el contenido.

### **Cómo hacerlo manualmente:**

#### **Paso 1: Intentar acceder al archivo**
```bash
# En el navegador, ir a:
https://ramguiflex.com/wp-config.php
```

#### **Paso 2: Analizar la respuesta**
- **Código 404/403**: ✅ CORRECTO (protegido)
- **Código 200 sin credenciales**: ❌ VULNERABILIDAD (accesible)
- **Código 200 con credenciales**: ❌ CRÍTICO (información sensible expuesta)

#### **Paso 3: Verificar con curl**
```bash
curl https://ramguiflex.com/wp-config.php
# Buscar en la respuesta: DB_NAME, DB_USER, DB_PASSWORD
```

### **¿Por qué es peligroso?**
- **Con credenciales**: Acceso completo a la base de datos
- **Sin credenciales**: Información sobre configuración del servidor
- Permite a atacantes planificar ataques más sofisticados

---

## 📁 5. Verificación de Listado de Directorios

### **Cómo lo hace ShieldScan:**
Hace peticiones a directorios comunes y busca patrones de listado.

### **Cómo hacerlo manualmente:**

#### **Paso 1: Probar directorios comunes**
```bash
# En el navegador, ir a:
https://ramguiflex.com/wp-content/
https://ramguiflex.com/wp-includes/
https://ramguiflex.com/wp-admin/
https://ramguiflex.com/uploads/
```

#### **Paso 2: Analizar la respuesta**
- **Página de error 404/403**: ✅ CORRECTO (protegido)
- **Lista de archivos**: ❌ VULNERABILIDAD (listado habilitado)
- **Página normal**: ✅ CORRECTO (sin listado)

#### **Paso 3: Buscar indicadores de listado**
En la respuesta HTML, buscar:
- "Index of"
- "Parent Directory"
- "Directory Listing"
- "Apache HTTP Server"
- "Last Modified"
- "Size"
- "Name</th>"

#### **Paso 4: Verificar con curl**
```bash
curl https://ramguiflex.com/wp-content/
# Buscar en la respuesta los indicadores mencionados
```

### **¿Por qué es peligroso?**
- Expone la estructura del sitio
- Identifica archivos sensibles
- Facilita ataques dirigidos
- Puede revelar backups y archivos de configuración

---

## 🔒 6. Verificación de Configuración SSL

### **Cómo lo hace ShieldScan:**
Verifica si la URL usa HTTPS y hace una petición para confirmar.

### **Cómo hacerlo manualmente:**

#### **Paso 1: Verificar el protocolo**
```bash
# Verificar si la URL usa HTTPS
https://ramguiflex.com  # ✅ CORRECTO
http://ramguiflex.com   # ❌ VULNERABILIDAD
```

#### **Paso 2: Verificar el certificado**
```bash
# Usando openssl
openssl s_client -connect ramguiflex.com:443 -servername ramguiflex.com

# Usando curl
curl -I https://ramguiflex.com
```

#### **Paso 3: Usar herramientas online**
- **SSL Labs**: https://www.ssllabs.com/ssltest/
- **SSL Checker**: https://www.sslshopper.com/ssl-checker.html

#### **Paso 4: Verificar en el navegador**
1. Abrir el sitio en el navegador
2. Hacer clic en el candado en la barra de direcciones
3. Verificar que el certificado es válido

### **¿Por qué es peligroso sin HTTPS?**
- Comunicación en texto plano
- Interceptación de credenciales
- Robo de cookies de sesión
- Ataques man-in-the-middle

---

## 🛠️ Herramientas Adicionales para Auditorías Manuales

### **Escáneres de Vulnerabilidades:**
- **Nmap**: `nmap --script vuln https://ramguiflex.com`
- **Nikto**: `nikto -h https://ramguiflex.com`
- **WPScan**: `wpscan --url https://ramguiflex.com`

### **Verificación de Headers:**
- **Header Check**: `curl -I https://ramguiflex.com | grep -i security`
- **SSL Test**: `curl -I https://ramguiflex.com | grep -i ssl`

### **Análisis de WordPress:**
- **WPScan**: Escáner específico para WordPress
- **WordPress Security Scanner**: Herramientas online
- **Plugin Checker**: Verificar plugins vulnerables

---

## 📊 Interpretación de Resultados

### **Estados de Seguridad:**
- **✅ PASS**: Configuración correcta
- **⚠️ WARNING**: Mejora recomendada
- **🚨 CRITICAL**: Vulnerabilidad crítica
- **❌ ERROR**: Error en la verificación

### **Prioridades de Corrección:**
1. **CRÍTICO**: Corregir inmediatamente
2. **WARNING**: Corregir en las próximas 24-48 horas
3. **PASS**: Mantener la configuración actual

---

## 🔧 Comandos Útiles para Auditorías

### **Verificación completa con curl:**
```bash
#!/bin/bash
SITE="https://ramguiflex.com"

echo "=== Verificando Headers de Seguridad ==="
curl -I $SITE | grep -i -E "(strict-transport-security|x-content-type-options|x-frame-options|x-xss-protection|content-security-policy)"

echo "=== Verificando wp-admin ==="
curl -I $SITE/wp-admin/

echo "=== Verificando xmlrpc.php ==="
curl -I $SITE/xmlrpc.php

echo "=== Verificando wp-config.php ==="
curl -I $SITE/wp-config.php

echo "=== Verificando Listado de Directorios ==="
curl -I $SITE/wp-content/
curl -I $SITE/wp-includes/
```

### **Script de verificación automatizada:**
```bash
#!/bin/bash
# Guardar como security_check.sh

SITE=$1
if [ -z "$SITE" ]; then
    echo "Uso: ./security_check.sh https://ejemplo.com"
    exit 1
fi

echo "🔍 Iniciando auditoría de seguridad para: $SITE"
echo "================================================"

# Headers de seguridad
echo "🛡️ Verificando headers de seguridad..."
curl -s -I $SITE | grep -i -E "(strict-transport-security|x-content-type-options|x-frame-options)" || echo "❌ Headers críticos faltantes"

# wp-admin
echo "🔧 Verificando wp-admin..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $SITE/wp-admin/)
if [ "$STATUS" = "200" ]; then
    echo "❌ VULNERABILIDAD: wp-admin accesible"
elif [ "$STATUS" = "302" ] || [ "$STATUS" = "301" ]; then
    echo "✅ wp-admin protegido (redirige)"
else
    echo "✅ wp-admin no accesible"
fi

# xmlrpc.php
echo "📡 Verificando xmlrpc.php..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $SITE/xmlrpc.php)
if [ "$STATUS" = "404" ]; then
    echo "✅ xmlrpc.php no encontrado"
else
    echo "❌ VULNERABILIDAD: xmlrpc.php accesible (código: $STATUS)"
fi

# wp-config.php
echo "🔐 Verificando wp-config.php..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $SITE/wp-config.php)
if [ "$STATUS" = "404" ] || [ "$STATUS" = "403" ]; then
    echo "✅ wp-config.php protegido"
else
    echo "❌ VULNERABILIDAD: wp-config.php accesible (código: $STATUS)"
fi

echo "================================================"
echo "✅ Auditoría completada"
```

---

## 📚 Recursos Adicionales

### **Documentación de Seguridad:**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [WordPress Security](https://wordpress.org/support/article/hardening-wordpress/)
- [Mozilla Security Guidelines](https://infosec.mozilla.org/guidelines/)

### **Herramientas Recomendadas:**
- **Mozilla Observatory**: https://observatory.mozilla.org/
- **SecurityHeaders.com**: https://securityheaders.com/
- **SSL Labs**: https://www.ssllabs.com/ssltest/
- **WPScan**: https://wpscan.com/

---

**Desarrollado con ❤️ por el Equipo de Seguridad y Operaciones**
