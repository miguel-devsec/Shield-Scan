# ShieldScan v2.0 — Web Security Auditor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/miguel-devsec/ShieldScan/blob/main/LICENSE)
[![Pipeline](https://github.com/miguel-devsec/ShieldScan/actions/workflows/devsecops.yml/badge.svg)](https://github.com/miguel-devsec/ShieldScan/actions/workflows/devsecops.yml)

Automated web security auditing platform built with a microservices architecture and a complete DevSecOps pipeline. Detects security misconfigurations in WordPress and general web applications.

---

## Available Images

| Image | Pull Command |
|-------|-------------|
| **API** (FastAPI + JWT) | `docker pull migueldevsec/shieldscan-api:latest` |
| **Worker** (Celery async auditor) | `docker pull migueldevsec/shieldscan-worker:latest` |
| **Frontend** (React SPA + nginx) | `docker pull migueldevsec/shieldscan-frontend:latest` |

### Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable build from `main` |
| `v2.0.0` | Stable release — microservices architecture |
| `vYYYYMMDD-HHMM` | CI/CD timestamped builds |

---

## Quick Start

All three images are designed to run together. The fastest way to get started:

```bash
# 1. Clone the repository (for docker-compose.yml and config files)
git clone https://github.com/miguel-devsec/ShieldScan.git
cd ShieldScan

# 2. Configure environment
cp env.example .env

# 3. Pull and run all services
docker compose pull
docker compose up -d
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API + Swagger | http://localhost:8000/docs |

---

## Architecture

```
Browser
  │
  ▼ :3000
Frontend (nginx + React SPA)
  │ /api/ proxy
  ▼ :8000
API (FastAPI + JWT auth)
  ├──► PostgreSQL 16   (users + audit results)
  └──► Redis 7         (task queue)
              │
              ▼ Celery task
         Worker (async security auditor)
              │ httpx
              ▼
         Target Website
```

---

## Security Checks Performed

- **HTTP Security Headers** — HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- **WordPress Detection** — confidence score + detection signals
- **WordPress Attack Surface** — wp-admin, xmlrpc.php, wp-config.php, directory listing
- **SSL/TLS** — HTTPS availability, HTTP→HTTPS redirect, certificate validity
- **Sensitive Files** — .env, .git/config, composer.json, package.json exposure

---

## Image Security Properties

All images follow security best practices:

| Property | Value |
|----------|-------|
| Base images | `python:3.11-slim`, `node:18-alpine`, `nginx:alpine` |
| Run as root | No — dedicated non-root user in all images |
| Health check | Yes — all images define HEALTHCHECK |
| Secrets | None hardcoded — all via environment variables |
| Scanned with | Trivy (CI gate fails on CRITICAL CVEs) |

---

## Environment Variables

### API & Worker

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection URL |
| `REDIS_URL` | Yes | Redis connection URL |
| `SECRET_KEY` | Yes (API only) | JWT signing key (min 32 chars) |

### Example `.env`

```env
DB_PASSWORD=change_me_in_production
SECRET_KEY=generate_with_python3_c_import_secrets_print_secrets_token_hex_32
DATABASE_URL=postgresql://shieldscan:${DB_PASSWORD}@db:5432/shieldscan
REDIS_URL=redis://redis:6379/0
```

---

## Source Code & Documentation

- **GitHub**: https://github.com/miguel-devsec/ShieldScan
- **Architecture Manual**: `/docs-en/architecture.md`
- **Deployment Guide**: `/docs-en/deployment-operations.md`
- **Security Manual**: `/docs-en/security-manual.md`

---

## License

[MIT](https://github.com/miguel-devsec/ShieldScan/blob/main/LICENSE) — ArthurTech Security Operations Team
