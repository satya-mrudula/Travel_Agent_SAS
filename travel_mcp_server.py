
from mcp.server.fastmcp import FastMCP
import requests
import time

mcp = FastMCP("TravelPlanningAgent")

# OpenStreetMap configuration
HEADERS = {
    "User-Agent": "TravelPlanningAgent/1.0 (educational project)"
}

# Cache city coordinates to avoid repeated geocoding
city_cache = {}


@mcp.tool()
def search_destinations(city: str) -> list:
    """Search tourist attractions in any city using OpenStreetMap."""

    try:
        # Step 1: Find city coordinates
        if city.lower() not in city_cache:

            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": city,
                    "format": "json",
                    "limit": 1
                },
                headers=HEADERS,
                timeout=15
            )

            response.raise_for_status()
            results = response.json()

            if not results:
                return [f"No location found for {city}."]

            location = results[0]

            latitude = float(location["lat"])
            longitude = float(location["lon"])

            city_cache[city.lower()] = (
                latitude,
                longitude
            )

            # Respect Nominatim's one-request-per-second policy
            time.sleep(1.1)

        else:
            latitude, longitude = city_cache[city.lower()]

        # Step 2: Search tourist attractions
        query = f"""
        [out:json][timeout:25];

        (
          nwr(around:12000,{latitude},{longitude})
          ["name"]
          ["tourism"~"attraction|museum|viewpoint|zoo|theme_park"];

          nwr(around:12000,{latitude},{longitude})
          ["name"]
          ["historic"];

          nwr(around:12000,{latitude},{longitude})
          ["name"]
          ["leisure"="park"];
        );

        out center tags 30;
        """

        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            headers=HEADERS,
            timeout=45
        )

        response.raise_for_status()

        data = response.json()

        attractions = []
        seen = set()

        for place in data.get("elements", []):

            tags = place.get("tags", {})
            name = tags.get("name")

            if not name or name.lower() in seen:
                continue

            seen.add(name.lower())

            category = (
                tags.get("tourism")
                or tags.get("historic")
                or tags.get("leisure")
                or "Tourist attraction"
            )

            attractions.append({
                "name": name,
                "category": category
            })

            if len(attractions) >= 15:
                break

        if not attractions:
            return [
                f"No mapped tourist attractions found near {city}."
            ]

        return attractions

    except requests.RequestException as e:
        return [
            f"Could not retrieve attraction data: {str(e)}"
        ]

    except Exception as e:
        return [
            f"Destination search failed: {str(e)}"
        ]


@mcp.tool()
def suggest_accommodation(budget: float) -> str:
    """Suggest accommodation according to budget."""

    if budget <= 5000:
        return "Budget hotel: Rs. 1000 per night"

    elif budget <= 15000:
        return "Standard hotel: Rs. 2000 per night"

    else:
        return "Premium hotel: Rs. 3500 per night"


@mcp.tool()
def suggest_transport() -> list:
    """Suggest transportation options."""

    return [
        "Metro - affordable city travel",
        "Auto - short-distance travel",
        "Cab - comfortable family travel",
        "Bus - economical transportation"
    ]


@mcp.tool()
def estimate_expenses(
    days: int,
    people: int,
    hotel_cost: float,
    budget: float
) -> dict:
    """Calculate estimated travel expenses."""

    accommodation = hotel_cost * (days - 1)
    food = 250 * people * days
    transport = 500 * days
    sightseeing = 200 * people

    total = (
        accommodation + food
        + transport + sightseeing
    )

    return {
        "Accommodation": accommodation,
        "Food": food,
        "Transport": transport,
        "Sightseeing": sightseeing,
        "Total": total,
        "Budget": budget,
        "Remaining": budget - total
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
