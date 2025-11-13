import httpx
import asyncio
from app.database import SessionLocal
from app.models import Webhook

async def deliver_webhook_task(webhook_id: int, payload: dict):
    db = SessionLocal()
    try:
        wh = db.query(Webhook).get(webhook_id)
        if not wh or not wh.enabled:
            return

        async with httpx.AsyncClient() as client:
            await client.post(wh.url, json=payload, timeout=10)
    except Exception as e:
        print(f"Webhook {webhook_id} delivery failed:", e)
    finally:
        db.close()
