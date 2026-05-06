# Manual de Arquitectura — ShieldScan v2.0

## 1. Visión General

ShieldScan es una plataforma de auditoría de seguridad web diseñada con una **arquitectura de microservicios**. El sistema desacopla las responsabilidades en servicios independientes y desplegables que se comunican mediante interfaces bien definidas: una API REST síncrona y una cola de mensajes asíncrona.

El principio de diseño central es la **separación de responsabilidades**: la API gestiona la autenticación, autorización y despacho de solicitudes; el worker gestiona el proceso de auditoría de larga duración e intensivo en I/O; el frontend gestiona la interacción con el usuario. Esta separación permite escalado, despliegue y dominios de fallo independientes.

---

## 2. Diagrama de Componentes

```mermaid
graph TB
    subgraph Browser["Cliente — Navegador"]
        UI[React SPA]
    end

    subgraph Docker["Red Docker: shieldscan-net"]
        subgraph FE["Servicio Frontend (puerto 3000)"]
            Nginx[nginx reverse proxy]
        end

        subgraph API["Servicio API (puerto 8000)"]
            FastAPI[Aplicación FastAPI]
            Auth[Módulo JWT Auth]
            Router[Routers REST]
            Metrics[Prometheus /metrics]
        end

        subgraph Worker["Servicio Worker"]
            Celery[Celery Worker]
            Auditor[SecurityAuditor]
        end

        subgraph Infra["Servicios de Infraestructura"]
            PG[(PostgreSQL 16\nUsuarios + Auditorías)]
            Redis[(Redis 7\nBroker de Mensajes)]
        end
    end

    subgraph Target["Externo"]
        Site[Sitio Web Objetivo]
    end

    UI -->|HTTP :3000| Nginx
    Nginx -->|/api/ proxy| FastAPI
    FastAPI --> Auth
    FastAPI --> Router
    FastAPI --> Metrics
    Router -->|SQLAlchemy ORM| PG
    Router -->|send_task| Redis
    Redis -->|consumir cola| Celery
    Celery --> Auditor
    Auditor -->|httpx HTTP| Site
    Auditor -->|UPDATE estado/resultado| PG
```

### Responsabilidades de cada componente

| Componente | Responsabilidad | Tecnología |
|-----------|----------------|-----------|
| **nginx** | Servir el build estático de React; proxear `/api/*` a FastAPI | nginx:alpine |
| **FastAPI** | API REST, autenticación JWT, control de roles, despacho a Celery | Python 3.11, FastAPI 0.104 |
| **Celery Worker** | Consumir tareas de auditoría desde Redis, ejecutar verificaciones de seguridad, escribir resultados en BD | Celery 5.3, httpx |
| **PostgreSQL** | Almacenamiento persistente de usuarios y resultados de auditoría | PostgreSQL 16 |
| **Redis** | Broker de mensajes asíncrono entre API y worker | Redis 7 |

---

## 3. Diagrama de Despliegue

```mermaid
graph TB
    subgraph Host["Máquina Host"]
        subgraph DockerNet["Red Bridge Docker: shieldscan-net"]
            subgraph C1["Contenedor: shieldscan-frontend\nPuerto 3000→80"]
                nginx_c[nginx + build React]
            end

            subgraph C2["Contenedor: shieldscan-api\nPuerto 8000→8000"]
                api_c[FastAPI + uvicorn]
            end

            subgraph C3["Contenedor: shieldscan-worker\n(sin puerto expuesto)"]
                worker_c[Celery worker]
            end

            subgraph C4["Contenedor: shieldscan-db\n(solo interno)"]
                db_c[PostgreSQL 16]
                V1[("Volumen:\npostgres_data")]
            end

            subgraph C5["Contenedor: shieldscan-redis\n(solo interno)"]
                redis_c[Redis 7]
                V2[("Volumen:\nredis_data")]
            end
        end
    end

    db_c --- V1
    redis_c --- V2

    Internet((Internet)) -->|:3000| C1
    Internet -->|:8000| C2
    C1 -->|interno :8000| C2
    C2 -->|interno :5432| C4
    C2 -->|interno :6379| C5
    C3 -->|interno :6379| C5
    C3 -->|interno :5432| C4
```

### Decisiones de diseño

- **PostgreSQL y Redis no están expuestos al host** — solo accesibles dentro de la red bridge Docker. Esto elimina la superficie de ataque externa directa.
- **El frontend usa nginx como servidor de archivos estáticos y proxy de API** — evita las solicitudes preflight CORS desde el navegador y centraliza el punto de entrada.
- **El worker no tiene puerto expuesto** — solo consume de la cola Redis. No existe ruta de red entrante al worker.
- **Los volúmenes son volúmenes Docker con nombre**, no bind mounts — garantiza que los datos persisten entre reinicios de contenedores y evita problemas de permisos de sistema de archivos.

---

## 4. Diagrama de Secuencia — Flujo de Autenticación

```mermaid
sequenceDiagram
    actor Usuario
    participant FE as Frontend (nginx)
    participant API as API (FastAPI)
    participant DB as PostgreSQL

    Usuario->>+FE: Abrir /login
    FE-->>-Usuario: Servir formulario de login (React)

    Usuario->>+FE: Enviar email + contraseña
    FE->>+API: POST /auth/login\n{email, password}
    API->>+DB: SELECT * FROM users WHERE email=?
    DB-->>-API: Registro de usuario (hashed_password, role)
    API->>API: bcrypt.checkpw(password, hash)

    alt Credenciales válidas
        API->>API: create_access_token({sub: user_id, role})
        API-->>-FE: 200 {access_token, token_type: "bearer"}
        FE->>FE: Guardar token en localStorage
        FE-->>Usuario: Redirigir a /dashboard
    else Credenciales inválidas
        API-->>FE: 401 {detail: "Invalid credentials"}
        FE-->>Usuario: Mostrar mensaje de error
    end
```

