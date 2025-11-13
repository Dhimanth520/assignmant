from pydantic import BaseModel
from datetime import datetime
from pydantic import HttpUrl

class ProductBase(BaseModel):
    sku: str
    name: str
    description: str | None = None
    active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class ProductOut(ProductBase):
    id: int

    class Config:
        orm_mode = True


class WebhookBase(BaseModel):
    url: str
    event: str
    enabled: bool = True
    # headers: dict | None = None

class WebhookCreate(BaseModel):
    url: HttpUrl
    event: str
    enabled: bool = True

class WebhookUpdate(WebhookBase):
    pass

class WebhookOut(WebhookBase):
    id: int
    last_status: int | None = None
    last_response: str | None = None
    last_called_at: datetime | None = None

    class Config:
        orm_mode = True
