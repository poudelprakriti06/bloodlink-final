from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


def get_coordinates(district, municipality, ward, area):

    geolocator = Nominatim(user_agent="bloodlink")

    # Try detailed address first
    queries = [
        f"{area}, {municipality}, {district}, Nepal",
        f"{area}, {district}, Nepal",
        f"{municipality}, {district}, Nepal",
    ]

    try:
        for address in queries:

            location = geolocator.geocode(address)

            if location:
                return {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                }

        return None

    except (GeocoderTimedOut, GeocoderServiceError):
        return None