#!/usr/bin/env python3
import os, logging, tempfile, subprocess, shutil, random, time, asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID    = int(os.environ.get("API_ID", "0"))
API_HASH  = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
TEMP_BASE = "/tmp"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client("bypass_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

PIPELINE = [
    "Color", "Audio", "Metadata", "Chroma",
    "Border", "CRF", "FPS", "Scale"
]

def progress_bar(done, total=8):
    filled = int((done / total) * 10)
    bar = "█" * filled + "░" * (10 - filled)
    pct = int((done / total) * 100)
    return f"[{bar}] {pct}%"


class BypassEngine:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(dir=TEMP_BASE)

    def _ffmpeg(self, inp, out, args, timeout=900):
        cmd = ['ffmpeg', '-y', '-i', inp] + args + [out]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 100:
                return out
        except Exception as e:
            logger.error(f"FFmpeg: {e}")
        return None

    def run_step(self, name, current):
        out = os.path.join(self.temp_dir, f'{name}.mp4')
        h = random.uniform(-30, 30)
        s = random.uniform(0.7, 1.3)
        p = random.uniform(0.92, 1.08)
        b = random.randint(1, 3)
        crf = random.randint(18, 28)

        args_map = {
            "Color":    ['-vf', f'hue=h={h}:s={s}', '-c:v','libx264','-preset','fast','-crf','23','-c:a','aac','-b:a','128k'],
            "Audio":    ['-af', f'asetrate=44100*{p},aresample=44100', '-c:v','libx264','-preset','fast','-crf','23','-c:a','aac'],
            "Metadata": ['-map_metadata','-1','-metadata',f'title=V{random.randint(1000,9999)}','-c','copy'],
            "Chroma":   ['-vf','format=yuv422p','-c:v','libx264','-preset','fast','-crf','23','-c:a','aac'],
            "Border":   ['-vf',f'drawbox=x=0:y=0:w=iw:h={b}:color=black:t=fill,drawbox=x=0:y=ih-{b}:w=iw:h={b}:color=black:t=fill','-c:v','libx264','-preset','fast','-crf','23','-c:a','aac'],
            "CRF":      ['-c:v','libx264','-preset','medium','-crf',str(crf),'-c:a','aac','-b:a','128k'],
            "FPS":      ['-r','24','-c:v','libx264','-preset','fast','-crf','23','-c:a','aac','-b:a','128k'],
            "Scale":    ['-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black','-c:v','libx264','-preset','fast','-crf','23','-c:a','aac','-b:a','128k'],
        }
        return self._ffmpeg(current, out, args_map[name])

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


def make_dl_progress(msg_obj, loop, start_time, file_size):
    last_update = [0]
    async def progress(current, total):
        now = time.time()
        if now - last_update[0] < 2:
            return
        last_update[0] = now
        elapsed = now - start_time
        speed = current / elapsed if elapsed > 0 else 0
        speed_mb = speed / (1024 * 1024)
        pct = int((current / total) * 100) if total else 0
        filled = int(pct / 10)
        bar = "█" * filled + "░" * (10 - filled)
        cur_mb = current / (1024 * 1024)
        tot_mb = total / (1024 * 1024)
        text = (
            f"📥 ডাউনলোড হচ্ছে...\n"
            f"[{bar}] {pct}%\n"
            f"{cur_mb:.1f} MB / {tot_mb:.1f} MB\n"
            f"গতি: {speed_mb:.2f} MB/s"
        )
        asyncio.run_coroutine_threadsafe(msg_obj.edit_text(text), loop)
    return progress


def make_ul_progress(msg_obj, loop, start_time):
    last_update = [0]
    async def progress(current, total):
        now = time.time()
        if now - last_update[0] < 2:
            return
        last_update[0] = now
        elapsed = now - start_time
        speed = current / elapsed if elapsed > 0 else 0
        speed_mb = speed / (1024 * 1024)
        pct = int((current / total) * 100) if total else 0
        filled = int(pct / 10)
        bar = "█" * filled + "░" * (10 - filled)
        cur_mb = current / (1024 * 1024)
        tot_mb = total / (1024 * 1024)
        text = (
            f"📤 আপলোড হচ্ছে...\n"
            f"[{bar}] {pct}%\n"
            f"{cur_mb:.1f} MB / {tot_mb:.1f} MB\n"
            f"গতি: {speed_mb:.2f} MB/s"
        )
        asyncio.run_coroutine_threadsafe(msg_obj.edit_text(text), loop)
    return progress


@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "**Video Bypass Bot v3**\n\n"
        "2GB পর্যন্ত ভিডিও সাপোর্ট\n"
        "Real-time progress দেখাবে\n\n"
        "যেকোনো ভিডিও পাঠান!"
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

    msg = await message.reply_text(f"📥 ডাউনলোড শুরু হচ্ছে... ({size_mb:.1f} MB)")
    input_path = os.path.join(TEMP_BASE, f'in_{media.file_unique_id}.mp4')
    loop = asyncio.get_event_loop()

    try:
        dl_start = time.time()
        await client.download_media(
            message,
            file_name=input_path,
            progress=make_dl_progress(msg, loop, dl_start, media.file_size)
        )
        dl_time = time.time() - dl_start
        await msg.edit_text(f"✅ ডাউনলোড সম্পন্ন ({size_mb:.1f} MB, {dl_time:.1f}s)\n\n🔄 Bypass শুরু হচ্ছে...")

    except Exception as e:
        await msg.edit_text(f"❌ ডাউনলোড ব্যর্থ: {e}")
        return

    engine = BypassEngine()
    try:
        current = input_path
        done_techniques = []

        for i, name in enumerate(PIPELINE):
            bar = progress_bar(i, 8)
            await msg.edit_text(
                f"🔄 Bypass চলছে...\n"
                f"{bar}\n"
                f"ধাপ {i+1}/8: {name} প্রয়োগ হচ্ছে...\n"
                f"সম্পন্ন: {', '.join(done_techniques) if done_techniques else 'কিছু না'}"
            )
            result = engine.run_step(name, current)
            if result:
                done_techniques.append(f"✅{name}")
                current = result
            else:
                done_techniques.append(f"❌{name}")

        if not os.path.exists(current) or current == input_path:
            await msg.edit_text("❌ সব technique ব্যর্থ হয়েছে!")
            return

        out_mb = os.path.getsize(current) / (1024 * 1024)
        await msg.edit_text(
            f"✅ Bypass সম্পন্ন!\n"
            f"{progress_bar(8, 8)}\n"
            f"আউটপুট: {out_mb:.1f} MB\n\n"
            f"📤 আপলোড শুরু হচ্ছে..."
        )

        ul_start = time.time()
        await client.send_video(
            message.chat.id,
            current,
            caption=f"✅ Bypassed | {len(done_techniques)}/8 টেকনিক",
            supports_streaming=True,
            reply_to_message_id=message.id,
            progress=make_ul_progress(msg, loop, ul_start)
        )
        ul_time = time.time() - ul_start
        await msg.edit_text(
            f"✅ সম্পন্ন!\n"
            f"ডাউনলোড: {dl_time:.1f}s\n"
            f"আপলোড: {ul_time:.1f}s\n"
            f"টেকনিক: {', '.join(done_techniques)}"
        )

    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")
        logger.exception("Error")
    finally:
        engine.cleanup()
        if os.path.exists(input_path):
            os.remove(input_path)


app.run()
