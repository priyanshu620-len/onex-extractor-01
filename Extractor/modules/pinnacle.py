import os
import re
from base64 import b64encode

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod import listen
import requests

from config import *

KEY = b"^#^#&@*HDU@&@*()"
IV = b"^@%#&*NSHUE&$*#)"

COMMON_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "origin": "https://videos.ssccglpinnacle.com",
    "priority": "u=1, i",
    "referer": "https://videos.ssccglpinnacle.com/",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}


def enc_url(url: str) -> str:
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    ciphertext = cipher.encrypt(pad(url.encode("utf-8"), AES.block_size))
    return "helper://" + b64encode(ciphertext).decode("utf-8")


def count_urls(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        total_links = len(lines)
        pdf_links = sum(1 for line in lines if ".pdf" in line.lower())
        video_links = total_links - pdf_links

        return total_links, pdf_links, video_links
    except Exception:
        return 0, 0, 0


def split_name_url(line: str):
    match = re.search(r"(https?://\S+)", line)
    if match:
        name = line[: match.start()].strip().rstrip(":")
        url = match.group(1).strip()
        return name, url
    return line.strip(), None


def encrypt_file(input_file: str) -> str:
    output_file = "encrypted_" + input_file
    with (
        open(input_file, "r", encoding="utf-8") as f,
        open(output_file, "w", encoding="utf-8") as out,
    ):
        for line in f:
            name, url = split_name_url(line)
            if url:
                enc = enc_url(url)
                out.write(f"{name}: {enc}\n")
            else:
                out.write(line.strip() + "\n")
    return output_file


async def pinnacle_txt(bot: Client, message: Message):
    user_id = message.from_user.id

    try:
        response = requests.get(
            "https://auth.ssccglpinnacle.com/categories", headers=COMMON_HEADERS
        )
        categ_data = response.json()
    except Exception as e:
        await message.reply(f"❌ Failed to fetch categories: {e}")
        return

    menu_text = ""
    categ_ids = []
    categ_names = {}

    for index, data in enumerate(categ_data):
        menu_text += f"🔸 `{index + 1}` → {data['categoryTitle']}\n"
        categ_ids.append(data["_id"])
        categ_names[data["_id"]] = data["categoryTitle"]

    category_msg = await message.chat.ask(
        f"Enter the number of the category you want to scrape:\n\n{menu_text}"
    )

    try:
        cat_index = int(category_msg.text.strip()) - 1
        if 0 <= cat_index < len(categ_ids):
            category_id = categ_ids[cat_index]
        else:
            await message.reply("❌ Invalid category number.")
            return
    except ValueError:
        await message.reply("❌ Please enter a valid number.")
        return

    try:
        # Fixed: using category_id instead of category_name
        response = requests.get(
            f"https://auth.ssccglpinnacle.com/api/videoCourses/{category_id}",
            headers=COMMON_HEADERS,
        )
        batches_data = response.json()
        if not batches_data:
            await message.reply("❌ No batches found in this category.")
            return

        batch_ids = []
        batch_detail = {}
        batch_menu = ""

        for index, data in enumerate(batches_data):
            batch_menu += (
                f"🔹 `{index + 1}` → **{data['courseTitle']} 💵₹{data['price']}**\n"
            )
            batch_ids.append(data["_id"])
            batch_detail[data["_id"]] = {
                "name": data["courseTitle"],
                "price": str(data["price"]),
                "thumbnail": data.get("englishCoverImage", ""),
            }

        msg = await message.chat.ask(f"Select a batch by number:\n\n{batch_menu}")
        try:
            batch_index = int(msg.text.strip()) - 1
            if 0 <= batch_index < len(batch_ids):
                batch_id = batch_ids[batch_index]
            else:
                await message.reply("❌ Invalid batch selection.")
                return
        except ValueError:
            await message.reply("❌ Please enter a valid number.")
            return

        response = requests.get(
            f"https://auth.ssccglpinnacle.com/api/youtubeChapters/course/{batch_id}",
            headers=COMMON_HEADERS,
        )
        topic = response.json()

        urls = []
        for top in topic:
            vids = top.get("topics", [])
            for vid in vids:
                urls.append(
                    f"{vid.get('videoTitle', 'Untitled')} : {vid.get('videoYoutubeLink', '')}\n"
                )

        selected = batch_detail[batch_id]
        safe_batch_name = re.sub(r'[\\/*?:"<>|]', "", selected["name"])
        filename = f"{safe_batch_name}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(urls)

        enc_file = encrypt_file(filename)

        try:
            user = await bot.get_users(user_id)
            full_name = f"{user.first_name} {user.last_name or ''}".strip()
            mention = f"[{full_name}](tg://user?id={user.id})"
        except Exception:
            mention = "Unknown"

        total, pdfs, videos = count_urls(filename)

        caption = (
            "<b>📦 Batch Extracted!</b>\n"
            "<pre><b>📱 App:</b> Pinnacle Academy</pre>\n\n"
            "<b>📦 Batch:</b>\n"
            f"┣ 📛 <code>{selected['name']}</code>\n"
            f"┣ 💵 ₹{selected['price']}\n"
            f'┣ 🖼 <a href="{selected["thumbnail"]}">Thumbnail</a>\n'
            "┣ 📅 Start: <i>None</i>\n"
            "┗ ⏳ Expiry: <i>None</i>\n\n"
            "<b><pre>📊 Content:</b>\n"
            f"    🔗 Total: <code>{total}</code>\n"
            f"    🎥 Videos: <code>{videos}</code>\n"
            f"    📄 PDFs: <code>{pdfs}</code></pre>\n\n"
            "<b>⏱ Time Taken:</b> <i>0.00</i>\n"
            f"<b>🏆 Extracted By:</b> {mention}"
        )

        thumb_path = globals().get("image", None)

        await bot.send_document(
            message.chat.id, document=enc_file, caption=caption, thumb=thumb_path
        )
        if "LOGS_CHANNEL" in globals():
            await bot.send_document(
                LOGS_CHANNEL,
                document=filename,
                caption=caption,
                thumb=thumb_path,
            )

        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(enc_file):
            os.remove(enc_file)

    except Exception as e:
        await message.reply(f"❌ An error occurred: {e}")
