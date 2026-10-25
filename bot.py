import asyncio
import io
import logging
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("app-builder")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-6-astra").strip()
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}
DB_PATH = os.getenv("DB_PATH", "bot_users.db")
MAX_PROMPT_LENGTH = 5000

db_lock = threading.Lock()


def init_db():
    with db_lock, sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                requests INTEGER DEFAULT 0
            )
        """)
        con.commit()


def record_user(user):
    if not user:
        return
    with db_lock, sqlite3.connect(DB_PATH) as con:
        con.execute("""
            INSERT INTO users(user_id, username, first_seen, last_seen, requests)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username, last_seen=CURRENT_TIMESTAMP
        """, (user.id, user.username or ""))
        con.commit()


def increment_requests(user_id):
    with db_lock, sqlite3.connect(DB_PATH) as con:
        con.execute(
            "UPDATE users SET requests=requests+1, last_seen=CURRENT_TIMESTAMP WHERE user_id=?",
            (user_id,),
        )
        con.commit()


def get_stats():
    with db_lock, sqlite3.connect(DB_PATH) as con:
        users = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        requests = con.execute("SELECT COALESCE(SUM(requests), 0) FROM users").fetchone()[0]
    return users, requests


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 অ্যাপ তৈরি", callback_data="create")],
        [
            InlineKeyboardButton("🌐 Web App", callback_data="web"),
            InlineKeyboardButton("📱 Android App", callback_data="android"),
        ],
        [InlineKeyboardButton("💻 সোর্স কোড / সাহায্য", callback_data="help")],
    ])


def get_openai_client():
    if not OPENAI_API_KEY:
        return None
    from openai import OpenAI
    return OpenAI(api_key=OPENAI_API_KEY)


def generate_app_idea(platform: str, prompt: str) -> str:
    client = get_openai_client()
    if client is None:
        return (
            "⚠️ AI ফিচার চালু নেই।\n\n"
            "অ্যাডমিনকে OPENAI_API_KEY সেট করতে হবে।\n\n"
            "তোমার আইডিয়া পেয়েছি:\n" + prompt[:1500]
        )

    if platform == "android":
        target = (
            "Android app. Give a practical starter project using Kotlin and Jetpack Compose. "
            "Return code in clearly named files, build/setup instructions, and note any missing "
            "production details. Do not claim an APK has been compiled."
        )
    elif platform == "web":
        target = (
            "Web app. Prefer a self-contained HTML/CSS/JavaScript starter when suitable. "
            "Return complete code in clearly named files and instructions to run it."
        )
    else:
        target = (
            "Android and Web app. Give a practical plan, a web starter in HTML/CSS/JavaScript, "
            "and an Android starter in Kotlin/Jetpack Compose. Separate files clearly and explain "
            "how to run/build each. Do not claim an APK has been compiled."
        )

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=(
            "You are a careful app-building assistant. Reply in Bengali, but keep code, "
            "file names, and technical identifiers in their normal form. Ask for clarification "
            "only if absolutely necessary. Produce useful starter code, explain assumptions, "
            "include safe defaults, and never claim to have run, tested, deployed, or compiled "
            "code unless that actually happened. Never include secrets in code."
        ),
        input=f"Target: {target}\nUser's app idea:\n{prompt}",
    )
    return response.output_text or "দুঃখিত, AI থেকে কোনো লেখা পাওয়া যায়নি।"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    record_user(update.effective_user)
    context.user_data.pop("platform", None)
    await update.effective_message.reply_text(
        "👋 স্বাগতম AI App Builder Bot-এ!\n\n"
        "তুমি কী ধরনের অ্যাপ বানাতে চাও, নিচের মেনু থেকে বেছে নাও।\n"
        "তারপর অ্যাপের কাজ ও ফিচার বাংলায় লিখে পাঠাও।",
        reply_markup=main_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "ব্যবহার:\n"
        "1. /start লিখে মেনু খোলো\n"
        "2. Web, Android বা দুটোই বেছে নাও\n"
        "3. অ্যাপের নাম, কাজ, পেজ ও ফিচার লিখে পাঠাও\n"
        "4. AI কোড ও চালানোর নির্দেশনা দেবে\n\n"
        "নোট: এই বট starter code তৈরি করে। নিজে থেকে APK compile বা app publish করে না।",
        reply_markup=main_keyboard(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    record_user(query.from_user)

    choice = query.data
    if choice == "help":
        await query.message.reply_text(
            "উদাহরণ: “একটি বাংলা দোকানের অ্যাপ বানাও, যেখানে পণ্যের তালিকা, সার্চ, "
            "কার্ট ও যোগাযোগ পেজ থাকবে। পরিষ্কার নীল-সাদা ডিজাইন চাই।”\n\n"
            "অ্যাপ তৈরির জন্য মেনু থেকে Web, Android অথবা অ্যাপ তৈরি বেছে নাও।"
        )
        return

    if choice == "create":
        await query.message.reply_text(
            "কোন প্ল্যাটফর্মের অ্যাপ বানাবে?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Web App", callback_data="web")],
                [InlineKeyboardButton("📱 Android App", callback_data="android")],
                [InlineKeyboardButton("🌐 + 📱 দুটোই", callback_data="both")],
            ]),
        )
        return

    context.user_data["platform"] = {
        "web": "web", "android": "android", "both": "both"
    }.get(choice, "both")
    labels = {"web": "Web App", "android": "Android App", "both": "Android + Web App"}
    await query.message.reply_text(
        f"ঠিক আছে — {labels[context.user_data['platform']]}।\n\n"
        "এখন অ্যাপের আইডিয়া লিখে পাঠাও। সম্ভব হলে অ্যাপের নাম, কী কাজ করবে, "
        "কোন কোন পেজ লাগবে এবং পছন্দের ডিজাইন উল্লেখ করো।\n\n"
        "বাতিল করতে /start লিখতে পারো।"
    )


async def handle_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    record_user(user)
    idea = (update.effective_message.text or "").strip()

    if not context.user_data.get("platform"):
        await update.effective_message.reply_text(
            "আগে মেনু থেকে Web App, Android App অথবা দুটোই বেছে নাও।",
            reply_markup=main_keyboard(),
        )
        return

    if not idea:
        await update.effective_message.reply_text("অ্যাপের আইডিয়াটি টেক্সট হিসেবে পাঠাও।")
        return
    if len(idea) > MAX_PROMPT_LENGTH:
        await update.effective_message.reply_text(
            f"বার্তাটি অনেক বড়। অনুগ্রহ করে {MAX_PROMPT_LENGTH} অক্ষরের মধ্যে পাঠাও।"
        )
        return

    platform = context.user_data["platform"]
    await update.effective_chat.send_action(ChatAction.TYPING)
    status = await update.effective_message.reply_text(
        "🛠️ তোমার অ্যাপের পরিকল্পনা ও কোড তৈরি করছি…"
    )

    try:
        result = await asyncio.to_thread(generate_app_idea, platform, idea)
        increment_requests(user.id)
        # Telegram messages have a length limit; send long answers as a text file.
        if len(result) > 3800:
            data = io.BytesIO(result.encode("utf-8"))
            data.name = "app_builder_output.txt"
            await update.effective_message.reply_document(
                document=data,
                caption="তোমার AI-generated app plan ও source code (টেক্সট ফাইল)।",
            )
            await status.edit_text("✅ কাজ শেষ! কোডের ফাইলটি উপরে পাঠানো হয়েছে।")
        else:
            await status.edit_text(result)
        await update.effective_message.reply_text(
            "আরেকটি অ্যাপ তৈরি করতে নিচের মেনু ব্যবহার করো।",
            reply_markup=main_keyboard(),
        )
    except Exception:
        log.exception("App generation failed")
        await status.edit_text(
            "দুঃখিত, কোড তৈরি করা যায়নি। API key, API billing/limit এবং সার্ভারের লগ পরীক্ষা করো।"
        )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id not in ADMIN_IDS:
        await update.effective_message.reply_text("⛔ এই কমান্ড শুধু অ্যাডমিনের জন্য।")
        return
    users, requests = get_stats()
    await update.effective_message.reply_text(
        "🛡️ Admin Dashboard\n\n"
        f"👥 মোট ব্যবহারকারী: {users}\n"
        f"🧠 সফল AI অনুরোধ: {requests}\n\n"
        "এই সংস্করণে অ্যাডমিন পরিসংখ্যান /admin কমান্ডে দেখা যায়।"
    )


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/health"):
            self.send_response(404)
            self.end_headers()
            return
        body = b"Telegram AI App Builder is running."
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log.info("Health server listening on port %s", port)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required.")
    init_db()
    start_health_server()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_idea))
    log.info("Telegram bot started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
