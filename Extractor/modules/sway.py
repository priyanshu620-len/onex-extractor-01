import io
import re
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pyrogram import filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from Extractor import app

THREAD_POOL = ThreadPoolExecutor(max_workers=50)

API_BASE = "https://gdgoenkaratia.com/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.selectionway.com/",
    "Origin": "https://www.selectionway.com",
}

BATCH_CACHE = {}
PAGE_SIZE = 8


def clean_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name.strip('_. ') or "SelectionWay_Batch"


def build_batch_keyboard(chat_id: int, page: int = 0) -> InlineKeyboardMarkup:
    batches = BATCH_CACHE.get(chat_id, [])
    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_batches = batches[start_idx:end_idx]

    buttons = []
    for idx, b in enumerate(page_batches, start=start_idx):
        title = b.get("title", "Unknown")
        btn_title = (title[:30] + "..") if len(title) > 32 else title
        buttons.append([InlineKeyboardButton(f"📚 {btn_title}", callback_data=f"sw_pick_{idx}")])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"sw_page_{page - 1}"))
    if end_idx < len(batches):
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"sw_page_{page + 1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="sw_close")])
    return InlineKeyboardMarkup(buttons)


def _sync_fetch_batches():
    url = f"{API_BASE}/courses/active?userId="
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("state") == 200:
                return data.get("data", [])
    except Exception:
        pass
    return []


def _sync_fetch_topics(course_id):
    url = f"{API_BASE}/topic-and-section?courseId={course_id}&userId="
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("state") == 200:
                return data.get("data", {}).get("topics", [])
    except Exception:
        pass
    return []


def _sync_fetch_classes(topic_id, course_id):
    url = f"{API_BASE}/topics/{topic_id}/classes?courseId={course_id}&userId="
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("state") == 200:
                return data.get("data", {}).get("classes", [])
    except Exception:
        pass
    return []


# Callable function from start.py or direct command
async def cmd_selectionway(client, message: Message):
    status_msg = await message.reply_text("⚡ **Fetching SelectionWay batches...**")
    
    loop = asyncio.get_running_loop()
    batches = await loop.run_in_executor(THREAD_POOL, _sync_fetch_batches)

    if not batches:
        await status_msg.edit_text("❌ **Failed to fetch batches or no active batches found.**")
        return

    chat_id = message.chat.id
    BATCH_CACHE[chat_id] = batches
    kb = build_batch_keyboard(chat_id, page=0)
    
    await status_msg.edit_text(
        f"🎯 **SelectionWay Batches Found:** `{len(batches)}`\n\nSelect a batch below to extract:",
        reply_markup=kb
    )


@app.on_message(filters.command(["sway", "selectionway"]) & filters.private)
async def sway_msg_handler(client, message: Message):
    await cmd_selectionway(client, message)


@app.on_callback_query(filters.regex(r"^sw_page_(\d+)"))
async def cb_pagination(client, callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    kb = build_batch_keyboard(callback.message.chat.id, page=page)
    await callback.edit_message_reply_markup(reply_markup=kb)
    await callback.answer()


@app.on_callback_query(filters.regex(r"^sw_close$"))
async def cb_close(client, callback: CallbackQuery):
    BATCH_CACHE.pop(callback.message.chat.id, None)
    await callback.message.delete()
    await callback.answer("Closed")


@app.on_callback_query(filters.regex(r"^sw_pick_(\d+)"))
async def cb_extract(client, callback: CallbackQuery):
    idx = int(callback.data.split("_")[2])
    user_batches = BATCH_CACHE.get(callback.message.chat.id, [])
    
    if not user_batches or idx >= len(user_batches):
        await callback.answer("Session expired. Send /sway again.", show_alert=True)
        return

    batch = user_batches[idx]
    course_id = batch.get("id")
    batch_title = batch.get("title", "Batch")
    faculty = batch.get("facultyDetails", {}).get("name", "N/A")

    await callback.answer("Starting extraction...")
    status_msg = await callback.edit_message_text(
        f"⏳ **Extracting:** `{batch_title}`\n\n_Fetching topics & class links..._"
    )

    loop = asyncio.get_running_loop()
    topics = await loop.run_in_executor(THREAD_POOL, _sync_fetch_topics, course_id)

    if not topics:
        await status_msg.edit_text("❌ **No topics found for this course.**")
        return

    output = io.StringIO()
    total_videos = 0
    total_pdfs = 0

    for t_idx, topic in enumerate(topics, 1):
        topic_id = topic.get("topicId")
        topic_name = topic.get("topicName", f"Topic {t_idx}")
        
        if t_idx % 2 == 0 or t_idx == len(topics):
            try:
                await status_msg.edit_text(
                    f"⏳ **Extracting:** `{batch_title}`\n"
                    f"📁 **Topic** `{t_idx}/{len(topics)}`: _{topic_name}_\n"
                    f"🎥 Videos: `{total_videos}` | 📑 PDFs: `{total_pdfs}`"
                )
            except Exception:
                pass

        classes = await loop.run_in_executor(THREAD_POOL, _sync_fetch_classes, topic_id, course_id)
        if not classes:
            continue

        for cls in classes:
            title = cls.get("title", "Untitled").strip()
            
           mp4s = cls.get("mp4Recordings", [])
            selected_video_url = ""

            if mp4s:
                # 1. Look for 720p specifically
                for mp4 in mp4s:
                    q = str(mp4.get("quality", "")).lower()
                    if "720" in q:
                        selected_video_url = mp4.get("url", "").strip()
                        break
                
                # 2. If 720p isn't found, pick the highest/last available MP4
                if not selected_video_url and len(mp4s) > 0:
                    selected_video_url = mp4s[-1].get("url", "").strip()
            
            # 3. Fallback to class_link (HLS) if no mp4Recordings exist
            if not selected_video_url:
                selected_video_url = cls.get("class_link", "").strip()

            # Write only ONE entry per lecture
            if selected_video_url:
                output.write(f"{title}:{selected_video_url}\n")
                total_videos += 1

            for pdf in cls.get("classPdf", []):
                pdf_url = pdf.get("url", "").strip()
                pdf_name = pdf.get("name", "PDF").strip()
                if pdf_url:
                    output.write(f"{title} - {pdf_name}:{pdf_url}\n")
                    total_pdfs += 1

        await asyncio.sleep(0.05)

    total_links = total_videos + total_pdfs
    if total_links == 0:
        await status_msg.edit_text("⚠️ **No downloadable links found in this batch.**")
        return

    file_bytes = io.BytesIO(output.getvalue().encode("utf-8"))
    safe_name = f"{clean_filename(batch_title)}.txt"
    file_bytes.name = safe_name

    caption = (
        f"✅ **Extraction Complete!**\n\n"
        f"📚 **Batch:** `{batch_title}`\n"
        f"👨‍🏫 **Faculty:** `{faculty}`\n"
        f"🎥 **Videos:** `{total_videos}`\n"
        f"📑 **PDFs:** `{total_pdfs}`\n"
        f"🔗 **Total Links:** `{total_links}`"
    )

    await client.send_document(
        chat_id=callback.message.chat.id,
        document=file_bytes,
        file_name=safe_name,
        caption=caption
    )
    
    await status_msg.delete()