### Diagrama de Secuencia — Flujo de Ejecución de Auditoría

```mermaid
sequenceDiagram
    actor Usuario
    participant FE as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant RD as Redis
    participant WK as Celery Worker
    participant TG as Sitio Objetivo

    Usuario->>+FE: Enviar formulario de auditoría (URL, empresa)
    FE->>+API: POST /audits/\nAuthorization: Bearer <token>
    API->>API: Validar JWT, extraer user_id
    API->>+DB: INSERT INTO audits (status='pending')
    DB-->>-API: audit_id
    API->>+RD: send_task("perform_audit", [audit_id, url, empresa])
    RD-->>-API: tarea encolada
    API-->>-FE: 201 {id, status: "pending"}
    FE-->>Usuario: Mostrar "Auditoría iniciada" + sondear resultado

    RD->>+WK: Entregar tarea: perform_audit
    WK->>+DB: UPDATE audits SET status='running'
    DB-->>-WK: OK
    WK->>+TG: HTTP HEAD/GET (headers, robots.txt, wp-admin...)
    TG-->>-WK: Respuestas HTTP
    WK->>WK: SecurityAuditor.run() → dict de resultados
    WK->>+DB: UPDATE audits SET status='completed', result=JSON
    DB-->>-WK: OK

    FE->>+API: GET /audits/{id}
    API->>+DB: SELECT * FROM audits WHERE id=? AND user_id=?
    DB-->>-API: Auditoría con JSON de resultado
    API-->>-FE: 200 {status: "completed", result: {...}}
    FE-->>Usuario: Renderizar dashboard de resultados
```

---

## 5. Diagrama de Casos de Uso

```mermaid
graph LR
    subgraph Actores
        UA([Usuario])
        AA([Administrador])
    end

    subgraph Sistema ShieldScan
        UC1[Registrar cuenta]
        UC2[Iniciar sesión]
        UC3[Lanzar auditoría de seguridad]
        UC4[Ver propias auditorías]
        UC5[Ver auditorías de todos los usuarios]
        UC6[Ver detalle de auditoría]
        UC7[Cerrar sesión]
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

    UC3 -.->|incluye| UC2
    UC4 -.->|incluye| UC2
    UC5 -.->|incluye| UC2
    UC5 -.->|extiende| UC4
```

### Definición de actores

| Actor | Descripción |
|-------|-------------|
| **Usuario** | Usuario autenticado con acceso estándar; solo puede ver sus propias auditorías |
| **Administrador** | Rol elevado; puede ver todas las auditorías de todos los usuarios mediante `/audits/admin/all` |

---

## 6. Modelo de Datos

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

    USERS ||--o{ AUDITS : "posee"
```

### Ciclo de vida del estado de una auditoría

```mermaid
stateDiagram-v2
    [*] --> pending : POST /audits/
    pending --> running : Worker recoge la tarea
    running --> completed : Auditoría finalizada con éxito
    running --> failed : Excepción tras max_retries
    failed --> [*]
    completed --> [*]
```

---

## 7. Patrones de Diseño

| Patrón | Dónde se aplica | Justificación |
|--------|----------------|---------------|
| **API Gateway** | FastAPI es el único punto de entrada para todas las solicitudes del cliente | Centraliza auth, rate limiting y enrutamiento |
| **Cola de mensajes** | Redis + Celery desacopla la ejecución de auditorías de la solicitud HTTP | Las solicitudes HTTP retornan en < 200ms; las auditorías tardan 5–30s |
| **Patrón Repository** | SQLAlchemy Session + modelos ORM | Desacopla la lógica de negocio del SQL; permite pruebas unitarias sin BD real |
| **Control de acceso basado en roles** | Dependencia `require_admin` en FastAPI | Aplica la autorización a nivel del framework, no en la lógica de negocio |
| **Contenedores no-root** | Todos los Dockerfiles cambian a usuario no-root | Defensa en profundidad: limita el radio de explosión si un contenedor es comprometido |
| **Health checks** | Todos los servicios Docker definen `HEALTHCHECK` | Permite `depends_on: condition: service_healthy` en Docker Compose, evitando condiciones de carrera al arrancar |

---

## 8. Justificación de Tecnologías

| Elección | Alternativas consideradas | Por qué se eligió |
|----------|--------------------------|-------------------|
| **FastAPI** sobre Flask | Flask, Django | Documentación OpenAPI automática, soporte async nativo, validación Pydantic |
| **Celery + Redis** sobre threading | Hilos Python, asyncio | Cola de tareas persistente, lógica de reintentos, escalado horizontal de workers |
| **PostgreSQL** sobre SQLite | SQLite, MySQL | Grado producción, ACID compliant, soporte de columna JSON |
| **bcrypt directo** sobre passlib | passlib | passlib 1.7.4 no tiene mantenimiento e incompatible con bcrypt ≥ 4.0.0 |
| **JWT** sobre cookies de sesión | Cookies de sesión | Sin estado — funciona entre microservicios; sin almacenamiento de sesión en servidor |
| **nginx** como servidor frontend | Node.js serve, Apache | Mínima huella, proxy inverso integrado, probado en producción |
