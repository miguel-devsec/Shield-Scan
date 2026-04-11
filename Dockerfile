# WordPress Security Auditor - Dockerfile
FROM python:3.9-slim

# Configurar variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOST=0.0.0.0
ENV PORT=8000

# Crear usuario no-root para ejecutar la aplicación
RUN groupadd -r auditor && useradd -r -g auditor auditor

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorio para archivos estáticos
RUN mkdir -p static

# Cambiar permisos para que el usuario no-root pueda ejecutar la aplicación
RUN chown -R auditor:auditor /app

# Cambiar a usuario no-root para ejecutar la aplicación
USER auditor

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')" || exit 1

# Comando por defecto
CMD ["python", "start.py"]
