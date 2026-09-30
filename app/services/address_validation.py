import logging
import httpx

from app.config import settings
from app.models.address import Address


logger = logging.getLogger(__name__)


class AddressValidationService:

    async def validate(self, address: Address) -> dict:
        result = await self._validate_with_google(address)

        if not result:
            return {
                "status": "review",
                "reason": "Google Address Validation API failed",
            }

        verdict = result.get("verdict", {})
        validated_address = result.get("address", {})

        components = validated_address.get(
            "addressComponents",
            []
        )

        formatted_address = validated_address.get(
            "formattedAddress"
        )

        checks = {
            "possible_next_action": (
                verdict.get("possibleNextAction") == "ACCEPT"
            ),

            "address_complete": (
                verdict.get("addressComplete") is True
            ),

            "premise_granularity": (
                verdict.get("validationGranularity")
                in {"PREMISE", "SUB_PREMISE"}
            ),

            "premise_confirmed": self._is_component_acceptable(
                components,
                {"premise", "subpremise"},
                {"CONFIRMED"},
            ),

            "postal_code_confirmed": self._is_component_acceptable(
                components,
                {"postal_code"},
                {"CONFIRMED"},
            ),

            "locality_confirmed": self._is_component_acceptable(
                components,
                {
                    "locality",
                    "postal_town",
                    "administrative_area_level_2",
                },
                {"CONFIRMED"},
            ),

            "route_acceptable": self._is_component_acceptable(
                components,
                {"route"},
                {
                    "CONFIRMED",
                    "UNCONFIRMED_BUT_PLAUSIBLE",
                },
            ),
        }

        accepted = all(checks.values())

        if accepted:
            return {
                "status": "accept",
                "validated_address": formatted_address,
                "checks": checks,
            }

        failed_checks = [
            name
            for name, passed in checks.items()
            if not passed
        ]

        return {
            "status": "review",
            "validated_address": formatted_address,
            "failed_checks": failed_checks,
            "checks": checks,
        }

    async def _validate_with_google(
        self,
        address: Address,
    ) -> dict | None:

        url = (
            "https://addressvalidation.googleapis.com/"
            "v1:validateAddress"
        )

        full_address = ", ".join(
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


        payload = {
            "address": {
                "regionCode": "IN",
                "addressLines": [full_address],
            }
        }

        logger.info(
            "Google Address Validation request: %s",
            payload,
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    params={
                        "key": settings.google_maps_api_key,
                    },
                    json=payload,
                )

            logger.info(
                "Google Address Validation response status=%s body=%s",
                response.status_code,
                response.text,
            )

            response.raise_for_status()

            data = response.json()

            return data.get("result")

        except httpx.HTTPError as exc:
            logger.exception(
                f"Google address validation failed: {exc}"
            )
            return None

    def _is_component_acceptable(
        self,
        components: list[dict],
        component_types: set[str],
        allowed_levels: set[str],
    ) -> bool:
        for component in components:
            if component.get("componentType") not in component_types:
                continue

            return component.get("confirmationLevel") in allowed_levels

        return False