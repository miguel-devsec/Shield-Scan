# Modelado de Amenazas — ShieldScan v2.0

## 1. Contexto y Alcance

ShieldScan es un auditor de seguridad web con arquitectura de microservicios. Este documento describe el modelo de amenazas STRIDE para los componentes principales del sistema.

**Herramienta utilizada:** OWASP Threat Dragon  
**Metodología:** STRIDE  
**Fecha:** 2025

---

## 2. Diagrama de Flujo de Datos — Nivel 0

```
[Usuario] ──HTTP──► [Frontend nginx] ──HTTP──► [API FastAPI] ──TCP──► [PostgreSQL]
                                                     │
                                                  [Redis]
                                                     │
                                               [Worker Celery] ──HTTP──► [Sitio Objetivo]
```

## 3. Diagrama de Flujo de Datos — Nivel 1

### Entidades externas
- **Usuario**: Persona que accede via navegador web
- **Sitio Objetivo**: Sitio WordPress/web que será auditado

### Procesos
- **P1 — Frontend (nginx)**: Sirve la SPA React, proxea /api/ hacia la API
- **P2 — API (FastAPI)**: Autenticación JWT, gestión de auditorías, encolado de tareas
- **P3 — Worker (Celery)**: Ejecuta el escaneo de seguridad de forma asíncrona

### Almacenes de datos
- **D1 — PostgreSQL**: Usuarios, credenciales hasheadas, resultados de auditorías
- **D2 — Redis**: Cola de tareas Celery, caché de resultados

### Flujos de datos
- F1: Usuario → Frontend: petición HTTPS
- F2: Frontend → API: petición JSON con Bearer Token
- F3: API → PostgreSQL: consultas SQL
- F4: API → Redis: publicar tarea de auditoría
- F5: Worker → Redis: consumir tarea
- F6: Worker → Sitio Objetivo: peticiones HTTP de análisis
- F7: Worker → PostgreSQL: guardar resultados

---

## 4. Análisis STRIDE

### 4.1 Spoofing (Suplantación de identidad)

| ID | Componente | Amenaza | Mitigación |
|----|-----------|---------|------------|
| S1 | API /auth/login | Ataque de fuerza bruta contra credenciales | Rate limiting, bcrypt con cost factor alto |
| S2 | JWT Token | Falsificación de tokens JWT | Algoritmo HS256 con SECRET_KEY fuerte, expiración 24h |
| S3 | Worker | Worker malicioso suplantando al legítimo | Redis en red interna (no expuesto), sin autenticación externa |

**Mitigaciones implementadas:**
- Contraseñas hasheadas con bcrypt (passlib)
- JWT con expiración configurable
- Redis y PostgreSQL solo accesibles dentro de la red Docker interna

### 4.2 Tampering (Manipulación de datos)

| ID | Componente | Amenaza | Mitigación |
|----|-----------|---------|------------|
| T1 | PostgreSQL | Inyección SQL | SQLAlchemy ORM con parámetros vinculados |
| T2 | API POST /audits | URL maliciosa como entrada | Validación de URL en el modelo Pydantic |
| T3 | Worker | Modificación de resultados en tránsito | Redis en red interna, comunicación entre servicios por red Docker |

### 4.3 Repudiation (Repudio)

| ID | Componente | Amenaza | Mitigación |
|----|-----------|---------|------------|
| R1 | API | Usuario niega haber creado una auditoría | Registro de user_id, timestamp y URL en cada auditoría |
| R2 | Worker | Pérdida de logs de ejecución | Logs estructurados en Celery con nivel INFO |

### 4.4 Information Disclosure (Divulgación de información)

| ID | Componente | Amenaza | Mitigación |
|----|-----------|---------|------------|
| I1 | API /docs | Exposición de documentación en producción | docs_url deshabilitable via env var |
| I2 | JWT Payload | Datos sensibles en el token | Solo se almacena user_id y role en el payload |
| I3 | Variables de entorno | Secretos en logs o respuestas de error | SECRET_KEY y DB_PASSWORD solo via env vars, no hardcoded |
| I4 | PostgreSQL | Credenciales de BD expuestas | Credenciales via variables de entorno, red interna |

### 4.5 Denial of Service (Denegación de servicio)

| ID | Componente | Amenaza | Mitigación |
|----|-----------|---------|------------|
| D1 | Worker | Auditorías masivas saturan el worker | Celery con concurrency=4, timeout de 20s en httpx |
| D2 | API | Flood de peticiones al endpoint /audits | Rate limiting recomendado (FastAPI Limiter) |
| D3 | Sitio Objetivo | ShieldScan usado para atacar terceros | User-agent identificable, sin ataques activos |

### 4.6 Elevation of Privilege (Escalada de privilegios)

| ID | Componente | Amenaza | Mitigación |
|----|-----------|---------|------------|
| E1 | API /audits/admin/all | Usuario normal accede a endpoint de admin | Dependencia `require_admin` verifica rol en JWT |
| E2 | Contenedores | Escape de contenedor | Todos los contenedores corren como usuario no-root |
| E3 | API | Acceso a auditorías de otros usuarios | Filtro por user_id en todas las consultas |

---

## 5. Riesgos Identificados por Severidad

| Severidad | Riesgo | Estado |
|-----------|--------|--------|
| ALTA | Fuerza bruta en /auth/login | Mitigado parcialmente (bcrypt) — Rate limiting pendiente |
| ALTA | Inyección de URL en worker (SSRF) | Mitigado con validación de URL en Pydantic |
| MEDIA | JWT sin revocación | Aceptado — TTL de 24h como compensación |
| MEDIA | Redis sin autenticación | Mitigado — solo accesible en red interna Docker |
| BAJA | Logs verbosos con datos de auditoría | Mitigado — solo se loguea audit_id y url |

---

## 6. Controles de Seguridad Implementados

1. **Autenticación**: JWT con HS256, expiración 24h, roles (user/admin)
2. **Contraseñas**: bcrypt via passlib con factor de costo seguro
3. **Inyección SQL**: SQLAlchemy ORM, sin queries manuales con concatenación
4. **XSS**: Sanitización html.escape() en reportes generados
5. **Contenedores**: Usuario no-root en todos los Dockerfiles
6. **Secretos**: Ningún secreto hardcodeado — todos via variables de entorno
7. **Red**: PostgreSQL y Redis no expuestos al host (solo red interna Docker)
8. **CORS**: Configurado en FastAPI (ajustar origins en producción)
