from villascout.models.domain import SourceListing, SourceName, Villa


def villa(place_id: str = "place-1") -> Villa:
    return Villa(
        name="Casa Verde",
        location="Igatpuri",
        address="Lake Road",
        latitude=19.7,
        longitude=73.5,
        source_listing=SourceListing(
            source=SourceName.GOOGLE_PLACES,
            external_id=place_id,
            source_url="https://maps.google.com/example",
            raw_payload={"place_id": place_id},
        ),
    )
