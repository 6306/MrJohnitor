import discord
import markovify
import os
import json
import time
import re
import asyncio
import random

# <<< SET THIS TO YOUR BOT'S TOKEN >>>
TOKEN = "THISISNOTAREALTOKEN"
MESSAGE_FILE = "messages.txt"
MODEL_FILE = "model.json"
BANNED_USERS_FILE = "banned_users.json"

# <<< SET THIS TO YOUR DISCORD USER ID >>>
OWNER_ID = 12345678901234567890

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

collected_messages = []
last_response = None
last_active_channel = None
saving_lock = asyncio.Lock()

"""Fit this list with words you do not want your bot to learn. They will be stored in the model.json file, but the filter catches it before sending the message out."""
BANNED_WORDS = [
    "nigga", "nigger", "fag", "faggot", "retard", "tranny", "kike", "chink", "spic", "coon",
    "wetback", "towelhead", "sandnigger", "gook", "dyke", "slut", "whore", "rapist", "rape",
    "raped", "pedo"
]

# === BANNED USERS HANDLING ===
# Internally store banned users as raw integer IDs, but in JSON as "<@id>".
banned_users = set()


def load_banned_users():
    """Load banned users from banned_users.json as <@id> strings."""
    global banned_users
    if os.path.exists(BANNED_USERS_FILE):
        try:
            with open(BANNED_USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert "<@123>" → 123
            for entry in data:
                m = re.match(r"<@(\d+)>", entry)
                if m:
                    banned_users.add(int(m.group(1)))

            print(f"[Loaded {len(banned_users)} banned users]")
        except Exception as e:
            print(f"[Failed to load {BANNED_USERS_FILE}] {e}")
            banned_users = set()
    else:
        banned_users = set()


def save_banned_users():
    """Save banned users to banned_users.json as <@id> strings."""
    try:
        # Convert 123 → "<@123>"
        formatted = [f"<@{uid}>" for uid in banned_users]

        with open(BANNED_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(formatted, f, indent=2)

        print("[Banned users saved]")
    except Exception as e:
        print(f"[Failed to save {BANNED_USERS_FILE}] {e}")


def mask_banned_users(text: str) -> str:
    """
    Replace any banned user mention (<@id> or <@!id>) with Unknown.
    This applies to ALL bot messages, including command responses.
    """
    if not text:
        return text
    for uid in banned_users:
        text = text.replace(f"<@{uid}>", "Non-mentionable User")
        text = text.replace(f"<@!{uid}>", "Non-mentionable User")
    return text


load_banned_users()

# === Load messages ===
if os.path.exists(MESSAGE_FILE):
    with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
        collected_messages = f.read().splitlines()

# === Load model ===
markov_model = None
if os.path.exists(MODEL_FILE):
    try:
        with open(MODEL_FILE, "r", encoding="utf-8") as f:
            model_json = json.load(f)
            markov_model = markovify.NewlineText.from_json(model_json)
            print("[Model loaded from model.json]")
    except Exception as e:
        print(f"[Failed to load model.json] {e}")


# === Utility functions ===
def clean_message(text):
    for word in BANNED_WORDS:
        text = re.sub(rf"\b{re.escape(word)}\b", "OOPS!", text, flags=re.IGNORECASE)
    return text


async def save_message(msg):
    """Safely append a message once to the file."""
    msg = msg.strip()
    if not msg:
        return
    async with saving_lock:
        if msg not in collected_messages[-5:]:
            collected_messages.append(msg)
            with open(MESSAGE_FILE, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
            if len(collected_messages) % 5 == 0:
                build_model_and_save()


def build_model_and_save():
    global markov_model
    if collected_messages:
        try:
            text = "\n".join(collected_messages)
            markov_model = markovify.NewlineText(text, state_size=1)
            with open(MODEL_FILE, "w", encoding="utf-8") as f:
                f.write(markov_model.to_json())
            print("[Model rebuilt and saved to model.json]")
        except Exception as e:
            print(f"[Error rebuilding model] {e}")


def generate_message():
    global last_response
    if not markov_model:
        return "*[Not enough data]*"

    # Try full sentences first
    for _ in range(10):
        msg = markov_model.make_sentence(tries=100)
        if msg and msg != last_response:
            msg = clean_message(msg)
            msg = mask_banned_users(msg)
            last_response = msg
            return msg

    # Fallback to short sentences
    for _ in range(10):
        msg = markov_model.make_short_sentence(100, tries=100)
        if msg and msg != last_response:
            msg = clean_message(msg)
            msg = mask_banned_users(msg)
            last_response = msg
            return msg

    return "*[Not enough data]*"


async def send_with_typing(channel, content, reply_to=None, force_no_reply=False):
    if reply_to and reply_to.author.id in banned_users:
        force_no_reply = True

    # Always mask banned user mentions in outgoing content
    content = mask_banned_users(content)

    async with channel.typing():
        await asyncio.sleep(random.uniform(1, 3))
        if reply_to and not force_no_reply:
            sent = await reply_to.reply(content)
        else:
            sent = await channel.send(content)
    await save_message(content)
    return sent


async def self_conversation_loop(message):
    """Bot sends self messages (not threaded) for 30 seconds, 7–15 seconds apart."""
    start_time = time.time()
    while time.time() - start_time < 30:
        await asyncio.sleep(random.randint(7, 15))
        response = generate_message()
        await send_with_typing(message.channel, response, force_no_reply=True)
        print(f"[Self-chat] {response}")
        await save_message(response)


async def background_insanity():
    """Randomly triggers self-talk in the last active channel, 30 seconds max."""
    global last_active_channel
    await client.wait_until_ready()
    while not client.is_closed():
        await asyncio.sleep(random.randint(900, 5400))  # every 15–90 minutes
        if last_active_channel:
            try:
                print("[Random self-talk triggered]")
                response = generate_message()
                fake_msg = await send_with_typing(last_active_channel, response, force_no_reply=True)
                await self_conversation_loop(fake_msg)
            except Exception as e:
                print(f"[Error in background insanity loop] {e}")


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user} (ID: {client.user.id})")
    client.loop.create_task(background_insanity())


@client.event
async def on_message(message: discord.Message):
    global last_active_channel
    last_active_channel = message.channel

    msg = message.content.strip()
    if not msg:
        return

    # Ignore its own messages for triggering responses, but still learn from them
    if message.author.id == client.user.id:
        await save_message(msg)
        return

    print(f"[{message.author}] {msg}")

    # Log all non-self messages
    await save_message(msg)

    lower_msg = msg.lower()

    # ===== Owner-only ban management commands =====

    # !add @user / !add <id>
    if lower_msg.startswith("!add"):
        if message.author.id != OWNER_ID:
            await send_with_typing(
                message.channel,
                "❌ You don't have permission to use this command.",
                reply_to=message
            )
            return

        parts = msg.split(maxsplit=1)
        if len(parts) < 2:
            await send_with_typing(
                message.channel,
                "Usage: `!add @user` or `!add <user_id>`",
                reply_to=message
            )
            return

        target_user = None

        # If a mention is present, use that
        if message.mentions:
            target_user = message.mentions[0]
        else:
            # Try to interpret the argument as a user ID
            try:
                uid = int(parts[1])
                target_user = await client.fetch_user(uid)
            except Exception:
                target_user = None

        if not target_user:
            await send_with_typing(
                message.channel,
                "❌ Could not find that user. Mention them or use a valid user ID.",
                reply_to=message
            )
            return

        banned_users.add(target_user.id)
        save_banned_users()

        await send_with_typing(
            message.channel,
            f"✅ <@{target_user.id}> has been added to the ban list. They will no longer be mentioned by me.",
            reply_to=message
        )
        return

    # !remove @user / !remove <id>
    if lower_msg.startswith("!remove"):
        if message.author.id != OWNER_ID:
            await send_with_typing(
                message.channel,
                "❌ You don't have permission to use this command.",
                reply_to=message
            )
            return

        parts = msg.split(maxsplit=1)
        if len(parts) < 2:
            await send_with_typing(
                message.channel,
                "Usage: `!remove @user` or `!remove <user_id>`",
                reply_to=message
            )
            return

        target_user = None
        target_id = None

        if message.mentions:
            target_user = message.mentions[0]
            target_id = target_user.id
        else:
            try:
                target_id = int(parts[1])
            except Exception:
                target_id = None

        if target_id is None:
            await send_with_typing(
                message.channel,
                "❌ Could not parse that user. Mention them or use a valid user ID.",
                reply_to=message
            )
            return

        if target_id in banned_users:
            banned_users.remove(target_id)
            save_banned_users()
            await send_with_typing(
                message.channel,
                f"✅ Removed <@{target_id}> from the ban list.",
                reply_to=message
            )
        else:
            await send_with_typing(
                message.channel,
                f"ℹ <@{target_id}> is not in the ban list.",
                reply_to=message
            )
        return

    # !listbanned
    if lower_msg.startswith("!listbanned"):
        if message.author.id != OWNER_ID:
            await send_with_typing(
                message.channel,
                "❌ You don't have permission to use this command.",
                reply_to=message
            )
            return

        if not banned_users:
            await send_with_typing(
                message.channel,
                "🚫 Ban list is currently **empty**.",
                reply_to=message
            )
            return

        mentions = [f"<@{uid}>" for uid in banned_users]
        text = "🚫 **Banned users:**\n" + ", ".join(mentions)
        await send_with_typing(message.channel, text, reply_to=message)
        return

    # !clearbans
    if lower_msg.startswith("!clearbans"):
        if message.author.id != OWNER_ID:
            await send_with_typing(
                message.channel,
                "❌ You don't have permission to use this command.",
                reply_to=message
            )
            return

        banned_users.clear()
        save_banned_users()
        await send_with_typing(
            message.channel,
            "🧹 Ban list cleared. `banned_users.json` has been reset.",
            reply_to=message
        )
        return

    # ===== Other commands =====

    if lower_msg.startswith("!chaininfo"):
        await send_with_typing(
            message.channel,
            f"🧠 Collected messages: {len(collected_messages)}\n"
            f"💾 Model saved: {'Yes' if os.path.exists(MODEL_FILE) else 'No'}",
            reply_to=message
        )
        return

    if lower_msg.startswith("!unique"):
        unique_count = len(set(collected_messages))
        await send_with_typing(
            message.channel,
            f"📊 Unique messages: {unique_count} / Total: {len(collected_messages)}",
            reply_to=message
        )
        return

    if lower_msg.startswith("!save"):
        start = time.time()
        build_model_and_save()
        await send_with_typing(
            message.channel,
            f"✅ Model rebuilt and saved.\n🕒 Took {time.time() - start:.2f}s\n📜 Messages: {len(collected_messages)}",
            reply_to=message
        )
        return

    # Mention / reply detection
    mentioned = client.user in message.mentions
    is_reply = (
        message.reference
        and message.reference.resolved
        and message.reference.resolved.author.id == client.user.id
    )

    # Self mention triggers 30-second insanity (non-threaded)
    if mentioned and message.author.id == client.user.id:
        print("[Self-mention detected: starting self-talk for 30 seconds]")
        await self_conversation_loop(message)
        return

    # Normal mention/reply behavior (threaded)
    if mentioned or is_reply:
        response = generate_message()
        await send_with_typing(message.channel, response, reply_to=message)
        await save_message(response)


client.run(TOKEN)
