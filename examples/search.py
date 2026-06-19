"""
Search for users with filters.

Run:
    export INTERPALS_USERNAME=alice
    export INTERPALS_PASSWORD=s3cr3t
    python examples/search.py
"""
import asyncio
import os

from interpals_client import InterpalsClient


async def main() -> None:
    username = os.environ["INTERPALS_USERNAME"]
    password = os.environ["INTERPALS_PASSWORD"]

    async with InterpalsClient(username, password) as client:
        await client.login()

        users = await client.search(
            country="Germany",
            age_min=20,
            age_max=30,
            native_lang="German",
            learning_lang="English",
            online_only=False,
        )

        print(f"Found {len(users)} users")
        for u in users:
            print(f"- {u.display_name} ({u.username}) — {u.city}, {u.country}")


if __name__ == "__main__":
    asyncio.run(main())
