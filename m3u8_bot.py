import logging
import asyncio
import os
import requests
import m3u8
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ====== CONFIG ======
TOKEN = os.getenv("BOT_TOKEN")  # Koyeb secret se lega

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
    "Origin": "https://appx-play.akamai.net.in",
    "Referer": "https://appx-play.akamai.net.in/",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd"
}

# ====== Downloader ======
def download_video(m3u8_url, output_file="output.mp4"):
    print("[*] Fetching playlist...")
    m3u8_obj = m3u8.load(m3u8_url, headers=headers)

    base_url = m3u8_url.rsplit("/", 1)[0] + "/"
    segment_urls = [
        seg.uri if seg.uri.startswith("http") else base_url + seg.uri
        for seg in m3u8_obj.segments
    ]
    print(f"[*] Found {len(segment_urls)} segments.")

    os.makedirs("segments", exist_ok=True)
    ts_files = []

    for i, url in enumerate(segment_urls):
        ts_file = f"segments/{i}.ts"
        ts_files.append(ts_file)

        if not os.path.exists(ts_file) or os.path.getsize(ts_file) == 0:
            print(f"Downloading {i+1}/{len(segment_urls)} ...")
            r = requests.get(url, headers=headers, stream=True)
            if r.status_code == 200:
                with open(ts_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        f.write(chunk)
            else:
                print(f"[!] Failed {i+1}, status {r.status_code}")

    print("[*] Merging into MP4...")
    with open("segments/files.txt", "w", encoding="utf-8") as f:
        for ts in ts_files:
            f.write(f"file '{os.path.abspath(ts)}'\n")

    subprocess.run([
        "ffmpeg", "-f", "concat", "-safe", "0", "-i",
        "segments/files.txt", "-c", "copy", output_file
    ])

    print(f"[*] Done! Saved as {output_file}")

# ====== Telegram Bot ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me an M3U8 link and I’ll download it for you!")

async def handle_m3u8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m3u8_url = update.message.text.strip()
    await update.message.reply_text("⏳ Downloading video... Please wait.")

    output_file = "final_video.mp4"
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, download_video, m3u8_url, output_file)

        await update.message.reply_video(video=open(output_file, "rb"))
        os.remove(output_file)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_m3u8))
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()