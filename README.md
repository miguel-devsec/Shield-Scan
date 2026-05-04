# ShieldScan v2.0 — Web Security Auditor

[![DevSecOps Pipeline](https://github.com/miguel-devsec/ShieldScan/actions/workflows/devsecops.yml/badge.svg)](https://github.com/miguel-devsec/ShieldScan/actions/workflows/devsecops.yml)
[![Docker Hub](https://img.shields.io/docker/v/migueldevsec/shieldscan-api?label=Docker%20Hub&logo=docker)](https://hub.docker.com/u/migueldevsec)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![React 18](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://reactjs.org)

Security auditing platform for WordPress and general web applications, built with a **microservices architecture** and fully integrated into a **DevSecOps pipeline**.

> The application is the vehicle; the DevSecOps pipeline is the product.

---

## Purpose

ShieldScan automates the process of identifying security misconfigurations in web applications. It checks HTTP security headers, WordPress-specific attack surfaces, SSL configuration, directory listing, and exposed sensitive files. Results are stored persistently and accessible through a React dashboard.

---

## Technologies

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, nginx |
| API Gateway | FastAPI 0.104, Python 3.11, SQLAlchemy 2.0 |
| Async Worker | Celery 5.3, httpx |
| Database | PostgreSQL 16 |
| Message Broker | Redis 7 |
| Auth | JWT (python-jose), bcrypt |
| Containerization | Docker, Docker Compose, Docker Swarm |
| IaC | Ansible |
| CI/CD | GitHub Actions |
| Security (SAST) | Semgrep, Bandit, Gitleaks |
| Security (DAST) | OWASP ZAP |
| Security (Image) | Trivy |
| Security (IaC) | Checkov |
| Observability | Prometheus, Grafana, Loki, Promtail, Falco |

---

## License

[MIT](LICENSE) — ArthurTech Security Operations Team

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User (Browser)                        │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP :3000
┌────────────────────────────▼────────────────────────────────┐
│              Frontend — React SPA (nginx)                    │
│              servicios/frontend  ·  port 3000                │
└────────────────────────────┬────────────────────────────────┘
                             │ /api/ → proxy
┌────────────────────────────▼────────────────────────────────┐
│              API — FastAPI (Python 3.11)                     │
│              servicios/api  ·  port 8000                     │
│              JWT Auth · REST · Celery dispatch               │
└──────────────┬─────────────────────────┬────────────────────┘
               │                         │
   ┌───────────▼──────────┐   ┌──────────▼──────────┐
   │  PostgreSQL 16        │   │  Redis 7             │
   │  Users + Audits       │   │  Message broker      │
   └───────────────────────┘   └──────────┬──────────┘
                                          │ Celery queue
                            ┌─────────────▼──────────────┐
                            │  Worker — Celery (Python)   │
                            │  servicios/worker           │
                            │  Async security auditor     │
                            └─────────────┬──────────────┘
                                          │ HTTP (httpx)
                            ┌─────────────▼──────────────┐
                            │    Target Website           │
                            └────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker Desktop (with Compose v2)
- No other local dependencies required

### 1. Clone the repository

```bash
git clone https://github.com/miguel-devsec/ShieldScan.git
cd ShieldScan
```

### 2. Configure environment variables

```bash
cp env.example .env
# Edit .env with secure values for production
```

### 3. Start all services

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API + Swagger | http://localhost:8000/docs |

### 4. Create an admin user

Register normally through the web interface, then promote yourself:

```bash
docker exec -it shieldscan-db psql -U shieldscan -d shieldscan \
  -c "UPDATE users SET role='admin' WHERE email='your@email.com';"
```

### 5. Optional — Start the monitoring stack

```bash
docker compose --profile monitoring up -d
```

| URL | Service | Credentials |
|-----|---------|-------------|
| http://localhost:9090 | Prometheus | — |
| http://localhost:3001 | Grafana | admin / admin |

---

## DevSecOps Pipeline

The complete pipeline is defined in [`.github/workflows/devsecops.yml`](.github/workflows/devsecops.yml) and covers 5 phases of the DevSecOps lifecycle:

| Phase | Job | Tool | Description |
|-------|-----|------|-------------|
| **Phase 2 — Code** | `secrets-scan` | Gitleaks | Secret detection across git history |
| **Phase 2 — Code** | `sast` | Semgrep + Bandit | Static analysis (Python) |
| **Phase 2 — Code** | `sca` | Trivy (fs) | Dependency vulnerability analysis |
| **Phase 3 — Build** | `build-and-scan` | Trivy (image) | Docker image scanning — **fails on CRITICAL CVEs** |
| **Phase 4 — Test** | `unit-tests` | Pytest | Unit tests with coverage |
| **Phase 4 — Test** | `dast` | OWASP ZAP | Dynamic analysis against staging *(main only)* |
| **Phase 5 — Release** | `iac-scan` | Checkov | Dockerfile and IaC scanning |
| **Phase 5 — Release** | `push-images` | Docker Hub | Semantic push `vYYYYMMDD-HHMM` + `latest` |

---

## Repository Structure

```
ShieldScan/
├── .github/
│   └── workflows/
│       └── devsecops.yml        # Complete DevSecOps pipeline
├── docs/
│   ├── architecture.md          # Architecture manual + UML diagrams
│   ├── development-guide.md     # Developer setup and contribution guide
│   ├── deployment-operations.md # Deployment and operations guide
│   ├── security-manual.md       # Threat model + security tools guide
│   ├── threat-model.md          # STRIDE threat model
│   └── user-manual.md           # End-user application guide
├── infraestructura/
│   └── ansible/                 # Deployment playbook
├── monitoring/
│   ├── falco/                   # Runtime anomaly detection rules
│   ├── grafana/                 # Dashboard provisioning
│   ├── loki/                    # Log aggregation config
│   ├── prometheus/              # Metrics scraping config
│   └── promtail/                # Log shipping config
├── orquestacion/
│   └── docker-swarm.yml         # Docker Swarm production stack
├── servicios/
│   ├── api/                     # FastAPI — API Gateway + Auth
│   ├── worker/                  # Celery — Async worker
│   └── frontend/                # React SPA + nginx
├── .pre-commit-config.yaml      # Local security hooks
├── docker-compose.yml           # Complete development environment
└── env.example                  # Environment variable template
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture Manual](docs/architecture.md) | Microservices design, UML diagrams, patterns |
| [Development Guide](docs/development-guide.md) | Local setup, testing, contribution workflow |
| [Deployment & Operations](docs/deployment-operations.md) | Production deployment, Ansible, Swarm |
| [Security Manual](docs/security-manual.md) | Threat model, security tools, vulnerability management |
| [User Manual](docs/user-manual.md) | End-user guide with feature walkthrough |
