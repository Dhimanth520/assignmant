from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.routers import upload ,products ,webhooks
from app.database import Base, engine

app = FastAPI(title="Product Importer")
Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(upload.router)
app.include_router(products.router, tags=["Products"])
app.include_router(webhooks.router)

# Home page route
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Serve the basic HTML UI for CSV upload
    """
    return templates.TemplateResponse("index.html", {"request": request})
