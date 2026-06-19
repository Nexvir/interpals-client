"""
Fetch a single user's full profile.

Run:
    export INTERPALS_USERNAME=alice
    export INTERPALS_PASSWORD=s3cr3t
    python examples/profile.py some_username
"""
import asyncio
import os
import sys

from interpals_client import InterpalsClient, ProfileNotFoundError


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python examples/profile.py <username>")
        return

    target = sys.argv[1]
    username = os.environ["INTERPALS_USERNAME"]
    password = os.environ["INTERPALS_PASSWORD"]

    async with InterpalsClient(username, password) as client:
        await client.login()

        try:
            profile = await client.get_profile(target)
        except ProfileNotFoundError:
            print(f"No profile found for {target!r}")
            return

        print(profile.summary())
        print()
        print(profile.bio)


if __name__ == "__main__":
    asyncio.run(main())
