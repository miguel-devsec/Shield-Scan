FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN groupadd -r shieldscan && useradd -r -g shieldscan shieldscan

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R shieldscan:shieldscan /app

USER shieldscan

CMD ["celery", "-A", "app.worker.celery_app", "worker", "--loglevel=info", "-Q", "audits", "--concurrency=4"]
