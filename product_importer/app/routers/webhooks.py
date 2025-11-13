from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.webhook_tasks import deliver_webhook_task
import httpx

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# Create Webhook
@router.post("/", response_model=schemas.WebhookOut)
def create_webhook(webhook: schemas.WebhookCreate, db: Session = Depends(get_db)):
    # Convert HttpUrl to string before saving
    db_wh = models.Webhook(
        url=str(webhook.url),
        event=webhook.event,
        enabled=webhook.enabled
    )
    db.add(db_wh)
    db.commit()
    db.refresh(db_wh)
    return db_wh

#List Webhooks
@router.get("/", response_model=list[schemas.WebhookOut])
def list_webhooks(db: Session = Depends(get_db)):
    return db.query(models.Webhook).all()

#Update Webhook
@router.put("/{webhook_id}", response_model=schemas.WebhookOut)
def update_webhook(webhook_id: int, webhook: schemas.WebhookCreate, db: Session = Depends(get_db)):
    db_wh = db.query(models.Webhook).get(webhook_id)
    if not db_wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    for k, v in webhook.dict().items():
        if k == "url":
            setattr(db_wh, k, str(v))
        else:
            setattr(db_wh, k, v)

    db.commit()
    db.refresh(db_wh)
    return db_wh

# Delete Webhook
@router.delete("/{webhook_id}")
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    wh = db.query(models.Webhook).get(webhook_id)
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(wh)
    db.commit()
    return {"detail": "Webhook deleted"}

# Test Webhook
@router.post("/test/{webhook_id}")
async def test_webhook(webhook_id: int, db: Session = Depends(get_db)):
    wh = db.query(models.Webhook).get(webhook_id)
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    payload = {"event": "test", "message": "This is a test webhook."}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(wh.url, json=payload, timeout=5)
            return {
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook test failed: {e}")
