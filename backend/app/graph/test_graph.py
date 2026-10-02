import asyncio

from app.graph.graph import graph


async def main():
    result = await graph.ainvoke({
        "messages": [],
        "current_query": "Is it safe to cycle in Bhopal today?",
        "location": "Bhopal",
        "activity": "cycling",
        "time_context": "today",
        "user_type": None,
        "matched_sops": [],
    })

    print(result)


if __name__ == "__main__":
    asyncio.run(main())