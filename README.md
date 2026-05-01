# ShieldScan v2.0 — Auditor de Seguridad Web

Plataforma de auditoría de seguridad para sitios WordPress y aplicaciones web generales, construida con **arquitectura de microservicios** e integrada en un pipeline **DevSecOps completo**.

> La aplicación es el vehículo; el pipeline DevSecOps es el producto.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        Usuario (Browser)                     │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP :3000
┌────────────────────────────▼────────────────────────────────┐
│              Frontend — React SPA (nginx)                    │
│              servicios/frontend  · puerto 3000               │
│              Vite + React Router + Axios                     │
└────────────────────────────┬────────────────────────────────┘
                             │ /api/ → proxy
┌────────────────────────────▼────────────────────────────────┐
│              API — FastAPI (Python 3.11)                     │
│              servicios/api  · puerto 8000                    │
│              JWT Auth · REST · Celery dispatch               │
└──────────────┬─────────────────────────┬────────────────────┘
               │                         │
   ┌───────────▼──────────┐   ┌──────────▼──────────┐
   │  PostgreSQL 16        │   │  Redis 7             │
   │  Usuarios + Auditorías│   │  Broker de mensajes  │
   └───────────────────────┘   └──────────┬──────────┘
                                          │ Celery queue
                            ┌─────────────▼──────────────┐
                            │  Worker — Celery (Python)   │
                            │  servicios/worker           │
                            │  Auditor de seguridad async │
                            └─────────────┬──────────────┘
                                          │ HTTP (httpx)
                            ┌─────────────▼──────────────┐
                            │    Sitio Web Objetivo       │
                            └────────────────────────────┘
```

### Componentes

| Servicio | Tecnología | Función |
|---------|-----------|---------|
| **frontend** | React 18 + Vite + nginx | SPA — Login, dashboard, resultados |
| **api** | FastAPI + SQLAlchemy | API REST, autenticación JWT, roles |
| **worker** | Celery + httpx | Ejecución asíncrona de auditorías |
| **db** | PostgreSQL 16 | Persistencia de usuarios y auditorías |
| **redis** | Redis 7 | Broker de mensajes para Celery |

---

## Inicio Rápido

### Prerrequisitos

- Docker Desktop
- Docker Compose v2

### 1. Clonar el repositorio

```bash
git clone https://github.com/<tu-usuario>/shieldscan.git
cd shieldscan
```

### 2. Configurar variables de entorno

```bash
cp env.example .env
# Editar .env con valores seguros para producción
```

### 3. Levantar todos los servicios

```bash
docker compose up --build
```

| Servicio | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API + docs | http://localhost:8000/docs |

### 4. Crear usuario administrador

Regístrate normalmente en la interfaz web y luego promuévete a admin:

```bash
docker exec -it shieldscan-db psql -U shieldscan -d shieldscan \
  -c "UPDATE users SET role='admin' WHERE email='tu@email.com';"
```

---

## Variables de Entorno

| Variable | Descripción | Default |
|---------|-------------|---------|
| `DB_PASSWORD` | Contraseña de PostgreSQL | `shieldscan` |
| `SECRET_KEY` | Clave de firma JWT | *(cambiar en producción)* |
| `DATABASE_URL` | URL de conexión a PostgreSQL | construida desde `DB_PASSWORD` |
| `REDIS_URL` | URL del broker Redis | `redis://redis:6379/0` |

---

## API Endpoints

### Autenticación

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/auth/register` | Crear cuenta de usuario |
| `POST` | `/auth/login` | Iniciar sesión → retorna JWT |
| `GET` | `/auth/me` | Perfil del usuario autenticado |

### Auditorías

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/audits/` | Iniciar nueva auditoría (async) |
| `GET` | `/audits/` | Listar auditorías del usuario |
| `GET` | `/audits/{id}` | Ver resultado de una auditoría |
| `GET` | `/audits/admin/all` | Ver todas las auditorías *(admin)* |

La auditoría se encola en Redis y el worker la ejecuta de forma asíncrona. El resultado queda guardado en PostgreSQL.

### Verificaciones de seguridad

- Headers HTTP de seguridad (HSTS, CSP, X-Frame-Options, etc.)
- Detección de WordPress con score de confianza
- Acceso a `wp-admin`, `xmlrpc.php`, `wp-config.php`
- Listado de directorios
- Configuración SSL/HTTPS
- Archivos sensibles expuestos (`.env`, `.git/config`, etc.)

