import json
import logging
from datetime import datetime, timezone
from sqlalchemy import text
from .worker import celery_app
from .auditor import SecurityAuditor
from .database import get_session

logger = logging.getLogger(__name__)


@celery_app.task(name="perform_audit", bind=True, max_retries=2)
def perform_audit(self, audit_id: int, url: str, company_name: str):
    db = get_session()
    try:
        db.execute(
            text("UPDATE audits SET status='running' WHERE id=:id"),
            {"id": audit_id},
        )
        db.commit()

        auditor = SecurityAuditor(url)
        try:
            result = auditor.run()
        finally:
            auditor.close()

        result["company_name"] = company_name or "Cliente"

        db.execute(
            text(
                "UPDATE audits SET status='completed', result=:result, completed_at=:now WHERE id=:id"
            ),
            {
                "result": json.dumps(result),
                "now": datetime.now(timezone.utc),
                "id": audit_id,
            },
        )
        db.commit()
        logger.info("Audit %d completed for %s", audit_id, url)

    except Exception as exc:
        logger.exception("Audit %d failed: %s", audit_id, exc)
        try:
            db.execute(
                text("UPDATE audits SET status='failed' WHERE id=:id"),
                {"id": audit_id},
            )
            db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
