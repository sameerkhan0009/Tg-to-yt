import os
from pyrogram import Client, filters
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# ==== Telegram Bot Setup ====
API_ID = int(os.getenv(""))   # your Telegram API ID
API_HASH = os.getenv("05e0d957751c827aa03494f503ab54fe")    # your Telegram API Hash
BOT_TOKEN = os.getenv("7627011309:AAHf2txD-WsYk--0-oX3s0XKDWDnqurub6w")  # BotFather token

bot = Client("yt_uploader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ==== YouTube Authentication ====
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def youtube_auth():
    creds = None
    if os.path.exists("token.pkl"):
        with open("token.pkl", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=8080)
        with open("token.pkl", "wb") as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)

youtube = youtube_auth()

# ==== Bot Handler ====
@bot.on_message(filters.video)
async def upload_video(client, message):
    file_path = await message.download()
    await message.reply_text("📤 Uploading to YouTube...")

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Uploaded via Telegram Bot",
                "description": "This video was uploaded directly from Telegram.",
                "tags": ["Telegram", "YouTube", "Bot"],
                "categoryId": "22"
            },
            "status": {"privacyStatus": "private"}
        },
        media_body=MediaFileUpload(file_path)
    )
    response = request.execute()

    video_id = response["id"]
    yt_link = f"https://youtu.be/{video_id}"
    await message.reply_text(f"✅ Uploaded Successfully!\n{yt_link}")

    os.remove(file_path)

# ==== Run Bot ====
bot.run()
