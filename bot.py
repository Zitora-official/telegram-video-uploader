import os
import tempfile
from urllib.parse import urlparse

import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.environ["BOT_TOKEN"]
MAX_BYTES = 49 * 1024 * 1024

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text:
        return

    url = message.text.strip()
    parsed = urlparse(url)

    if parsed.scheme != "https" or not parsed.path.lower().endswith(".mp4"):
        await message.reply_text("Send a direct HTTPS MP4 download link.")
        return

    try:
        await message.reply_text("Downloading on the server and uploading to Telegram…")

        with requests.get(
            url, stream=True, timeout=(20, 90),
            headers={"User-Agent": "Mozilla/5.0"}
        ) as response:
            response.raise_for_status()
            length = int(response.headers.get("Content-Length", "0"))

            if length > MAX_BYTES:
                await message.reply_text("This bot supports videos up to 49 MB.")
                return

            with tempfile.NamedTemporaryFile(suffix=".mp4") as video:
                total = 0

                for chunk in response.iter_content(256 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)

                    if total > MAX_BYTES:
                        await message.reply_text("Video exceeds the 49 MB limit.")
                        return

                    video.write(chunk)

                video.flush()
                video.seek(0)

                await context.bot.send_video(
                    chat_id=message.chat_id,
                    video=video,
                    caption="Uploaded from download link",
                    supports_streaming=True,
                    read_timeout=180,
                    write_timeout=180,
                )

    except Exception as error:
        print(type(error).__name__, str(error))
        await message.reply_text(
            "Upload failed. The link may be expired, restricted, or too large."
        )

app = Application.builder().token(TOKEN).build()
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)
)
app.run_polling()
