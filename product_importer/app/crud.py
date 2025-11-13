from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy import func

def get_product_by_sku(db: Session, sku: str):
    return db.query(models.Product).filter(func.lower(models.Product.sku) == sku.lower()).first()

def create_or_update_product(db: Session, product: schemas.ProductCreate):
    db_product = get_product_by_sku(db, product.sku)
    if db_product:
        db_product.name = product.name
        db_product.description = product.description
        db_product.active = product.active
    else:
        db_product = models.Product(**product.dict())
        db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_products(db: Session, skip: int = 0, limit: int = 50, filter_sku: str | None = None):
    query = db.query(models.Product)
    if filter_sku:
        query = query.filter(models.Product.sku.ilike(f"%{filter_sku}%"))
    return query.offset(skip).limit(limit).all()

def delete_product(db: Session, product_id: int):
    db_product = db.query(models.Product).get(product_id)
    if db_product:
        db.delete(db_product)
        db.commit()
    return db_product

def delete_all_products(db: Session):
    deleted = db.query(models.Product).delete()
    db.commit()
    return deleted
