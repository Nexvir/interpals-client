"""
Read your inbox and reply to the first thread.

Run:
    export INTERPALS_USERNAME=alice
    export INTERPALS_PASSWORD=s3cr3t
    python examples/messages.py
"""
import asyncio
import os

from interpals_client import InterpalsClient, SendMessageError


async def main() -> None:
    username = os.environ["INTERPALS_USERNAME"]
    password = os.environ["INTERPALS_PASSWORD"]

    async with InterpalsClient(username, password) as client:
        await client.login()

        threads = await client.get_threads()
        print(f"{len(threads)} threads in inbox")
        for t in threads:
            unread = " (unread)" if t.has_unread else ""
            print(f"- {t.display_name or t.username}{unread}: {t.snippet}")

        if not threads:
            return

        first = threads[0]
        msgs = await client.get_messages(first.id, limit=5)
        print(f"\nLast {len(msgs)} messages with {first.username}:")
        for m in reversed(msgs):
            who = "me" if m.is_own else m.author.name
            print(f"  [{who}] {m.content}")

        try:
            await client.send_message(first.id, "Hey! Just replying via the API.")
            print("\nReply sent.")
        except SendMessageError as e:
            print(f"\nCould not send reply: {e}")


if __name__ == "__main__":
    asyncio.run(main())
