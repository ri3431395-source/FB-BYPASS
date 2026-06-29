#!/usr/bin/env python3
"""
Telegram Video Fingerprint Bypass Bot - Railway Deploy Ready
Authorized Pentesting Tool
"""

import os
import sys
import json
import time
import random
import logging
import asyncio
import hashlib
import tempfile
import subprocess
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from mutagen.mp4 import MP4, MP4Cover

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================================
# CONFIGURATION
# ============================================================

# Railway Environment Variable থেকে টোকেন পড়ুন
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN environment variable সেট করা হয়নি!")
    print("   Railway Dashboard > Variables > BOT_TOKEN = আপনার_টোকেন")
    sys.exit(1)

AUTHORIZED_USERS_STR = os.environ.get("AUTHORIZED_USERS", "")
AUTHORIZED_USERS = [int(uid.strip()) for uid in AUTHORIZED_USERS_STR.split(",") if uid.strip()] if AUTHORIZED_USERS_STR else []

# Railway-তে temporary directory
TEMP_BASE = os.environ.get("TEMP_DIR", "/tmp")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============================================================
# VIDEO BYPASS ENGINE
# ============================================================

class VideoBypassEngine:
    """Complete video fingerprint bypass engine"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(dir=TEMP_BASE)
        self.techniques_used = []
    
    def _run_ffmpeg(self, input_path, output_path, cmd_args, timeout=300):
        cmd = ['ffmpeg', '-y', '-i', input_path] + cmd_args + [output_path]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, check=False
            )
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return output_path
            else:
                logger.error(f"FFmpeg error (code {result.returncode}): {result.stderr[:300]}")
                return None
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout")
            return None
        except Exception as e:
            logger.error(f"FFmpeg exception: {str(e)}")
            return None
    
    def _compute_hash(self, filepath):
        sha = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha.update(chunk)
        return sha.hexdigest()
    
    # ---------- T1: Frame Rate ----------
    def technique_fps(self, input_path, output_path):
        cmd = ['-r', '24', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k']
        return self._run_ffmpeg(input_path, output_path, cmd)
    
    # ---------- T2: Resolution ----------
    def technique_resolution(self, input_path, output_path):
        cmd = [
            '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k'
        ]
        return self._run_ffmpeg(input_path, output_path, cmd)
    
    # ---------- T3: Color Shift ----------
    def technique_color(self, input_path, output_path):
        hue = random.uniform(-25, 25)
        sat = random.uniform(0.8, 1.2)
        cmd = ['-vf', f'hue=h={hue}:s={sat}', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k']
        return self._run_ffmpeg(input_path, output_path, cmd)
    
    # ---------- T4: Audio Pitch ----------
    def technique_audio(self, input_path, output_path):
        pitch = random.uniform(0.93, 1.07)
        cmd = ['-af', f'asetrate=44100*{pitch},aresample=44100', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23']
        return self._run_ffmpeg(input_path, output_path, cmd)
    
    # ---------- T5: Metadata Wipe ----------
    def technique_metadata(self, input_path, output_path):
        cmd = [
            '-map_metadata', '-1',
            '-metadata', f'title="V_{random.randint(1000,9999)}"',
            '-metadata', f'artist="R_{random.randint(100,999)}"',
            '-metadata', f'date="{random.randint(2020,2025)}"',
            '-c', 'copy'
        ]
        return self._run_ffmpeg(input_path, output_path, cmd)
    
    # ---------- T6: Chroma Change ----------
    def technique_chroma(self, input_path, output_path):
        cmd = ['-vf', 'format=yuv422p', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac']
        return self._run_ffmpeg(input_path, output_path, cmd)
    
    # ---------- T7: Border ----------
    def technique_border(self, input_path, output_path):
        bs = random.randint(1, 3)
        cmd = [
            '-vf', f'drawbox=x=0:y=0:w=iw:h={bs}:color=black:t=fill,drawbox=x=0:y=ih-{bs}:w=iw:h={bs}:color=black:t=fill',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac'
        ]
        return self._run_ffmpeg(input_path, output_path, cmd)
    
    # ---------- T8: Compression ----------
    def technique_compression(self, input_path, output_path):
        crf = random.randint(19, 26)
        cmd = ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf), '-profile:v', 'high', '-c:a', 'aac', '-b:a', '128k']
        return self._run_ffmpeg(input_path, output_path, cmd)
    
    # ---------- Full Pipeline ----------
    def full_bypass(self, input_path):
        self.techniques_used = []
        current = input_path
        
        logger.info(f"Pipeline start | Original hash: {self._compute_hash(input_path)[:16]}")
        
        techniques = [
            ('Color', self.technique_color),
            ('Audio', self.technique_audio),
            ('Metadata', self.technique_metadata),
            ('Chroma', self.technique_chroma),
            ('Border', self.technique_border),
            ('Compression', self.technique_compression),
            ('FPS', self.technique_fps),
            ('Resolution', self.technique_resolution),
        ]
        
        final = None
        for name, func in techniques:
            out = os.path.join(self.temp_dir, f's_{len(self.techniques_used)}_{name.lower()}.mp4')
            result = func(current, out)
            if result:
                self.techniques_used.append(name)
                current = result
                final = result
                logger.info(f"  ✓ {name}")
            else:
                logger.warning(f"  ✗ {name}")
        
        if final:
            logger.info(f"Final hash: {self._compute_hash(final)[:16]}")
            logger.info(f"Used: {', '.join(self.techniques_used)}")
        
        return final, self.techniques_used
    
    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


# ============================================================
# BOT HANDLERS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👋 হ্যালো {user.first_name}!\n\n"
        "🤖 **Video Fingerprint Bypass Bot**\n"
        "অনুমোদিত পেন্টেস্টিং টুল | Railway Deployed\n\n"
        "**📹 ব্যবহার:** MP4 ভিডিও পাঠান → বট প্রসেস করবে → bypassed ভিডিও ফেরত দিবে\n\n"
        "**⚙️ টেকনিক:** Color Shift, Audio Pitch, Metadata Wipe, Chroma, Border, Compression, FPS, Resolution\n\n"
        "**🔬 Authorized Pentesting Only**"
    )
    await update.message.reply_text(text, parse_mode='Markdown')


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Auth check
    if AUTHORIZED_USERS and user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("⛔ অননুমোদিত ব্যবহারকারী।")
        return
    
    # Get video
    video = update.message.video or update.message.document
    if not video:
        await update.message.reply_text("❌ MP4 ভিডিও পাঠান।")
        return
    
    msg = await update.message.reply_text("⏳ ডাউনলোড হচ্ছে...")
    
    try:
        file = await context.bot.get_file(video.file_id)
        input_path = os.path.join(TEMP_BASE, f'in_{video.file_unique_id}.mp4')
        await file.download_to_drive(input_path)
        await msg.edit_text("🔄 প্রসেসিং শুরু... (৮টি টেকনিক প্রয়োগ করা হবে, ১-৫ মিনিট)")
    except Exception as e:
        await msg.edit_text(f"❌ ডাউনলোড ব্যর্থ: {str(e)}")
        return
    
    engine = VideoBypassEngine()
    try:
        output_path, techniques = engine.full_bypass(input_path)
        
        if not output_path or not os.path.exists(output_path):
            await msg.edit_text("❌ প্রসেসিং ব্যর্থ। ভিডিও চেক করুন।")
            return
        
        fsize = os.path.getsize(output_path)
        status = (
            f"✅ **প্রসেস সম্পন্ন!**\n\n"
            f"**ব্যবহৃত:** {', '.join(techniques)}\n"
            f"**সাইজ:** {fsize/(1024*1024):.1f}MB\n\n"
            f"📤 আপলোড হচ্ছে..."
        )
        await msg.edit_text(status, parse_mode='Markdown')
        
        if fsize > 48 * 1024 * 1024:
            await update.message.reply_text(
                "⚠️ ফাইল ৪৮MB+ (Telegram limit: 50MB)। কম্প্রেস করে আবার পাঠান।"
            )
        else:
            with open(output_path, 'rb') as f:
                await update.message.reply_video(
                    video=f,
                    caption=f"✅ Bypassed | {', '.join(techniques)}",
                    supports_streaming=True
                )
            
            await msg.edit_text(
                f"✅ সম্পন্ন! {', '.join(techniques)}\n"
                f"এখন এই ভিডিও অন্য প্ল্যাটফর্মে টেস্ট করুন।",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        await msg.edit_text(f"❌ এরর: {str(e)}")
        logger.exception("Process error")
    finally:
        engine.cleanup()
        if os.path.exists(input_path):
            os.remove(input_path)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 **Help**\n\n"
        "/start - শুরু\n"
        "/help - সাহায্য\n"
        "/status - বট স্ট্যাটাস\n\n"
        "ভিডিও পাঠালেই প্রসেস শুরু হবে।"
    )
    await update.message.reply_text(text, parse_mode='Markdown')


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ffmpeg_ok = os.system('which ffmpeg > /dev/null 2>&1') == 0
    text = (
        f"✅ **বট অনলাইন**\n"
        f"FFmpeg: {'✔️' if ffmpeg_ok else '❌'}\n"
        f"Deploy: Railway\n"
        f"Python: {sys.version[:5]}"
    )
    await update.message.reply_text(text, parse_mode='Markdown')


# ============================================================
# MAIN
# ============================================================

def main():
    print("🤖 Video Bypass Bot starting on Railway...")
    print(f"   Authorized users: {'All' if not AUTHORIZED_USERS else AUTHORIZED_USERS}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.Document.VIDEO, handle_video))
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
