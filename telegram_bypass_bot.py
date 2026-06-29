#!/usr/bin/env python3
import os, logging, hashlib, tempfile, subprocess, shutil, random
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID   = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
TEMP_BASE = "/tmp"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client("bypass_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


class BypassEngine:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(dir=TEMP_BASE)
        self.techniques = []

    def _ffmpeg(self, inp, out, args, timeout=900):
        cmd = ['ffmpeg', '-y', '-i', inp] + args + [out]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 100:
                return out
        except Exception as e:
            logger.error(f"FFmpeg error: {e}")
        return None

    def t_color(self, i, o):
        h, s = random.uniform(-30, 30), random.uniform(0.7, 1.3)
        return self._ffmpeg(i, o, ['-vf', f'hue=h={h}:s={s}', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k'])

    def t_audio(self, i, o):
        p = random.uniform(0.92, 1.08)
        return self._ffmpeg(i, o, ['-af', f'asetrate=44100*{p},aresample=44100', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac'])

    def t_meta(self, i, o):
        return self._ffmpeg(i, o, ['-map_metadata', '-1', '-metadata', f'title=V{random.randint(1000,9999)}', '-c', 'copy'])

    def t_chroma(self, i, o):
        return self._ffmpeg(i, o, ['-vf', 'format=yuv422p', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac'])

    def t_border(self, i, o):
        b = random.randint(1, 3)
        return self._ffmpeg(i, o, ['-vf', f'drawbox=x=0:y=0:w=iw:h={b}:color=black:t=fill,drawbox=x=0:y=ih-{b}:w=iw:h={b}:color=black:t=fill', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac'])

    def t_crf(self, i, o):
        return self._ffmpeg(i, o, ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(random.randint(18,28)), '-c:a', 'aac', '-b:a', '128k'])

    def t_fps(self, i, o):
        return self._ffmpeg(i, o, ['-r', '24', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k'])

    def t_scale(self, i, o):
        return self._ffmpeg(i, o, ['-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k'])

    def run(self, video_path):
        self.techniques = []
        current = video_path
        pipeline = [
            ('Color', self.t_color), ('Audio', self.t_audio),
            ('Metadata', self.t_meta), ('Chroma', self.t_chroma),
            ('Border', self.t_border), ('CRF', self.t_crf),
            ('FPS', self.t_fps), ('Scale', self.t_scale),
        ]
        final = None
        for name, func in pipeline:
            out = os.path.join(self.temp_dir, f'{len(self.techniques)}_{name}.mp4')
            result = func(current, out)
            if result:
                self.techniques.append(name)
                current = result
                final = result
        return final, self.techniques

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "**Video Bypass Bot v3 - 2GB Support**\n\n"
        "Pyrogram দিয়ে তৈরি — 2GB পর্যন্ত ভিডিও সাপোর্ট\n\n"
        "যেকোনো ভিডিও পাঠান, bypass করে দেব!\n\n"
        "/status - বট স্ট্যাটাস"
    )

@app.on_message(filters.command("status"))
async def status(client, message: Message):
    ff = os.system('which ffmpeg > /dev/null 2>&1') == 0
    await message.reply_text(
        f"**বট অনলাইন**\n"
        f"FFmpeg: {'OK' if ff else 'NOT FOUND'}\n"
        f"2GB Support: OK (Pyrogram)"
    )

@app.on_message(filters.video | filters.document)
async def handle_video(client, message: Message):
    media = message.video or message.document
    if not media:
        return
    if message.document and not (message.document.mime_type and 'video' in message.document.mime_type):
        return

    size_mb = media.file_size / (1024 * 1024)
    if media.file_size > 2 * 1024 * 1024 * 1024:
        await message.reply_text(f"ফাইল খুব বড়: {size_mb:.1f}MB (সর্বোচ্চ 2GB)")
        return

    msg = await message.reply_text(f"ডাউনলোড হচ্ছে... ({size_mb:.1f}MB)")
    input_path = os.path.join(TEMP_BASE, f'input_{media.file_unique_id}.mp4')

    try:
        await client.download_media(message, file_name=input_path)
        await msg.edit_text("8টি bypass টেকনিক প্রয়োগ হচ্ছে...")

        engine = BypassEngine()
        try:
            output_path, techniques = engine.run(input_path)
            if not output_path:
                await msg.edit_text("Bypass ব্যর্থ!")
                return

            out_mb = os.path.getsize(output_path) / (1024*1024)
            await msg.edit_text(f"আপলোড হচ্ছে... ({out_mb:.1f}MB)")

            await client.send_video(
                message.chat.id,
                output_path,
                caption=f"Bypassed | {', '.join(techniques)}",
                supports_streaming=True,
                reply_to_message_id=message.id
            )
            await msg.delete()

        finally:
            engine.cleanup()
            if os.path.exists(input_path):
                os.remove(input_path)

    except Exception as e:
        await msg.edit_text(f"Error: {str(e)}")
        logger.exception("Error")


app.run()
