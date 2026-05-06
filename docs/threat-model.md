# Threat Model — ShieldScan v2.0

## 1. Context and Scope

ShieldScan is a web security auditor built on a microservices architecture. This document describes the STRIDE threat model for the system's main components.

**Tool used:** OWASP Threat Dragon
**Methodology:** STRIDE
**Date:** 2025
**Model file:** [`ThreatDragonModels/New Threat Model/New Threat Model.json`](../ThreatDragonModels/New%20Threat%20Model/New%20Threat%20Model.json)

---

## 2. Data Flow Diagram — Level 0

```
[User] ──HTTP──► [Frontend nginx] ──HTTP──► [FastAPI API] ──TCP──► [PostgreSQL]
                                                   │
                                                [Redis]
                                                   │
                                           [Celery Worker] ──HTTP──► [Target Site]
```

## 3. Data Flow Diagram — Level 1

### External entities
- **User**: Person accessing via web browser
- **Target Site**: WordPress/web site to be audited

### Processes
- **P1 — Frontend (nginx)**: Serves the React SPA, proxies /api/ to the API
- **P2 — API (FastAPI)**: JWT authentication, audit management, task queuing
- **P3 — Worker (Celery)**: Executes the security scan asynchronously

### Data stores
- **D1 — PostgreSQL**: Users, hashed credentials, audit results
- **D2 — Redis**: Celery task queue, result cache

### Data flows
- F1: User → Frontend: HTTPS request
- F2: Frontend → API: JSON request with Bearer Token
- F3: API → PostgreSQL: SQL queries
- F4: API → Redis: publish audit task
- F5: Worker → Redis: consume task
- F6: Worker → Target Site: HTTP analysis requests
- F7: Worker → PostgreSQL: save results

---

## 4. STRIDE Analysis

### 4.1 Spoofing

| ID | Component | Threat | Mitigation |
|----|-----------|--------|------------|
| S1 | API /auth/login | Brute-force attack against credentials | Rate limiting, bcrypt with high cost factor |
| S2 | JWT Token | JWT token forgery | HS256 algorithm with strong SECRET_KEY, 24h expiry |
| S3 | Worker | Malicious worker impersonating the legitimate one | Redis on internal network (not exposed), no external authentication |

**Implemented mitigations:**
- Passwords hashed with bcrypt
- JWT with configurable expiry
- Redis and PostgreSQL only accessible within the internal Docker network

### 4.2 Tampering

| ID | Component | Threat | Mitigation |
|----|-----------|--------|------------|
| T1 | PostgreSQL | SQL Injection | SQLAlchemy ORM with bound parameters |
| T2 | API POST /audits | Malicious URL as input | URL validation in the Pydantic model |
| T3 | Worker | Modification of results in transit | Redis on internal network, inter-service communication via Docker network |

### 4.3 Repudiation

| ID | Component | Threat | Mitigation |
|----|-----------|--------|------------|
| R1 | API | User denies having created an audit | user_id, timestamp, and URL recorded with each audit |
| R2 | Worker | Loss of execution logs | Structured Celery logs at INFO level |

### 4.4 Information Disclosure

| ID | Component | Threat | Mitigation |
|----|-----------|--------|------------|
| I1 | API /docs | Exposure of documentation in production | docs_url can be disabled via env var |
| I2 | JWT Payload | Sensitive data in the token | Only user_id and role stored in payload |
| I3 | Environment variables | Secrets in logs or error responses | SECRET_KEY and DB_PASSWORD via env vars only, never hardcoded |
| I4 | PostgreSQL | Exposed DB credentials | Credentials via environment variables, internal network |

### 4.5 Denial of Service

| ID | Component | Threat | Mitigation |
|----|-----------|--------|------------|
| D1 | Worker | Massive audits saturate the worker | Celery with concurrency=4, 20s timeout in httpx |
| D2 | API | Flood of requests to /audits endpoint | Rate limiting recommended (FastAPI Limiter) |
| D3 | Target Site | ShieldScan used to attack third parties | Identifiable user-agent, no active attacks |

### 4.6 Elevation of Privilege

| ID | Component | Threat | Mitigation |
|----|-----------|--------|------------|
| E1 | API /audits/admin/all | Regular user accesses admin endpoint | `require_admin` dependency checks role in JWT |
| E2 | Containers | Container escape | All containers run as non-root user |
| E3 | API | Access to other users' audits | Filter by user_id in all queries |

---

## 5. Identified Risks by Severity

| Severity | Risk | Status |
|----------|------|--------|
| HIGH | Brute force on /auth/login | Partially mitigated (bcrypt) — Rate limiting pending |
| HIGH | URL injection in worker (SSRF) | Mitigated with URL validation in Pydantic |
| MEDIUM | JWT without revocation | Accepted — 24h TTL as compensation |
| MEDIUM | Redis without authentication | Mitigated — only accessible on internal Docker network |
| LOW | Verbose logs with audit data | Mitigated — only audit_id and url are logged |

---

## 6. Implemented Security Controls

1. **Authentication**: JWT with HS256, 24h expiry, roles (user/admin)
2. **Passwords**: bcrypt with secure cost factor
3. **SQL Injection**: SQLAlchemy ORM, no manual queries with string concatenation
4. **XSS**: html.escape() sanitization in generated reports
5. **Containers**: Non-root user in all Dockerfiles
6. **Secrets**: No hardcoded secrets — all via environment variables
7. **Network**: PostgreSQL and Redis not exposed to host (internal Docker network only)
8. **CORS**: Configured in FastAPI (adjust origins in production)
