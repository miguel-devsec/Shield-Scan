from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..auth import get_current_user, require_admin
from ..database import get_db
from ..celery_app import celery_app

router = APIRouter()


@router.post("/", response_model=schemas.AuditResponse, status_code=201)
def create_audit(
    audit_data: schemas.AuditCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not audit_data.url.startswith(("http://", "https://")):
        audit_data.url = f"https://{audit_data.url}"

    audit = models.Audit(
        user_id=current_user.id,
        url=audit_data.url,
        company_name=audit_data.company_name,
        status="pending",
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    celery_app.send_task(
        "perform_audit",
        args=[audit.id, audit.url, audit.company_name],
        queue="audits",
    )
    return audit


@router.get("/", response_model=List[schemas.AuditResponse])
def list_audits(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Audit)
        .filter(models.Audit.user_id == current_user.id)
        .order_by(models.Audit.created_at.desc())
        .all()
    )


@router.get("/admin/all", response_model=List[schemas.AuditResponse])
def admin_list_audits(
    _admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(models.Audit).order_by(models.Audit.created_at.desc()).all()


@router.get("/{audit_id}", response_model=schemas.AuditResponse)
def get_audit(
    audit_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    audit = (
        db.query(models.Audit)
        .filter(models.Audit.id == audit_id, models.Audit.user_id == current_user.id)
        .first()
    )
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit
