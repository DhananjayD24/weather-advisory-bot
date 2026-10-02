import asyncio

from app.services.weather_service import fetch_weather


async def main():
    # Bhopal coordinates
    latitude = 23.2599
    longitude = 77.4126

    weather = await fetch_weather(
        latitude,
        longitude,
    )

    print("Current weather:")
    print(weather["current"])

    print("\nHourly fields:")
    print(weather["hourly"].keys())


if __name__ == "__main__":
    asyncio.run(main())