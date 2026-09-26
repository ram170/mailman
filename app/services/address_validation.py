import httpx

from app.models.address import Address


class AddressValidationService:

    async def validate(self, address: Address) -> dict:
        if not address.zip:
            return {
                "status": "review",
                "reason": "Pincode is missing",
            }

        pincode_data = await self._lookup_pincode(address.zip)

        if not pincode_data:
            return {
                "status": "review",
                "reason": "Pincode could not be verified",
            }

        match = self._location_matches_address(
            address=address,
            pincode_data=pincode_data,
        )

        if not match:
            return {
                "status": "review",
                "reason": "Address location does not match pincode",
            }

        return {
            "status": "valid",
            "pincode": address.zip,
            **match,
        }

    async def _lookup_pincode(self, pincode: str) -> dict | None:
        url = f"https://api.postalpincode.in/pincode/{pincode}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)

            if response.status_code != 200:
                return None

            data = response.json()

        except (httpx.TimeoutException, httpx.RequestError):
            return None

        if not data:
            return None

        result = data[0]

        if result.get("Status") != "Success":
            return None

        post_offices = result.get("PostOffice") or []

        if not post_offices:
            return None

        return {
            "post_offices": [
                {
                    "name": office.get("Name"),
                    "district": office.get("District"),
                    "state": office.get("State"),
                    "region": office.get("Region"),
                    "division": office.get("Division"),
                    "block": office.get("Block"),
                }
                for office in post_offices
            ]
        }

    def _location_matches_address(
        self,
        address: Address,
        pincode_data: dict,
    ) -> dict | None:
        address_text = " ".join(
            filter(
                None,
                [
                    address.address1,
                    address.address2,
                    address.city,
                    address.province,
                ],
            )
        ).lower()

        for office in pincode_data["post_offices"]:
            possible_locations = [
                office.get("name"),
                office.get("block"),
                office.get("district"),
            ]

            for location in possible_locations:
                if location and location.lower() in address_text:
                    return {
                        "matched_location": location,
                        "state": office.get("state"),
                        "district": office.get("district"),
                    }

        return None