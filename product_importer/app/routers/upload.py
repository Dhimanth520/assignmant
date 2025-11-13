from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.tasks import import_csv_task
import uuid
import redis
import os
import tempfile

router = APIRouter()


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# csv Upload endpoint
@router.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_path = temp_file.name
    temp_file.write(await file.read())
    temp_file.close()
    r.set(f"upload_progress:{task_id}", 0)

    import_csv_task.delay(temp_path, task_id)

    return JSONResponse({"task_id": task_id})

# Uplload progress endpoint
@router.get("/upload-progress/{task_id}")
def get_upload_progress(task_id: str):
    progress = r.get(f"upload_progress:{task_id}")
    if progress is None:
        progress = 0
    else:
        progress = int(progress)
    return {"progress": progress}
