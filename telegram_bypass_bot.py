#!/usr/bin/env python3
"""
Telegram Video Bypass Bot v3 - 2GB Support
Authorized Pentesting Tool
"""

import os
import sys
import json
import logging
import hashlib
import tempfile
import subprocess
import shutil
import random
import requests

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")

# আপনার API এবং Hash ID - Environment Variable থেকে সেট করুন
API_TOKEN = os.environ.get("API_TOKEN", "YOUR_API_TOKEN")
HASH_ID = os.environ.get("HASH_ID", "YOUR_HASH_ID")
UPLOAD_URL = "https://api.yourservice.com/upload"  # আপনার API endpoint দিন
DOWNLOAD_URL = "https://api.yourservice.com/download"  # আপনার Download endpoint দিন

AUTHORIZED_USERS = []
TEMP_BASE = "/tmp"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============================================================
# LARGE FILE HANDLER (API Based - 2GB Support)
# ============================================================

class LargeFileHandler:
    """API ব্যবহার করে 2GB পর্যন্ত ফাইল আপলোড/ডাউনলোড"""
    
    @staticmethod
    def upload_via_api(file_path):
        """ফাইল API-তে আপলোড করে file_id রিটার্ন করে"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'video/mp4')}
                headers = {
                    'Authorization': f'Bearer {API_TOKEN}',
                    'X-Hash-ID': HASH_ID
                }
                resp = requests.post(UPLOAD_URL, headers=headers, files=files, timeout=600)
                
                if resp.status_code == 200:
                    data = resp.json()
                    file_id = data.get('file_id')
                    logger.info(f"API Upload success: {file_id}")
                    return file_id
                else:
                    logger.error(f"API Upload fail: {resp.status_code} - {resp.text[:200]}")
                    return None
        except Exception as e:
            logger.error(f"API Upload error: {e}")
            return None
    
    @staticmethod
    def download_via_api(file_id, output_path):
        """API থেকে file_id ব্যবহার করে ফাইল ডাউনলোড করে"""
        try:
            headers = {
                'Authorization': f'Bearer {API_TOKEN}',
                'X-Hash-ID': HASH_ID
            }
            params = {'file_id': file_id}
            resp = requests.get(DOWNLOAD_URL, headers=headers, params=params, stream=True, timeout=600)
            
            if resp.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"API Download success: {output_path}")
                return output_path
            else:
                logger.error(f"API Download fail: {resp.status_code} - {resp.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"API Download error: {e}")
            return None


# ============================================================
# BYPASS ENGINE
# ============================================================

class BypassEngine:
    """Video fingerprint bypass engine"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(dir=TEMP_BASE)
        self.techniques = []
    
    def _ffmpeg(self, inp, out, args, timeout=900):
        """FFmpeg wrapper"""
        cmd = ['ffmpeg', '-y', '-i', inp] + args + [out]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 100:
                return out
            logger.error(f"FFmpeg fail: {r.stderr[:200]}")
            return None
        except Exception as e:
            logger.error(f"FFmpeg error: {e}")
            return None
    
    # টেকনিক ১
    def t_color(self, inp, out):
        h = random.uniform(-30, 30)
        s = random.uniform(0.7, 1.3)
        return self._ffmpeg(inp, out, ['-vf', f'hue=h={h}:s={s}', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k'])
    
    # টেকনিক ২
    def t_audio(self, inp, out):
        p = random.uniform(0.92, 1.08)
        return self._ffmpeg(inp, out, ['-af', f'asetrate=44100*{p},aresample=44100', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23'])
    
    # টেকনিক ৩
    def t_meta(self, inp, out):
        return self._ffmpeg(inp, out, ['-map_metadata', '-1', '-metadata', f'title=V{random.randint(1000,9999)}', '-metadata', f'artist=R{random.randint(100,999)}', '-c', 'copy'])
    
    # টেকনিক ৪
    def t_chroma(self, inp, out):
        return self._ffmpeg(inp, out, ['-vf', 'format=yuv422p', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac'])
    
    # টেকনিক ৫
    def t_border(self, inp, out):
        b = random.randint(1, 3)
        return self._ffmpeg(inp, out, ['-vf', f'drawbox=x=0:y=0:w=iw:h={b}:color=black:t=fill,drawbox=x=0:y=ih-{b}:w=iw:h={b}:color=black:t=fill', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac'])
    
    # টেকনিক ৬
    def t_crf(self, inp, out):
        crf = random.randint(18, 28)
        return self._ffmpeg(inp, out, ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf), '-c:a', 'aac', '-b:a', '128k'])
    
    # টেকনিক ৭
    def t_fps(self, inp, out):
        return self._ffmpeg(inp, out, ['-r', '24', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k'])
    
    # টেকনিক ৮
    def t_scale(self, inp, out):
        return self._ffmpeg(inp, out, ['-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k'])
    
    def run(self, video_path):
        """Full bypass pipeline"""
        self.techniques = []
        current = video_path
        
        # Original hash
        sha = hashlib.sha256()
        with open(video_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha.update(chunk)
        orig_hash = sha.hexdigest()[:16]
        logger.info(f"Original hash: {orig_hash}")
        
        pipeline = [
            ('Color', self.t_color),
            ('Audio', self.t_audio),
            ('Metadata', self.t_meta),
            ('Chroma', self.t_chroma),
            ('Border', self.t_border),
            ('CRF', self.t_crf),
            ('FPS', self.t_fps),
            ('Scale', self.t_scale),
        ]
        
        final = None
        for name, func in pipeline:
            out = os.path.join(self.temp_dir, f'{len(self.techniques)}_{name.lower()}.mp4')
            try:
                result = func(current, out)
                if result:
                    self.techniques.append(name)
                    current = result
                    final = result
                    logger.info(f"✓ {name}")
                else:
                    logger.warning(f"✗ {name}")
            except Exception as e:
                logger.error(f"{name} crash: {e}")
        
        if final:
            sha = hashlib.sha256()
            with open(final, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    sha.update(chunk)
            logger.info(f"Final hash: {sha.hexdigest()[:16]}")
            logger.info(f"Techniques: {', '.join(self.techniques)}")
        
        return final, self.techniques
    
    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


# ============================================================
# BOT HANDLERS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👋 হ্যালো {user.first_name}!\n\n"
        "🤖 **Video Bypass Bot v3 - 2GB Support**\n"
        "বড় ফাইল সাপোর্ট + সমস্ত bypass টেকনিক\n\n"
        "**কিভাবে কাজ করে:**\n"
        "➡️ যেকোনো ভিডিও ফরওয়ার্ড/আপলোড করুন\n"
        "➡️ API এর মাধ্যমে 2GB পর্যন্ত ফাইল সাপোর্ট\n"
        "➡️ ৮টি bypass টেকনিক প্রয়োগ\n"
        "➡️ bypassed ভিডিও ফেরত\n\n"
        "**কমান্ড:**\n"
        "/start - শুরু\n"
        "/help - সাহায্য\n"
        "/status - বট স্ট্যাটাস"
    )
    await update.message.reply_text(text, parse_mode='Markdown')


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 **বিস্তারিত**\n\n"
        "**টেকনিক লিস্ট:**\n"
        "1. Color Shift - Hue/Saturation পরিবর্তন\n"
        "2. Audio Pitch - অডিও পিচ চেঞ্জ\n"
        "3. Metadata Clear - সব মেটাডাটা রিসেট\n"
        "4. Chroma Change - yuv422p ফরম্যাট\n"
        "5. Border Add - ইনভিজিবল বর্ডার\n"
        "6. CRF Change - কম্প্রেশন লেভেল\n"
        "7. FPS Change - 24fps\n"
        "8. Scale - 720p রেজুলেশন\n\n"
        "**ফাইল সাইজ:** 2GB পর্যন্ত (API based)"
    )
    await update.message.reply_text(text, parse_mode='Markdown')


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ভিডিও হ্যান্ডেল - 2GB পর্যন্ত সাপোর্ট"""
    user = update.effective_user
    
    # ভিডিও অবজেক্ট বের করা
    video = None
    if update.message.video:
        video = update.message.video
    elif update.message.document and update.message.document.mime_type and 'video' in update.message.document.mime_type:
        video = update.message.document
    else:
        await update.message.reply_text("❌ শুধু MP4 ভিডিও ফাইল গ্রহণযোগ্য।")
        return
    
    # File size check - 2GB পর্যন্ত অনুমতি
    file_size_mb = video.file_size / (1024 * 1024)
    if video.file_size > 2 * 1024 * 1024 * 1024:  # 2GB
        await update.message.reply_text(
            f"❌ ফাইল খুব বড়: {file_size_mb:.1f}MB\n"
            f"সর্বোচ্চ 2GB পর্যন্ত সাপোর্ট করে।"
        )
        return
    
    msg = await update.message.reply_text(
        f"⏳ ভিডিও প্রসেস করা হচ্ছে...\n"
        f"ফাইল সাইজ: {file_size_mb:.1f}MB\n"
        f"এতে কিছু সময় লাগতে পারে (ফাইল সাইজ অনুযায়ী)।"
    )
    
    try:
        # বড় ফাইলের জন্য API ব্যবহার (যদি 50MB এর বেশি হয়)
        input_path = os.path.join(TEMP_BASE, f'input_{video.file_unique_id}.mp4')
        
        if video.file_size > 48 * 1024 * 1024:
            # বড় ফাইল -> API upload তারপর ডাউনলোড
            await msg.edit_text(f"📤 বড় ফাইল ({file_size_mb:.1f}MB) -> API তে আপলোড হচ্ছে...")
            
            file = await context.bot.get_file(video.file_id)
            temp_path = os.path.join(TEMP_BASE, f'temp_{video.file_unique_id}.mp4')
            await file.download_to_drive(temp_path)
            
            # API upload
            file_id = LargeFileHandler.upload_via_api(temp_path)
            if not file_id:
                await msg.edit_text("❌ API আপলোড ব্যর্থ। API টোকেন/URL চেক করুন।")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return
            
            # API download
            await msg.edit_text(f"📥 API থেকে ডাউনলোড হচ্ছে...")
            downloaded = LargeFileHandler.download_via_api(file_id, input_path)
            if not downloaded:
                await msg.edit_text("❌ API ডাউনলোড ব্যর্থ।")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
        else:
            # ছোট ফাইল -> সরাসরি ডাউনলোড
            file = await context.bot.get_file(video.file_id)
            await file.download_to_drive(input_path)
        
        await msg.edit_text(
            f"✅ ডাউনলোড সম্পন্ন\n"
            f"🔄 ৮টি bypass টেকনিক প্রয়োগ করা হচ্ছে..."
        )
        
    except Exception as e:
        await msg.edit_text(f"❌ ডাউনলোড ব্যর্থ: {str(e)}")
        logger.exception("Download error")
        return
    
    # Bypass engine
    engine = BypassEngine()
    try:
        output_path, techniques = engine.run(input_path)
        
        if not output_path:
            await msg.edit_text("❌ Bypass ব্যর্থ।")
            return
        
        out_size = os.path.getsize(output_path)
        out_size_mb = out_size / (1024*1024)
        
        await msg.edit_text(
            f"✅ **Bypass সম্পন্ন!**\n\n"
            f"**ব্যবহৃত টেকনিক:** {', '.join(techniques)}\n"
            f"**আউটপুট সাইজ:** {out_size_mb:.1f}MB\n\n"
            f"📤 আপলোড হচ্ছে..."
        )
        
        # আউটপুট ফাইল সাইজ চেক
        if out_size > 48 * 1024 * 1024:
            # বড় আউটপুট -> API upload তারপর লিংক দিয়ে দেওয়া
            await msg.edit_text("📤 বড় আউটপুট -> API তে আপলোড হচ্ছে...")
            file_id = LargeFileHandler.upload_via_api(output_path)
            if file_id:
                download_link = f"{DOWNLOAD_URL}?file_id={file_id}&token={API_TOKEN[:8]}..."
                await update.message.reply_text(
                    f"✅ **Bypass সম্পন্ন!**\n\n"
                    f"**ব্যবহৃত টেকনিক:** {', '.join(techniques)}\n"
                    f"**ফাইল সাইজ:** {out_size_mb:.1f}MB\n\n"
                    f"**ডাউনলোড লিংক:**\n{download_link}\n\n"
                    f"এই ভিডিও ডাউনলোড করে Facebook-এ আপলোড করুন।"
                )
            else:
                await update.message.reply_text(
                    f"⚠️ আউটপুট ফাইল বড় ({out_size_mb:.1f}MB), "
                    f"Telegram এর 50MB লিমিটের মধ্যে নয়।\n"
                    f"API upload ও ব্যর্থ। দয়া করে ছোট ভিডিও ব্যবহার করুন।"
                )
        else:
            # ছোট আউটপুট -> সরাসরি Telegram-এ পাঠানো
            with open(output_path, 'rb') as f:
                await update.message.reply_video(
                    video=f,
                    caption=f"✅ Bypassed | {', '.join(techniques)}",
                    supports_streaming=True
                )
        
        await msg.edit_text(
            f"✅ সম্পন্ন! {', '.join(techniques)}\n"
            f"এখন এই ভিডিও Facebook-এ আপলোড করুন।"
        )
        
    except Exception as e:
        await msg.edit_text(f"❌ এরর: {str(e)}")
        logger.exception("Processing failed")
    finally:
        engine.cleanup()
        if os.path.exists(input_path):
            os.remove(input_path)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ff = os.system('which ffmpeg > /dev/null 2>&1') == 0
    api_ok = bool(API_TOKEN and API_TOKEN != "YOUR_API_TOKEN" and HASH_ID and HASH_ID != "YOUR_HASH_ID")
    text = (
        f"✅ **বট অনলাইন**\n"
        f"FFmpeg: {'✔️' if ff else '❌'}\n"
        f"API: {'✔️' if api_ok else '❌'} (2GB support)\n"
        f"API Token: {'✅ সেট করা আছে' if api_ok else '❌ সেট করুন'}\n"
        f"Hash ID: {'✅ সেট করা আছে' if api_ok else '❌ সেট করুন'}"
    )
    await update.message.reply_text(text, parse_mode='Markdown')


# ============================================================
# MAIN
# ============================================================

def main():
    logger.info("Starting Video Bypass Bot v3 - 2GB Support")
    
    if API_TOKEN == "YOUR_API_TOKEN":
        logger.warning("API_TOKEN সেট করা হয়নি! Environment Variable চেক করুন।")
    if HASH_ID == "YOUR_HASH_ID":
        logger.warning("HASH_ID সেট করা হয়নি! Environment Variable চেক করুন।")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.Document.VIDEO, handle_video))
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
