# Architecture Manual — ShieldScan v2.0

## 1. Overview

ShieldScan is a web security auditing platform designed around a **microservices architecture**. The system decouples concerns into independent, deployable services that communicate through well-defined interfaces: a synchronous REST API and an asynchronous message queue.

The core design principle is **separation of concerns**: the API handles authentication, authorization, and request dispatch; the worker handles the long-running, I/O-intensive audit process; the frontend handles user interaction. This separation enables independent scaling, independent deployment, and independent failure domains.

---

## 2. Component Diagram

```mermaid
graph TB
    subgraph Browser["Client — Browser"]
        UI[React SPA]
    end

    subgraph Docker["Docker Network: shieldscan-net"]
        subgraph FE["Frontend Service (port 3000)"]
            Nginx[nginx reverse proxy]
        end

        subgraph API["API Service (port 8000)"]
            FastAPI[FastAPI application]
            Auth[JWT Auth module]
            Router[REST Routers]
            Metrics[Prometheus /metrics]
        end

        subgraph Worker["Worker Service"]
            Celery[Celery Worker]
            Auditor[SecurityAuditor]
        end

        subgraph Infra["Infrastructure Services"]
            PG[(PostgreSQL 16\nUsers + Audits)]
            Redis[(Redis 7\nMessage Broker)]
        end
    end

    subgraph Target["External"]
        Site[Target Website]
    end

    UI -->|HTTP :3000| Nginx
    Nginx -->|/api/ proxy| FastAPI
    FastAPI --> Auth
    FastAPI --> Router
    FastAPI --> Metrics
    Router -->|SQLAlchemy ORM| PG
    Router -->|send_task| Redis
    Redis -->|consume queue| Celery
    Celery --> Auditor
    Auditor -->|httpx HTTP| Site
    Auditor -->|UPDATE status/result| PG
```

### Component responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|-----------|
| **nginx** | Serve static React build; proxy `/api/*` to FastAPI | nginx:alpine |
| **FastAPI** | REST API, JWT authentication, role enforcement, Celery dispatch | Python 3.11, FastAPI 0.104 |
| **Celery Worker** | Consume audit tasks from Redis, execute security checks, write results to DB | Celery 5.3, httpx |
| **PostgreSQL** | Persistent storage of users and audit results | PostgreSQL 16 |
| **Redis** | Async message broker between API and worker | Redis 7 |

---

## 3. Deployment Diagram

```mermaid
graph TB
    subgraph Host["Host Machine"]
        subgraph DockerNet["Docker Bridge Network: shieldscan-net"]
            subgraph C1["Container: shieldscan-frontend\nPort 3000→80"]
                nginx_c[nginx + React build]
            end

            subgraph C2["Container: shieldscan-api\nPort 8000→8000"]
                api_c[FastAPI + uvicorn]
            end

            subgraph C3["Container: shieldscan-worker\n(no exposed port)"]
                worker_c[Celery worker]
            end

            subgraph C4["Container: shieldscan-db\n(internal only)"]
                db_c[PostgreSQL 16]
                V1[("Volume:\npostgres_data")]
            end

            subgraph C5["Container: shieldscan-redis\n(internal only)"]
                redis_c[Redis 7]
                V2[("Volume:\nredis_data")]
            end
        end
    end

    db_c --- V1
    redis_c --- V2

    Internet((Internet)) -->|:3000| C1
    Internet -->|:8000| C2
    C1 -->|internal :8000| C2
    C2 -->|internal :5432| C4
    C2 -->|internal :6379| C5
    C3 -->|internal :6379| C5
    C3 -->|internal :5432| C4
```

### Design decisions

- **PostgreSQL and Redis are not exposed to the host** — only accessible inside the Docker bridge network. This eliminates direct external attack surface.
- **Frontend uses nginx as both static file server and API proxy** — avoids CORS preflight requests from the browser and centralizes the entry point.
- **Worker has no exposed port** — it only consumes from the Redis queue. There is no inbound network path to the worker.
- **Volumes are named Docker volumes**, not bind mounts — ensures data persists across container restarts and avoids filesystem permission issues.

---

## 4. Sequence Diagram — Authentication Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend (nginx)
    participant API as API (FastAPI)
    participant DB as PostgreSQL

    User->>+FE: Open /login
    FE-->>-User: Serve login form (React)

    User->>+FE: Submit email + password
    FE->>+API: POST /auth/login\n{email, password}
    API->>+DB: SELECT * FROM users WHERE email=?
    DB-->>-API: User record (hashed_password, role)
    API->>API: bcrypt.checkpw(password, hash)

    alt Credentials valid
        API->>API: create_access_token({sub: user_id, role})
        API-->>-FE: 200 {access_token, token_type: "bearer"}
        FE->>FE: Store token in localStorage
        FE-->>User: Redirect to /dashboard
    else Credentials invalid
        API-->>FE: 401 {detail: "Invalid credentials"}
        FE-->>User: Show error message
    end
