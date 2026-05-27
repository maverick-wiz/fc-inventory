"""Celery tasks: low-stock alerts, report generation, email dispatch."""
from app.workers.celery_app import celery_app
import logging

log = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def dispatch_low_stock_alert(self, tenant_id: str, product_id: str, qty_on_hand: int, reorder_point: int):
    """Fire low-stock alert to configured tenant recipients."""
    try:
        log.info(f"Low-stock alert: tenant={tenant_id} product={product_id} qty={qty_on_hand} reorder={reorder_point}")
        # TODO: fetch tenant notification config from DB and send email/push
        # For now: log and return
        return {"status": "sent", "tenant_id": tenant_id, "product_id": product_id}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def generate_report_async(self, tenant_id: str, report_type: str, params: dict, report_snapshot_id: str):
    """Async large report generation — stores result in S3 and updates report_snapshots."""
    try:
        log.info(f"Generating async report: type={report_type} tenant={tenant_id}")
        # TODO: run report query, upload to S3, update report_snapshots.s3_key
        return {"status": "complete", "snapshot_id": report_snapshot_id}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def send_email_notification(self, to_emails: list, subject: str, body: str):
    """Send email via configured SMTP."""
    try:
        log.info(f"Sending email: to={to_emails} subject={subject}")
        # TODO: implement SMTP via smtplib or SendGrid
        return {"status": "sent", "recipients": to_emails}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def dispatch_webhook(self, webhook_url: str, payload: dict, hmac_secret: str):
    """Push event to tenant webhook URL with HMAC-SHA256 signature."""
    import hmac, hashlib, json
    import httpx
    try:
        body = json.dumps(payload)
        sig = hmac.new(hmac_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        with httpx.Client(timeout=10) as client:
            resp = client.post(webhook_url, content=body, headers={
                "Content-Type": "application/json",
                "X-FC-Signature": f"sha256={sig}",
            })
            resp.raise_for_status()
        return {"status": "delivered", "url": webhook_url, "http_status": resp.status_code}
    except Exception as exc:
        raise self.retry(exc=exc)