---

## Pipeline DevSecOps (GitHub Actions)

El pipeline completo se define en [`.github/workflows/devsecops.yml`](.github/workflows/devsecops.yml) y cubre las 5 fases del ciclo DevSecOps:

| Fase | Job | Herramienta | Descripción |
|------|-----|-------------|-------------|
| **Fase 2 — Code** | `secrets-scan` | Gitleaks | Detección de secretos en el historial git |
| **Fase 2 — Code** | `sast` | Semgrep + Bandit | Análisis estático de seguridad (Python) |
| **Fase 2 — Code** | `sca` | Trivy (fs) | Análisis de dependencias vulnerables |
| **Fase 3 — Build** | `build-and-scan` | Trivy (image) | Escaneo de imágenes Docker — **falla en CVEs CRITICAL** |
| **Fase 4 — Test** | `unit-tests` | Pytest | Tests unitarios del API con coverage |
| **Fase 4 — Test** | `dast` | OWASP ZAP | Análisis dinámico contra staging *(solo en main)* |
| **Fase 5 — Release** | `iac-scan` | Checkov | Escaneo de Dockerfiles e IaC |
| **Fase 5 — Release** | `push-images` | Docker Hub | Push semántico `vYYYYMMDD-HHMM` + `latest` |

### Secrets requeridos en GitHub

Configurar en **Settings → Secrets and variables → Actions**:

| Secret | Valor |
|--------|-------|
| `DOCKER_HUB_USER` | `migueldevsec` |
| `DOCKER_HUB_PASSWORD` | Token de acceso de Docker Hub |

---

## Imágenes Docker

Las imágenes se publican automáticamente en Docker Hub al hacer push a `main`:

```
migueldevsec/shieldscan-api:latest
migueldevsec/shieldscan-worker:latest
migueldevsec/shieldscan-frontend:latest
```

Todas las imágenes:
- Basadas en imágenes `slim`/`alpine`
- Ejecutan con **usuario no-root**
- Incluyen `HEALTHCHECK`

---

## Seguridad

### Modelado de amenazas

El análisis STRIDE completo y los diagramas de flujo de datos (DFD nivel 0 y nivel 1) están documentados en [`docs/threat-model.md`](docs/threat-model.md).

### Controles implementados

- Contraseñas hasheadas con **bcrypt** (salt aleatorio por contraseña)
- Tokens **JWT** con expiración configurable (24h por defecto)
- Todos los contenedores corren como **usuario no-root**
- Secretos únicamente via **variables de entorno** — nunca hardcodeados
- PostgreSQL y Redis **no expuestos** al host (solo red Docker interna)
- Protección **CORS** en la API
- Sanitización de salida HTML para prevenir **XSS**

---

## Infraestructura y Orquestación

### Desarrollo local
```bash
docker compose up --build
```

### Producción — Docker Swarm

```bash
# Crear secrets en el swarm
echo "password_segura" | docker secret create db_password -
echo "jwt_secret_key"  | docker secret create secret_key -

# Desplegar el stack
docker stack deploy -c orquestacion/docker-swarm.yml shieldscan
```

### Despliegue automático — Ansible

```bash
ansible-playbook -i infraestructura/ansible/inventory.yml \
                 infraestructura/ansible/playbook.yml \
                 -e "db_password=... secret_key=... docker_hub_password=..."
```

---

## Estructura del Repositorio

```
ShieldScan/
├── .github/
│   └── workflows/
│       └── devsecops.yml       # Pipeline DevSecOps completo
├── docs/
│   └── threat-model.md         # Modelado de amenazas STRIDE
├── infraestructura/
│   └── ansible/                # Playbook de despliegue
├── orquestacion/
│   └── docker-swarm.yml        # Stack para Docker Swarm
├── servicios/
│   ├── api/                    # FastAPI — API Gateway + Auth
│   ├── worker/                 # Celery — Worker asíncrono
│   └── frontend/               # React SPA + nginx
├── docker-compose.yml          # Entorno de desarrollo completo
└── env.example                 # Plantilla de variables de entorno
```

---

## Hooks Pre-commit (Seguridad Local)

Los hooks de pre-commit ejecutan verificaciones de seguridad automáticamente en tu máquina **antes de cada `git commit`**, bloqueando el commit si detectan problemas.

