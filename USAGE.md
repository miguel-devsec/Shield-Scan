# Guía de Uso - WordPress Security Auditor

## 🚀 Inicio Rápido

### 1. Instalación
```bash
# Clonar el repositorio
git clone <repository-url>
cd wordpress-security-auditor

# Instalar dependencias
python install.py

# O instalar manualmente
python -m pip install -r requirements.txt
```

### 2. Ejecutar la Aplicación
```bash
# Iniciar servidor
python start.py

# O usar uvicorn directamente
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Acceder a la Interfaz
Abrir navegador en: `http://localhost:8000`

## 🔍 Uso de la Interfaz Web

### Paso a Paso
1. **Ingresar URL**: Escribir la URL del sitio WordPress a auditar
2. **Nombre de Empresa** (opcional): Agregar nombre para personalizar el reporte
3. **Iniciar Auditoría**: Hacer clic en el botón para comenzar el análisis
4. **Revisar Resultados**: El sistema generará un reporte completo
5. **Exportar Reporte**: Usar la función de impresión del navegador para guardar como PDF

### Ejemplo de Uso
```
URL: https://mi-sitio-wordpress.com
Empresa: Mi Empresa S.A.S.
```

## 🔧 Uso de la API

### Endpoint Principal
```bash
GET http://localhost:8000/
```
Devuelve la interfaz web.

### Realizar Auditoría
```bash
POST http://localhost:8000/audit
Content-Type: application/json

{
  "url": "https://ejemplo.com",
  "company_name": "Mi Empresa"
}
```

**Respuesta:**
```json
{
  "url": "https://ejemplo.com",
  "company_name": "Mi Empresa",
  "auditor_name": "Equipo de Seguridad y Operaciones",
  "timestamp": "2025-10-11T13:21:08.123456",
  "overall_status": "WARNING",
  "security_headers": {
    "Strict-Transport-Security": {
      "present": true,
      "value": "max-age=31536000",
      "status": "PASS"
    }
  },
  "wp_admin_access": {
    "accessible": false,
    "status": "PASS",
    "message": "wp-admin redirige correctamente al login"
  }
}
```

### Ver Resultados
```bash
GET http://localhost:8000/results?data=<encoded-data>
```

## 📊 Verificaciones Realizadas

### 1. Headers de Seguridad
- **Strict-Transport-Security (HSTS)**: Fuerza conexiones HTTPS
- **X-Content-Type-Options**: Previene MIME type sniffing
- **X-Frame-Options**: Previene clickjacking
- **X-XSS-Protection**: Protección XSS del navegador
- **Content-Security-Policy (CSP)**: Política de seguridad de contenido
- **Referrer-Policy**: Control de información de referrer
- **Permissions-Policy**: Control de permisos del navegador

### 2. Verificaciones WordPress
- **Acceso a wp-admin**: Verifica si el panel está protegido
- **XML-RPC**: Detecta si xmlrpc.php está habilitado
- **wp-config.php**: Verifica exposición de archivos de configuración
- **Listado de Directorios**: Detecta si está habilitado
- **Configuración SSL**: Verifica implementación de HTTPS

## 📄 Interpretación de Resultados

### Estados de Seguridad
- **✅ PASS**: Configuración correcta
- **⚠️ WARNING**: Mejora recomendada
- **🚨 CRITICAL**: Vulnerabilidad crítica
- **❌ ERROR**: Error en la verificación

### Ejemplo de Reporte
```
🔒 Reporte de Auditoría de Seguridad
Sitio: https://ejemplo.com
Cliente: Mi Empresa
Estado: WARNING

🛡️ Headers de Seguridad
✅ Strict-Transport-Security: PASS
✅ X-Content-Type-Options: PASS
⚠️ Content-Security-Policy: WARNING (No configurado)

🔧 Verificaciones WordPress
✅ wp-admin: PASS (Protegido correctamente)
⚠️ xmlrpc.php: WARNING (Habilitado)
✅ wp-config.php: PASS (No expuesto)
```

## 🐳 Uso con Docker

### Construir Imagen
```bash
docker build -t wordpress-auditor .
```

### Ejecutar Contenedor
```bash
docker run -p 8000:8000 wordpress-auditor
```

### Usar Docker Compose
```bash
docker-compose up --build
```

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
# .env
HOST=0.0.0.0
PORT=8000
DEBUG=False
REQUEST_TIMEOUT=30.0
COMPANY_NAME=Mi Empresa
AUDITOR_NAME=Equipo de Seguridad
```

### Personalizar Headers
Editar `config.py` para modificar los headers de seguridad verificados.

### Agregar Verificaciones
Extender la clase `WordPressSecurityChecker` para agregar nuevas verificaciones.

## 📈 Casos de Uso

### 1. Auditoría de Sitio Propio
```bash
# Auditar tu propio sitio
curl -X POST "http://localhost:8000/audit" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://mi-sitio.com", "company_name": "Mi Empresa"}'
```

### 2. Auditoría Masiva
```python
import asyncio
import httpx

async def audit_multiple_sites():
    sites = [
        "https://sitio1.com",
        "https://sitio2.com",
        "https://sitio3.com"
    ]

    async with httpx.AsyncClient() as client:
        for site in sites:
            response = await client.post(
                "http://localhost:8000/audit",
                json={"url": site}
            )
            print(f"Auditoría de {site}: {response.status_code}")

asyncio.run(audit_multiple_sites())
```

### 3. Integración con CI/CD
```yaml
# .github/workflows/security-audit.yml
name: Security Audit
on: [push, pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Security Audit
        run: |
          python start.py &
          sleep 10
          curl -X POST "http://localhost:8000/audit" \
               -H "Content-Type: application/json" \
               -d '{"url": "${{ github.event.repository.html_url }}"}'
```

## 🚨 Solución de Problemas

### Error: "No se pudo conectar al servidor"
```bash
# Verificar que el servidor esté ejecutándose
netstat -an | findstr :8000

# Reiniciar el servidor
python start.py
```

### Error: "Dependencias faltantes"
```bash
# Reinstalar dependencias
python -m pip install -r requirements.txt --force-reinstall
```

### Error: "Timeout en auditoría"
```bash
# Aumentar timeout en config.py
REQUEST_TIMEOUT = 60.0
```

## 📚 Recursos Adicionales

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Guía de Seguridad WordPress](https://wordpress.org/support/article/hardening-wordpress/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Mozilla Observatory](https://observatory.mozilla.org/)

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abrir Pull Request

## 📞 Soporte

- **Issues**: Crear issue en GitHub
- **Documentación**: Ver README.md
- **Email**: security@company.com

---

**Desarrollado con ❤️ por el Equipo de Seguridad y Operaciones**
