import asyncio
import io
import re
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import aiohttp

# --- Config & Headers ---
API_BASE = "https://gdgoenkaratia.com/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.selectionway.com/",
    "Origin": "https://www.selectionway.com",
}

# Temporary in-memory cache for batch lists: {user_id: [batch_data]}
BATCH_CACHE = {}
PAGE_SIZE = 8


# --- Helper Functions ---
def clean_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name.strip('_. ') or "SelectionWay_Batch"


def build_batch_keyboard(user_id: int, page: int = 0) -> InlineKeyboardMarkup:
    batches = BATCH_CACHE.get(user_id, [])
    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_batches = batches[start_idx:end_idx]

    buttons = []
    for idx, b in enumerate(page_batches, start=start_idx):
        title = b.get("title", "Unknown")
        # Keep title compact for inline buttons
        btn_title = (title[:32] + "..") if len(title) > 34 else title
        buttons.append([InlineKeyboardButton(f"📚 {btn_title}", callback_data=f"sw_pick_{idx}")])

    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"sw_page_{page - 1}"))
    if end_idx < len(batches):
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"sw_page_{page + 1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="sw_close")])
    return InlineKeyboardMarkup(buttons)


# --- API Fetching Core ---
async def fetch_batches(session: aiohttp.ClientSession, user_id: str = ""):
    url = f"{API_BASE}/courses/active?userId={user_id}"
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=25)) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("state") == 200:
                    return data.get("data", [])
    except Exception:
        pass
    return []


async def fetch_topics(session: aiohttp.ClientSession, course_id: str, user_id: str = ""):
    url = f"{API_BASE}/topic-and-section?courseId={course_id}&userId={user_id}"
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=25)) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("state") == 200:
                    return data.get("data", {}).get("topics", [])
    except Exception:
        pass
    return []


async def fetch_classes(session: aiohttp.ClientSession, topic_id: str, course_id: str, user_id: str = ""):
    url = f"{API_BASE}/topics/{topic_id}/classes?courseId={course_id}&userId={user_id}"
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("state") == 200:
                    return data.get("data", {}).get("classes", [])
    except Exception:
        pass
    return []


# --- Telegram Command & Callback Handlers ---

@Client.on_message(filters.command(["selectionway", "sw"]) & filters.private)
async def cmd_selectionway(client: Client, message: Message):
    status_msg = await message.reply_text("⚡ *Fetching available batches...*", parse_mode="markdown")
    
    async with aiohttp.ClientSession() as session:
        batches = await fetch_batches(session)

    if not batches:
        await status_msg.edit_text("❌ *Failed to fetch batches or no active batches found.*")
        return

    BATCH_CACHE[message.from_user.id] = batches
    kb = build_batch_keyboard(message.from_user.id, page=0)
    
    await status_msg.edit_text(
        f"🎯 *SelectionWay Batches Found:* `{len(batches)}`\n\nSelect a batch below to extract content:",
        reply_markup=kb,
        parse_mode="markdown"
    )


@Client.on_callback_query(filters.regex(r"^sw_page_(\d+)"))
async def cb_pagination(client: Client, callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    kb = build_batch_keyboard(callback.from_user.id, page=page)
    await callback.edit_message_reply_markup(reply_markup=kb)
    await callback.answer()


@Client.on_callback_query(filters.regex(r"^sw_close$"))
async def cb_close(client: Client, callback: CallbackQuery):
    BATCH_CACHE.pop(callback.from_user.id, None)
    await callback.message.delete()
    await callback.answer("Closed")


@Client.on_callback_query(filters.regex(r"^sw_pick_(\d+)"))
async def cb_extract(client: Client, callback: CallbackQuery):
    idx = int(callback.data.split("_")[2])
    user_batches = BATCH_CACHE.get(callback.from_user.id, [])
    
    if not user_batches or idx >= len(user_batches):
        await callback.answer("Session expired. Please send /selectionway again.", show_alert=True)
        return

    batch = user_batches[idx]
    course_id = batch.get("id")
    batch_title = batch.get("title", "Batch")
    faculty = batch.get("facultyDetails", {}).get("name", "N/A")

    await callback.answer("Starting extraction...")
    status_msg = await callback.edit_message_text(
        f"⏳ *Extracting Batch:*\n`{batch_title}`\n\n_Fetching topics & class links..._",
        parse_mode="markdown"
    )

    output = io.StringIO()
    total_videos = 0
    total_pdfs = 0

    async with aiohttp.ClientSession() as session:
        topics = await fetch_topics(session, course_id)

        if not topics:
            await status_msg.edit_text("❌ *No topics found for this course.*")
            return

        for t_idx, topic in enumerate(topics, 1):
            topic_id = topic.get("topicId")
            topic_name = topic.get("topicName", f"Topic {t_idx}")
            
            # Progress update every few topics
            if t_idx % 3 == 0 or t_idx == len(topics):
                try:
                    await status_msg.edit_text(
                        f"⏳ *Extracting:* `{batch_title}`\n"
                        f"📁 Topic `{t_idx}/{len(topics)}`: _{topic_name}_\n"
                        f"🎥 Videos: `{total_videos}` | 📑 PDFs: `{total_pdfs}`",
                        parse_mode="markdown"
                    )
                except Exception:
                    pass

            classes = await fetch_classes(session, topic_id, course_id)
            if not classes:
                continue

            for cls in classes:
                title = cls.get("title", "Untitled").strip()
                
                # Check MP4 Recordings
                mp4s = cls.get("mp4Recordings", [])
                if mp4s:
                    for mp4 in mp4s:
                        quality = mp4.get("quality", "default")
                        url = mp4.get("url", "").strip()
                        if url:
                            output.write(f"{title} ({quality}):{url}\n")
                            total_videos += 1
                else:
                    # Fallback to HLS stream if MP4 not listed
                    hls = cls.get("class_link", "").strip()
                    if hls:
                        output.write(f"{title}:{hls}\n")
                        total_videos += 1

                # Check PDFs
                for pdf in cls.get("classPdf", []):
                    pdf_url = pdf.get("url", "").strip()
                    pdf_name = pdf.get("name", "PDF").strip()
                    if pdf_url:
                        output.write(f"{title} - {pdf_name}:{pdf_url}\n")
                        total_pdfs += 1

            await asyncio.sleep(0.15)  # Guard against API rate limits

    total_links = total_videos + total_pdfs
    if total_links == 0:
        await status_msg.edit_text("⚠️ *No downloadable video or PDF links found in this batch.*")
        return

    # Convert text buffer to file
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
        caption=caption,
        parse_mode="markdown"
    )
    
    await status_msg.delete()
