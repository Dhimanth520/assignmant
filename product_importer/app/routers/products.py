
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from uuid import uuid4
import redis
import os
import csv
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, Webhook
from app.schemas import ProductCreate, ProductUpdate, ProductOut
from app.tasks import import_csv_task
from app.webhook_tasks import deliver_webhook_task

router = APIRouter()


# Redis connection for CSV progress

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)



# Get Products 

@router.get("/products/", response_model=list[ProductOut])
async def list_products(
    skip: int = 0,
    limit: int = 20,
    filter_id: int = Query(None),
    filter_sku: str = Query(None),
    filter_name: str = Query(None),
    filter_active: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if filter_id is not None:
        query = query.filter(Product.id == filter_id)
    if filter_sku:
        query = query.filter(Product.sku == filter_sku)
    if filter_name:
        query = query.filter(Product.name.ilike(f"%{filter_name}%"))
    if filter_active in ["true", "false"]:
        query = query.filter(Product.active == (filter_active == "true"))

    return query.order_by(Product.id).offset(skip).limit(limit).all()

# Create Product + Trigger Webhooks
@router.post("/products/", response_model=ProductOut)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    def create_in_db():
        existing = db.query(Product).filter(Product.sku.ilike(product.sku)).first()
        if existing:
            raise HTTPException(status_code=400, detail="SKU already exists")
        new_product = Product(**product.dict())
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product

    new_product = await run_in_threadpool(create_in_db)
    webhooks = await run_in_threadpool(
        lambda: db.query(Webhook)
        .filter(Webhook.event == "product.created", Webhook.enabled == True)
        .all()
    )
    for wh in webhooks:
        deliver_webhook_task.delay(wh.id, {"event": "product.created", "product": new_product.id})

    return new_product


# Update Product + Trigger Webhooks
@router.put("/products/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    def update_in_db():
        db_product = db.query(Product).get(product_id)
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        for key, value in product.dict().items():
            setattr(db_product, key, value)
        db.commit()
        db.refresh(db_product)
        return db_product

    updated = await run_in_threadpool(update_in_db)
    webhooks = await run_in_threadpool(
        lambda: db.query(Webhook)
        .filter(Webhook.event == "product.updated", Webhook.enabled == True)
        .all()
    )
    for wh in webhooks:
        deliver_webhook_task.delay(wh.id, {"event": "product.updated", "product": updated.id})

    return updated


# Delete Product + Trigger Webhooks
@router.delete("/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    def delete_in_db():
        db_product = db.query(Product).get(product_id)
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        db.delete(db_product)
        db.commit()
        return db_product

    deleted = await run_in_threadpool(delete_in_db)
    webhooks = await run_in_threadpool(
        lambda: db.query(Webhook)
        .filter(Webhook.event == "product.deleted", Webhook.enabled == True)
        .all()
    )
    for wh in webhooks:
        deliver_webhook_task.delay(wh.id, {"event": "product.deleted", "product": deleted.id})

    return {"detail": "Product deleted"}


# Bulk Delete All Products
@router.delete("/products/")
async def delete_all_products(db: Session = Depends(get_db)):
    def delete_all_in_db():
        db.query(Product).delete()
        db.commit()

    await run_in_threadpool(delete_all_in_db)
    return {"detail": "All products deleted"}
