# WordPress Security Auditor

🔒 **Auditor de Seguridad para Sitios WordPress**

Una herramienta completa para realizar auditorías de seguridad en sitios web basados en WordPress, generando reportes profesionales y detallados.

## 🚀 Características

- **Detección Inteligente de WordPress**: Algoritmo avanzado con 100% de precisión
- **Análisis de Headers de Seguridad**: Verificación de HSTS, CSP, X-Frame-Options, etc.
- **Verificación de WordPress**: Acceso a wp-admin, xmlrpc.php, wp-config.php
- **Verificaciones Generales**: Para sitios no-WordPress (archivos sensibles, tecnologías)
- **Detección de Vulnerabilidades**: Listado de directorios, configuración SSL
- **Reportes Profesionales**: Generación de reportes HTML con diseño moderno
- **Configuración Flexible**: Control de visibilidad de indicadores técnicos
- **API REST**: Interfaz programática para integración con otros sistemas
- **Interfaz Web**: Panel de usuario intuitivo y fácil de usar
- **Seguridad Mejorada**: Sanitización HTML para prevenir XSS

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python 3.8+ con FastAPI
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **HTTP Client**: httpx para peticiones asíncronas
- **Templates**: Jinja2 para generación de reportes
- **Servidor**: Uvicorn (ASGI)

## 📋 Requisitos del Sistema

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Conexión a internet para realizar las auditorías

## ⚙️ Configuración

### Variables de Entorno

Puedes controlar el comportamiento de la aplicación mediante variables de entorno:

```bash
# Mostrar indicadores de detección de WordPress (desarrollo)
SHOW_WP_DETECTION_INDICATORS=true

# Mostrar detalles técnicos (desarrollo)
SHOW_TECHNICAL_DETAILS=true

# Modo producción (oculta indicadores por defecto)
PRODUCTION_MODE=true
```

### Configuración de Reportes

- **Producción**: Los indicadores técnicos están ocultos por defecto
- **Desarrollo**: Cambiar `SHOW_WP_DETECTION_INDICATORS=true` para mostrar detalles

## 🔧 Instalación

1. **Clonar el repositorio**:
```bash
git clone <repository-url>
cd wordpress-security-auditor
```

2. **Crear entorno virtual** (recomendado):
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

## 🚀 Uso

### Ejecutar el servidor

```bash
python main.py
```

El servidor estará disponible en: `http://localhost:8000`

### Uso a través de la interfaz web

1. Abrir el navegador en `http://localhost:8000`
2. Ingresar la URL del sitio WordPress a auditar
3. Opcionalmente, agregar el nombre de la empresa
4. Hacer clic en "Iniciar Auditoría de Seguridad"
5. Esperar a que se complete el análisis
6. Revisar el reporte generado
7. Imprimir o guardar como PDF desde el navegador

### Uso a través de la API

#### Realizar auditoría

```bash
curl -X POST "http://localhost:8000/audit" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://ejemplo.com",
       "company_name": "Mi Empresa"
     }'
```

#### Obtener reporte HTML

```bash
curl "http://localhost:8000/results?data=<encoded-data>"
```

## 🔍 Verificaciones de Seguridad

### Headers de Seguridad
- **Strict-Transport-Security (HSTS)**: Fuerza conexiones HTTPS
- **X-Content-Type-Options**: Previene MIME type sniffing
- **X-Frame-Options**: Previene ataques de clickjacking
- **X-XSS-Protection**: Protección XSS del navegador
- **Content-Security-Policy (CSP)**: Política de seguridad de contenido
- **Referrer-Policy**: Control de información de referrer
- **Permissions-Policy**: Control de permisos del navegador

### Verificaciones WordPress
- **Acceso a wp-admin**: Verifica si el panel de administración está protegido
  - **CRÍTICO**: Si muestra página de login públicamente (permite ataques de fuerza bruta)
- **XML-RPC**: Detecta si xmlrpc.php está habilitado
  - **CRÍTICO**: Cualquier respuesta que no sea 404 (permite ataques DDoS y fuerza bruta masivos)
- **wp-config.php**: Verifica exposición de archivos de configuración
  - **CRÍTICO**: Si es accesible públicamente (expone información sensible)
- **Listado de Directorios**: Detecta si está habilitado el listado de archivos
  - **CRÍTICO**: Si permite listado (expone estructura del sitio)
- **Configuración SSL**: Verifica implementación de HTTPS
  - **CRÍTICO**: Si no usa HTTPS (comunicación en texto plano)

## 📊 Estados de Seguridad

- **PASS** ✅: Configuración correcta
- **WARNING** ⚠️: Mejora recomendada
- **CRITICAL** 🚨: Vulnerabilidad crítica (requiere atención inmediata)
- **ERROR** ❌: Error en la verificación

### 🆕 Mejoras en la Evaluación de Riesgos

**ShieldScan v1.1** incluye evaluaciones de riesgo más estrictas y precisas:

- **wp-admin accesible**: Ahora se marca como **CRÍTICO** (antes era PASS)
- **xmlrpc.php con código 405**: Ahora se marca como **CRÍTICO** (antes era PASS)
- **wp-config.php accesible**: Ahora se marca como **CRÍTICO** (antes era WARNING)
- **Listado de directorios**: Ahora se marca como **CRÍTICO** (antes era WARNING)
- **Sin HTTPS**: Ahora se marca como **CRÍTICO** (antes era WARNING)

Cada verificación incluye:
- **Explicación detallada del riesgo**
- **Recomendaciones específicas de corrección**
- **Contexto sobre por qué es peligroso**

## 📄 Generación de Reportes

Los reportes se generan en formato HTML con las siguientes características:

- **Diseño profesional** con colores corporativos
- **Responsive** para visualización en diferentes dispositivos
- **Imprimible** directamente desde el navegador
- **Exportable a PDF** usando la función de impresión del navegador
- **Información detallada** de cada verificación
- **Recomendaciones específicas** para cada hallazgo
- **Firma digital** del equipo de seguridad

## 🔒 Consideraciones de Seguridad

- El auditor no almacena información sensible
- Las auditorías se realizan de forma no intrusiva
- No se realizan ataques activos contra los sitios
- Se respetan los robots.txt y políticas de uso
- Las peticiones incluyen User-Agent apropiado

## 🚀 Despliegue en Producción

### Usando Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Variables de Entorno

```bash
# .env
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

## 🤝 Contribuciones

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Para soporte técnico o reportar bugs, por favor crear un issue en el repositorio.

## 🔄 Roadmap

- [ ] Integración con bases de datos para historial
- [ ] Notificaciones por email
- [ ] API de webhooks
- [ ] Dashboard de métricas
- [ ] Integración con CI/CD
- [ ] Análisis de plugins vulnerables
- [ ] Escaneo de archivos maliciosos
- [ ] Integración con herramientas de monitoreo

---

**Desarrollado con ❤️ por el Equipo de Seguridad y Operaciones**