```

### Sequence Diagram — Audit Execution Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant RD as Redis
    participant WK as Celery Worker
    participant TG as Target Site

    User->>+FE: Submit audit form (URL, company)
    FE->>+API: POST /audits/\nAuthorization: Bearer <token>
    API->>API: Validate JWT, extract user_id
    API->>+DB: INSERT INTO audits (status='pending')
    DB-->>-API: audit_id
    API->>+RD: send_task("perform_audit", [audit_id, url, company])
    RD-->>-API: task enqueued
    API-->>-FE: 201 {id, status: "pending"}
    FE-->>User: Show "Audit started" + poll for result

    RD->>+WK: Deliver task: perform_audit
    WK->>+DB: UPDATE audits SET status='running'
    DB-->>-WK: OK
    WK->>+TG: HTTP HEAD/GET (headers, robots.txt, wp-admin...)
    TG-->>-WK: HTTP responses
    WK->>WK: SecurityAuditor.run() → result dict
    WK->>+DB: UPDATE audits SET status='completed', result=JSON
    DB-->>-WK: OK

    FE->>+API: GET /audits/{id}
    API->>+DB: SELECT * FROM audits WHERE id=? AND user_id=?
    DB-->>-API: Audit with result JSON
    API-->>-FE: 200 {status: "completed", result: {...}}
    FE-->>User: Render audit results dashboard
```

---

## 5. Use Case Diagram

```mermaid
graph LR
    subgraph Actors
        UA([User])
        AA([Admin])
    end

    subgraph ShieldScan System
        UC1[Register account]
        UC2[Login]
        UC3[Launch security audit]
        UC4[View own audit results]
        UC5[View all users' audits]
        UC6[View audit detail]
        UC7[Logout]
    end

    UA --> UC1
    UA --> UC2
    UA --> UC3
    UA --> UC4
    UA --> UC6
    UA --> UC7
    AA --> UC2
    AA --> UC3
    AA --> UC4
    AA --> UC5
    AA --> UC6
    AA --> UC7

    UC3 -.->|includes| UC2
    UC4 -.->|includes| UC2
    UC5 -.->|includes| UC2
    UC5 -.->|extends| UC4
```

### Actor definitions

| Actor | Description |
|-------|-------------|
| **User** | Authenticated user with standard access; can only see their own audits |
| **Admin** | Elevated role; can view all audits from all users via `/audits/admin/all` |

---

## 6. Data Model

```mermaid
erDiagram
    USERS {
        int id PK
        string email UK
        string hashed_password
        string role
        datetime created_at
    }

    AUDITS {
        int id PK
        int user_id FK
        string url
        string company_name
        string status
        json result
        datetime created_at
        datetime completed_at
    }

    USERS ||--o{ AUDITS : "owns"
```

### Audit status lifecycle

```mermaid
stateDiagram-v2
    [*] --> pending : POST /audits/
    pending --> running : Worker picks up task
    running --> completed : Audit finished successfully
    running --> failed : Exception after max_retries
    failed --> [*]
    completed --> [*]
```

---

## 7. Design Patterns

| Pattern | Where applied | Justification |
|---------|--------------|---------------|
| **API Gateway** | FastAPI is the single entry point for all client requests | Centralizes auth, rate limiting, and routing |
| **Message Queue** | Redis + Celery decouples audit execution from the HTTP request | HTTP requests return in < 200ms; audits take 5–30s |
| **Repository pattern** | SQLAlchemy Session + ORM models | Decouples business logic from SQL; enables unit testing without a real DB |
| **Role-based access control** | `require_admin` dependency in FastAPI | Enforces authorization at the framework level, not business logic |
| **Non-root containers** | All Dockerfiles switch to a non-root user | Defense-in-depth: limits blast radius if a container is compromised |
| **Health checks** | All Docker services define `HEALTHCHECK` | Enables Docker Compose `depends_on: condition: service_healthy`, prevents race conditions on startup |

---

## 8. Technology Justification

| Choice | Alternatives considered | Why chosen |
|--------|------------------------|------------|
| **FastAPI** over Flask | Flask, Django | Automatic OpenAPI docs, native async support, Pydantic validation |
| **Celery + Redis** over threading | Python threads, asyncio | Persistent task queue, retry logic, horizontal worker scaling |
| **PostgreSQL** over SQLite | SQLite, MySQL | Production-grade, ACID compliant, JSON column support |
| **bcrypt direct** over passlib | passlib | passlib 1.7.4 is unmaintained and incompatible with bcrypt ≥ 4.0.0 |
| **JWT** over session cookies | Session cookies | Stateless — works across microservices; no server-side session storage |
| **nginx** as frontend server | Node.js serve, Apache | Minimal footprint, built-in reverse proxy, production-battle-tested |
