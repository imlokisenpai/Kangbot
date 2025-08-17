import os
import aiohttp
import asyncio
import subprocess
from telegram import Update, InputSticker
from telegram.ext import Application, CommandHandler, ContextTypes

# safer: read token from environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")

# Download helper
async def download_file(file, path, context):
    new_file = await context.bot.get_file(file.file_id)
    await new_file.download_to_drive(path)

# Convert photo → webp
def convert_to_webp(src, dest):
    subprocess.run([
        "ffmpeg", "-y", "-i", src,
        "-vf", "scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:-1:-1:color=white",
        "-lossless", "1", "-compression_level", "6", "-qscale", "90",
        dest
    ])

# Convert gif/mp4 → webm (video sticker)
def convert_to_webm(src, dest):
    subprocess.run([
        "ffmpeg", "-y", "-i", src,
        "-an", "-c:v", "libvpx-vp9",
        "-vf", "scale=512:512:force_original_aspect_ratio=decrease",
        "-b:v", "500K", "-crf", "30", "-pix_fmt", "yuva420p",
        dest
    ])

async def kang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a sticker/photo/gif with /kang.")
        return

    user = update.effective_user
    msg = update.message.reply_to_message
    emoji = "🤔"  # default emoji

    pack_short_name = f"{user.username or user.id}_kang_pack_by_{context.bot.username}".lower()
    pack_title = f"{user.first_name}’s Kang Pack"

    os.makedirs("tmp", exist_ok=True)

    input_sticker = None

    try:
        if msg.sticker:  # kang existing sticker
            input_sticker = InputSticker(msg.sticker.file_id, [msg.sticker.emoji or emoji])

        elif msg.photo:  # kang photo
            photo = msg.photo[-1]
            src = f"tmp/{photo.file_unique_id}.jpg"
            dest = f"tmp/{photo.file_unique_id}.webp"
            await download_file(photo, src, context)
            convert_to_webp(src, dest)
            input_sticker = InputSticker(open(dest, "rb"), [emoji])

        elif msg.animation or msg.video:  # kang gif/mp4
            vid = msg.animation or msg.video
            src = f"tmp/{vid.file_unique_id}.mp4"
            dest = f"tmp/{vid.file_unique_id}.webm"
            await download_file(vid, src, context)
            convert_to_webm(src, dest)
            input_sticker = InputSticker(open(dest, "rb"), [emoji])

        if not input_sticker:
            await update.message.reply_text("That file type can’t be kanged yet.")
            return

        try:
            await context.bot.add_sticker_to_set(
                user_id=user.id,
                name=pack_short_name,
                sticker=input_sticker
            )
            await update.message.reply_text(
                f"Added to [{pack_title}](t.me/addstickers/{pack_short_name}) ✅",
                parse_mode="Markdown"
            )
        except:
            await context.bot.create_new_sticker_set(
                user_id=user.id,
                name=pack_short_name,
                title=pack_title,
                stickers=[input_sticker]
            )
            await update.message.reply_text(
                f"Created new pack [{pack_title}](t.me/addstickers/{pack_short_name}) 🎉",
                parse_mode="Markdown"
            )

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# 🌙 Poetic /info command
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌌 *About this bot* 🌌\n\n"
        "I am a humble Kang machine, plucking stickers, photos, and gifs from the ether.\n"
        "With a whisper of `/kang`, I weave them into your own tapestry of laughter.\n\n"
        "✨ Forged in code and chaos by [@loki_senpai](https://t.me/loki_senpai) ✨"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("kang", kang))
    app.add_handler(CommandHandler("info", info))  # <-- new poetic command
    app.run_polling()

if __name__ == "__main__":
    main()
