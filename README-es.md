# ShieldScan v2.0 — Auditor de Seguridad Web

[![Pipeline DevSecOps](https://github.com/miguel-devsec/ShieldScan/actions/workflows/devsecops.yml/badge.svg)](https://github.com/miguel-devsec/ShieldScan/actions/workflows/devsecops.yml)
[![Docker Hub](https://img.shields.io/docker/v/migueldevsec/shieldscan-api?label=Docker%20Hub&logo=docker)](https://hub.docker.com/u/migueldevsec)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![React 18](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://reactjs.org)
[![Cobertura](https://img.shields.io/badge/cobertura-82%25-brightgreen)](servicios/api/tests/)

Plataforma de auditoría de seguridad para WordPress y aplicaciones web en general, construida con **arquitectura de microservicios** e integrada en un **pipeline DevSecOps** completo.

> La aplicación es el vehículo; el pipeline DevSecOps es el producto.

---

## Propósito

ShieldScan automatiza la identificación de configuraciones incorrectas de seguridad en aplicaciones web. Verifica cabeceras HTTP de seguridad, superficies de ataque específicas de WordPress, configuración SSL, listado de directorios y archivos sensibles expuestos. Los resultados se almacenan de forma persistente y son accesibles desde un panel de control React.

---

## Tecnologías

| Capa | Tecnología |
|------|-----------|
| Frontend | React 18, Vite, nginx |
| API Gateway | FastAPI 0.104, Python 3.11, SQLAlchemy 2.0 |
| Worker Asíncrono | Celery 5.3, httpx |
| Base de datos | PostgreSQL 16 |
| Broker de mensajes | Redis 7 |
| Autenticación | JWT (python-jose), bcrypt |
| Contenedores | Docker, Docker Compose, Docker Swarm |
| IaC | Ansible |
| CI/CD | GitHub Actions |
| Seguridad (SAST) | Semgrep, Bandit, Gitleaks |
| Seguridad (DAST) | OWASP ZAP |
| Seguridad (Imagen) | Trivy |
| Seguridad (IaC) | Checkov |
| Observabilidad | Prometheus, Grafana, Loki, Promtail, Falco |

---

## Licencia

[MIT](LICENSE) — ArthurTech Security Operations Team

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     Usuario (Navegador)                      │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP :3000
┌────────────────────────────▼────────────────────────────────┐
│              Frontend — React SPA (nginx)                    │
│              servicios/frontend  ·  puerto 3000              │
└────────────────────────────┬────────────────────────────────┘
                             │ /api/ → proxy
┌────────────────────────────▼────────────────────────────────┐
│              API — FastAPI (Python 3.11)                     │
│              servicios/api  ·  puerto 8000                   │
│              JWT Auth · REST · Celery dispatch               │
└──────────────┬─────────────────────────┬────────────────────┘
               │                         │
   ┌───────────▼──────────┐   ┌──────────▼──────────┐
   │  PostgreSQL 16        │   │  Redis 7             │
   │  Usuarios + Auditorías│   │  Broker de mensajes  │
   └───────────────────────┘   └──────────┬──────────┘
                                          │ cola Celery
                            ┌─────────────▼──────────────┐
                            │  Worker — Celery (Python)   │
                            │  servicios/worker           │
                            │  Auditor asíncrono          │
                            └─────────────┬──────────────┘
                                          │ HTTP (httpx)
                            ┌─────────────▼──────────────┐
                            │    Sitio Web Objetivo        │
                            └────────────────────────────┘
```

---

## Inicio Rápido

### Requisitos previos

- Docker Desktop (con Compose v2)
- Sin otras dependencias locales necesarias

### 1. Clonar el repositorio

```bash
git clone https://github.com/miguel-devsec/ShieldScan.git
cd ShieldScan
```

### 2. Configurar variables de entorno

```bash
cp env.example .env
# Editar .env con valores seguros para producción
```

### 3. Iniciar todos los servicios

```bash
docker compose up --build
```

| Servicio | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API + Swagger | http://localhost:8000/docs |

### 4. Crear un usuario administrador

Regístrate normalmente a través de la interfaz web y luego promuévete a administrador:

```bash
docker exec -it shieldscan-db psql -U shieldscan -d shieldscan \
  -c "UPDATE users SET role='admin' WHERE email='tu@email.com';"
```

### 5. Opcional — Iniciar el stack de monitorización

```bash
docker compose --profile monitoring up -d
```

| URL | Servicio | Credenciales |
|-----|---------|-------------|
| http://localhost:9090 | Prometheus | — |
| http://localhost:3001 | Grafana | admin / admin |

---

## Pipeline DevSecOps

El pipeline completo está definido en [`.github/workflows/devsecops.yml`](.github/workflows/devsecops.yml) y cubre 5 fases del ciclo de vida DevSecOps:

| Fase | Job | Herramienta | Descripción |
|------|-----|-------------|-------------|
| **Fase 2 — Código** | `secrets-scan` | Gitleaks | Detección de secretos en el historial git |
| **Fase 2 — Código** | `sast` | Semgrep + Bandit | Análisis estático (Python) |
| **Fase 2 — Código** | `sca` | Trivy (fs) | Análisis de vulnerabilidades en dependencias |
| **Fase 3 — Build** | `build-and-scan` | Trivy (image) | Escaneo de imagen Docker — **falla en CVEs CRÍTICOS** |
| **Fase 4 — Test** | `unit-tests` | Pytest | Tests unitarios con cobertura |
| **Fase 4 — Test** | `dast` | OWASP ZAP | Análisis dinámico contra staging *(solo main)* |
| **Fase 5 — Release** | `iac-scan` | Checkov | Escaneo de Dockerfile e IaC |
| **Fase 5 — Release** | `push-images` | Docker Hub | Push semántico `vYYYYMMDD-HHMM` + `latest` |

---

## Estructura del Repositorio

```
ShieldScan/
├── .github/
│   └── workflows/
│       └── devsecops.yml        # Pipeline DevSecOps completo
├── docs/
│   ├── architecture.md          # Manual de arquitectura + diagramas UML
│   ├── development-guide.md     # Guía de configuración y contribución
│   ├── deployment-operations.md # Guía de despliegue y operaciones
│   ├── security-manual.md       # Modelo de amenazas + guía de herramientas
│   ├── threat-model.md          # Modelo de amenazas STRIDE
│   └── user-manual.md           # Guía de usuario final
├── docs-es/
│   ├── architecture.md          # Manual de arquitectura (español)
│   ├── development-guide.md     # Guía de desarrollo (español)
│   ├── deployment-operations.md # Guía de despliegue (español)
│   ├── security-manual.md       # Manual de seguridad (español)
│   ├── threat-model.md          # Modelo de amenazas (español)
│   └── user-manual.md           # Manual de usuario (español)
├── infraestructura/
│   └── ansible/                 # Playbook de despliegue
├── monitoring/
│   ├── falco/                   # Reglas de detección de anomalías en runtime
│   ├── grafana/                 # Aprovisionamiento de dashboards
│   ├── loki/                    # Configuración de agregación de logs
│   ├── prometheus/              # Configuración de scraping de métricas
│   └── promtail/                # Configuración de envío de logs
├── orquestacion/
│   └── docker-swarm.yml         # Stack de producción Docker Swarm
├── servicios/
│   ├── api/                     # FastAPI — API Gateway + Auth
│   ├── worker/                  # Celery — Worker asíncrono
│   └── frontend/                # React SPA + nginx
├── .pre-commit-config.yaml      # Hooks de seguridad locales
├── docker-compose.yml           # Entorno de desarrollo completo
└── env.example                  # Plantilla de variables de entorno
```

---

## Documentación

| Documento | Descripción |
|----------|-------------|
| [Manual de Arquitectura](docs-es/architecture.md) | Diseño de microservicios, diagramas UML, patrones |
| [Guía de Desarrollo](docs-es/development-guide.md) | Configuración local, pruebas, flujo de contribución |
| [Despliegue y Operaciones](docs-es/deployment-operations.md) | Despliegue en producción, Ansible, Swarm |
| [Manual de Seguridad](docs-es/security-manual.md) | Modelo de amenazas, herramientas, gestión de vulnerabilidades |
| [Manual de Usuario](docs-es/user-manual.md) | Guía de usuario final con recorrido de funcionalidades |
