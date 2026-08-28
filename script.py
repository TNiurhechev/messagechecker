import os
import threading

from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession


API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
TELEGRAM_SESSION = os.environ["TELEGRAM_SESSION"]

TARGET_CHAT_ID = None

if TARGET_CHAT_ID:
    TARGET_CHAT_ID = int(TARGET_CHAT_ID)


client = TelegramClient(
    StringSession(TELEGRAM_SESSION),
    API_ID,
    API_HASH
)


def is_game_message(message):
    text = message.raw_text or ""

    return (
        "Participants (max." in text
        and message.buttons is not None
    )


def find_join_button(message):
    if not message.buttons:
        return None

    join_symbols = {"+", "＋", "➕", "✚", "⊕"}

    for row_index, row in enumerate(message.buttons):
        for column_index, button in enumerate(row):
            text = (button.text or "").strip()

            if text in join_symbols:
                return row_index, column_index, text

    if len(message.buttons) == 1 and len(message.buttons[0]) == 2:
        button = message.buttons[0][0]
        return 0, 0, button.text

    return None


@client.on(events.NewMessage)
async def auto_join(event):
    message = event.message

    # Ignore all other chats once TARGET_CHAT_ID is configured
    if TARGET_CHAT_ID is not None and event.chat_id != TARGET_CHAT_ID:
        return

    if not is_game_message(message):
        return

    print("\n" + "=" * 60)
    print("FOOTBALL GAME DETECTED")
    print("Chat ID:", event.chat_id)
    print("Message ID:", message.id)
    print("Message:")
    print(message.raw_text)
    print("=" * 60)

    join_button = find_join_button(message)

    if join_button is None:
        print("Couldn't confidently identify the JOIN button. Not clicking.")
        return

    row, column, button_text = join_button

    print(
        f"JOIN button found: [{row}, {column}] "
        f"text={button_text!r}"
    )

    try:
        await message.click(row, column)
        print("JOIN BUTTON CLICKED SUCCESSFULLY")

    except Exception as e:
        print(f"FAILED TO CLICK JOIN BUTTON: {type(e).__name__}: {e}")


app = Flask(__name__)


@app.route("/")
def home():
    return "Football auto-join is running.", 200


@app.route("/health")
def health():
    return "OK", 200


def run_web_server():
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )


async def main():
    print("Connecting to Telegram...")

    await client.start()

    me = await client.get_me()

    print(
        f"Logged into Telegram as "
        f"{me.first_name} (@{me.username})"
    )

    print("Football auto-join is running.")
    print("Waiting for new signup messages...")

    await client.run_until_disconnected()


if __name__ == "__main__":
    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )
    web_thread.start()

    with client:
        client.loop.run_until_complete(main())