from pydantic import BaseModel, ConfigDict

from app.models.address import Address


class ShopifyOrder(BaseModel):
    id: int

    name: str | None = None
    email: str | None = None

    shipping_address: Address | None = None

    model_config = ConfigDict(extra="ignore")