import json

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings
from app.integrations.shopify import verify_shopify_webhook
from app.models.order import ShopifyOrder
from app.services.address_validation import AddressValidationService
from app.services.email_service import EmailService


router = APIRouter(
    prefix="/webhooks/shopify",
    tags=["Shopify"],
)

address_validation_service = AddressValidationService()
email_service = EmailService()


@router.post("/orders/create")
async def order_created(
    request: Request,
    x_shopify_hmac_sha256: str | None = Header(default=None),
):
    raw_body = await request.body()

    if not x_shopify_hmac_sha256:
        raise HTTPException(
            status_code=401,
            detail="Missing Shopify HMAC",
        )

    if not verify_shopify_webhook(
        raw_body=raw_body,
        received_hmac=x_shopify_hmac_sha256,
        secret=settings.shopify_webhook_secret,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Shopify HMAC",
        )

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        )

    order = ShopifyOrder.model_validate(payload)

    if not order.shipping_address:
        return {
            "order_id": order.id,
            "status": "review",
            "reason": "Shipping address is missing",
        }

    validation_result = await address_validation_service.validate(
        order.shipping_address
    )

    if validation_result["status"] == "review":
        address = order.shipping_address

        address_text = ", ".join(
            filter(
                None,
                [
                    address.address1,
                    address.address2,
                    address.city,
                    address.province,
                    address.zip,
                    address.country,
                ],
            )
        )

        email_service.send_address_review_email(
            order_id=order.id,
            order_name=order.name,
            address=address_text,
            reason=validation_result.get(
                "reason",
                "Address verification failed",
            ),
        )

    return {
        "order_id": order.id,
        "order_name": order.name,
        "address_validation": validation_result,
    }