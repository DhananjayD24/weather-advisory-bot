import asyncio

from app.services.location_service import resolve_location


async def main():
    result = await resolve_location("Bhopal")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())