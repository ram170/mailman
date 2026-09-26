from pydantic import BaseModel, ConfigDict


class Address(BaseModel):
    address1: str | None = None
    address2: str | None = None

    city: str | None = None
    province: str | None = None

    country: str | None = None
    country_code: str | None = None

    zip: str | None = None

    model_config = ConfigDict(extra="ignore")