"""
Minimal login example.

Run:
    python examples/login.py

Set your credentials via environment variables so they don't end up in
shell history or source control:

    export INTERPALS_USERNAME=alice
    export INTERPALS_PASSWORD=s3cr3t
"""
import asyncio
import os

from interpals_client import InterpalsClient, AuthError


async def main() -> None:
    username = os.environ["INTERPALS_USERNAME"]
    password = os.environ["INTERPALS_PASSWORD"]

    async with InterpalsClient(username, password) as client:
        try:
            await client.login()
        except AuthError as e:
            print(f"Login failed: {e}")
            return

        print(f"Logged in as {username}")


if __name__ == "__main__":
    asyncio.run(main())