### Instalación (una sola vez)

```bash
pip install pre-commit
pre-commit install
```

### Hooks configurados (`.pre-commit-config.yaml`)

| Hook | Herramienta | Qué detecta |
|------|-------------|-------------|
| `gitleaks` | Gitleaks | Secretos, tokens y claves API en el código |
| `bandit` | Bandit | Vulnerabilidades de seguridad en Python |
| `detect-private-key` | pre-commit | Claves privadas hardcodeadas |
| `check-added-large-files` | pre-commit | Archivos > 500 KB accidentales |
| `check-yaml` / `check-json` | pre-commit | Sintaxis de archivos de configuración |

### Cómo funciona

```
git commit -m "feat: nueva función"
         │
         ▼
  [pre-commit hooks se ejecutan]
         │
    ┌────┴────┐
    │         │
  PASS       FAIL
    │         │
    ▼         ▼
  commit   commit BLOQUEADO
  creado   (ver error y corregir)
```

Si un hook falla, el commit NO se crea. Corriges el problema, haces `git add` nuevamente y vuelves a intentar el commit. Puedes ejecutarlos manualmente en cualquier momento:

```bash
pre-commit run --all-files
```

---

## Observabilidad — Fase 6 (Stack de Monitoreo)

El stack de monitoreo es opcional y se activa con el perfil `monitoring`. No afecta los servicios principales.

### Componentes

| Herramienta | Función | Puerto |
|------------|---------|--------|
| **Prometheus** | Recolecta métricas del API cada 15s | :9090 |
| **Grafana** | Dashboard de métricas y logs | :3001 |
| **Loki** | Backend de agregación de logs | :3100 |
| **Promtail** | Lee los logs de Docker y los envía a Loki | — |
| **Falco** | Detecta comportamiento anómalo en contenedores | — |

### Cómo funciona

```
┌─────────────┐  scrape /metrics  ┌────────────┐
│  API (8000) │ ◄──────────────── │ Prometheus │
└─────────────┘                   └─────┬──────┘
                                        │
┌─────────────┐  push logs        ┌─────▼──────┐
│  Promtail   │ ──────────────►  │    Loki     │
│  (Docker    │                   └─────┬──────┘
│   socket)   │                         │
└─────────────┘                   ┌─────▼──────┐
                                  │  Grafana   │ ◄── tú
┌─────────────┐  alertas stdout  └────────────┘
│    Falco    │ ─────────────────────────────────► Docker logs
│  (kernel)   │
└─────────────┘
```

- **Prometheus** hace "scraping" (pull) al endpoint `/metrics` del API cada 15 segundos
- **Promtail** hace "pushing" (push) de todos los logs Docker a Loki en tiempo real
- **Grafana** consulta ambos (Prometheus para métricas, Loki para logs) y los muestra en dashboards
- **Falco** monitorea las llamadas al kernel y alerta si un contenedor hace algo sospechoso (abrir una shell, leer `/etc/shadow`, etc.)

### Activar el stack de monitoreo

```bash
docker compose --profile monitoring up -d
```

| URL | Servicio | Credenciales |
|-----|---------|--------------|
| http://localhost:9090 | Prometheus | — |
| http://localhost:3001 | Grafana | admin / admin |

### Dashboards recomendados en Grafana

Una vez en Grafana, importa estos dashboards desde grafana.com:
- **ID 17175** — FastAPI Observability (métricas del API)
- **ID 15141** — Docker Container Logs con Loki

### Falco — Detección de anomalías

Falco monitorea el kernel y genera alertas cuando detecta comportamiento sospechoso:

```bash
# Ver alertas de Falco en tiempo real
docker logs -f shieldscan-falco
```

Reglas personalizadas en [`monitoring/falco/falco_rules.local.yaml`](monitoring/falco/falco_rules.local.yaml):
- Shell interactiva abierta en contenedor ShieldScan
- Lectura de archivos sensibles (`/etc/shadow`, `/proc/*/environ`)
- Conexiones de red inesperadas desde el worker

> **Nota:** Falco requiere acceso privilegiado al kernel. En Windows con Docker Desktop, puede tener funcionalidad limitada. Funciona completamente en hosts Linux.

---

## Licencia

MIT — ver [LICENSE](LICENSE)

**ArthurTech — Equipo de Seguridad y Operaciones**
