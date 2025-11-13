from celery import Celery
import csv
import os
import redis
from app.database import SessionLocal
from app.models import Product


celery_app = Celery(
    "tasks",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# Redis for progress tracking
r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)

@celery_app.task(bind=True)
def import_csv_task(self, csv_path, task_id):
    import csv
    from app.database import SessionLocal
    from app.models import Product
    db = SessionLocal()
    total = sum(1 for _ in open(csv_path)) - 1
    processed = 0
    batch = []
    batch_size = 5000
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append(Product(
                sku=row['sku'],
                name=row['name'],
                description=row.get('description'),
                active=row.get('active', 'true').lower() == 'true'
            ))
            processed += 1
            if len(batch) >= batch_size:
                db.bulk_save_objects(batch)
                db.commit()
                batch.clear()
                r.set(f"upload_progress:{task_id}", int(processed / total * 100))

    if batch:
        db.bulk_save_objects(batch)
        db.commit()

    r.set(f"upload_progress:{task_id}", 100)
    db.close()
