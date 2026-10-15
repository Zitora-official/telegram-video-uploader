import os
import tempfile
from urllib.parse import urlparse

import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.environ["BOT_TOKEN"]
GROUP_ID = -1003589637169
MAX_BYTES = 512 * 1024 * 1024

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text:
        return

    url = message.text.strip().split()[0].rstrip(".,)>]")
    parsed = urlparse(url)

    if parsed.scheme != "https" or not parsed.path.lower().endswith(".mp4"):
        await message.reply_text("Send a direct HTTPS MP4 download link.")
        return

    try:
        await message.reply_text("Downloading on the server…")

        with requests.get(
            url, stream=True, timeout=(20, 90),
            headers={"User-Agent": "Mozilla/5.0"}
        ) as r:
            r.raise_for_status()

            if int(r.headers.get("Content-Length", "0")) > MAX_BYTES:
                await message.reply_text("Video exceeds the 49 MB limit.")
                return

            with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
                total = 0
                for chunk in r.iter_content(256 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_BYTES:
                        await message.reply_text("Video exceeds the 49 MB limit.")
                        return
                    f.write(chunk)

                f.flush()
                f.seek(0)
                await context.bot.send_video(
                    chat_id=GROUP_ID,
                    video=f,
                    caption="Uploaded from download link",
                    supports_streaming=True,
                    read_timeout=180,
                    write_timeout=180,
                )

        await message.reply_text("Video uploaded to your group.")

    except Exception as e:
        print(type(e).__name__, str(e))
        await message.reply_text(
            "Upload failed. Check the link, file size, and bot permissions."
        )

app = Application.builder().token(TOKEN).build()
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)
)
app.run_polling()
