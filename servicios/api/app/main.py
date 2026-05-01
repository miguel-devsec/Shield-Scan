from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from .database import engine, Base
from .routers import auth, audits

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ShieldScan API", version="2.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(audits.router, prefix="/audits", tags=["audits"])

# Expose /metrics for Prometheus scraping
Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "shieldscan-api"}
