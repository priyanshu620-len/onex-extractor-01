from logging import exception  # This should be removed
import requests
from pyrogram import Client, filters
from pyromod import listen
from config import *
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode
import os
import re

KEY = b'^#^#&@*HDU@&@*()'   
IV = b'^@%#&*NSHUE&$*#)' 
# Encryption function
def enc_url(url):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    ciphertext = cipher.encrypt(pad(url.encode(), AES.block_size))
    return "helper://" + b64encode(ciphertext).decode('utf-8')  # helper:// prefix add karna

def count_urls(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        total_links = len(lines)

        pdf_links = 0
        video_links = 0

        for line in lines:
            url = line.lower()
            if ".pdf" in url:
                pdf_links += 1
            else:
                video_links += 1

        return total_links, pdf_links, video_links
    except Exception:
        return 0, 0, 0
# Function to split name & URL properly
def split_name_url(line):
    match = re.search(r"(https?://\S+)", line)  # Find `https://` ya `http://` ke baad ka URL
    if match:
        name = line[:match.start()].strip().rstrip(":")  # URL se pehle ka text (extra `:` hatao)
        url = match.group(1).strip()  # Sirf URL
        return name, url
    return line.strip(), None  # Agar URL nahi mila, to pura line name maan lo

# Function to encrypt file URLs
def encrypt_file(input_file):
    output_file = "encrypted_" + input_file  # Output file ka naam
    with open(input_file, "r", encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:
        for line in f:
            name, url = split_name_url(line)  # Sahi tarike se name aur URL split karo
            if url:
                enc = enc_url(url)  # Encrypt URL
                out.write(f"{name}: {enc}\n")  # Ek hi `:` likho
            else:
                out.write(line.strip() + "\n")  # Agar URL nahi mila to line jaisa hai waisa likho
    return output_file 

# telegram_bot = Client("app", api_id=api_id, api_hash=api_hash, bot_token=bot_token) 
from pyrogram.types import Message

async def pinnacle_txt(bot, message: Message):
    user_id = message.from_user.id

    categ = {}
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'origin': 'https://videos.ssccglpinnacle.com',
        'priority': 'u=1, i',
        'referer': 'https://videos.ssccglpinnacle.com/',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    }

    response = requests.get('https://auth.ssccglpinnacle.com/categories', headers=headers)
    categ_data = response.json()
    aa = ''
    categ = {}
    categ_ids = []

    for index, data in enumerate(categ_data):
        aa += f"🔸 `{index + 1}` → {data['categoryTitle']}\n"
        categ_ids.append(data["_id"])
        categ[data["_id"]] = data["categoryTitle"]

    # Ask for index
    category_msg = await message.chat.ask(f"Enter the number of the category you want to scrape:\n\n{aa}")

    try:
        index = int(category_msg.text.strip()) - 1
        if 0 <= index < len(categ_ids):
            category_id = categ_ids[index]
            category_name = categ[category_id]
            # await message.reply(f"you selcted>>>{category_name}")
        else:
            await message.reply("❌ Invalid category number.")
            return
    except ValueError:
        await message.reply("❌ Please enter a valid number.")
        return


    try:
        categ_id = category_name.strip()
        print(categ_id)
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'origin': 'https://videos.ssccglpinnacle.com',
            'priority': 'u=1, i',
            'referer': 'https://videos.ssccglpinnacle.com/',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        }

        response = requests.get(f'https://auth.ssccglpinnacle.com/api/videoCourses/{categ_id}', headers=headers)
        batches_data = response.json()
        batch_detail = {}
        b_d = ''

        # Create a list to map index to batch _id
        batch_ids = []

        for index, data in enumerate(batches_data):
            b_d += f"🔹 `{index + 1}` → **{data['courseTitle']} 💵₹{data['price']}**\n"
            # b_d += f"{index + 1}. {data['courseTitle']}\nPrice: ₹{data['price']}\n\n"
            batch_ids.append(data["_id"])
            batch_detail[data["_id"]] = {
                "name": data["courseTitle"],
                "price": str(data['price']),
                "thumbnail": data['englishCoverImage']
            }

        # Ask the user for index input
        msg = await message.chat.ask(f"Select a batch by number:\n\n{b_d}")
        index = int(msg.text.strip()) - 1

        # Get the actual batch_id using the index
        if 0 <= index < len(batch_ids):
            batch_id = batch_ids[index]
        else:
            await message.reply("Invalid selection.")
            return
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'origin': 'https://videos.ssccglpinnacle.com',
            'priority': 'u=1, i',
            'referer': 'https://videos.ssccglpinnacle.com/',
            'sec-ch- ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        }

        response = requests.get(
            f'https://auth.ssccglpinnacle.com/api/youtubeChapters/course/{batch_id}',
            headers=headers,
        )

        urls = []

        topic = response.json()
        for top in topic:
            vids = top['topics']
            for vid in vids:
                urls.append(vid['videoTitle'] + ' : ' + vid['videoYoutubeLink'] + '\n')
        batch_name = batch_detail[f'{batch_id}']['name']
        # price = batch_detail[f'{batch_id.text}']['price']
        # thumbnail = batch_detail[f'{batch_id.text}']['thumbnail']
        filename = f'{batch_name}.txt'
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(''.join(urls))
        try:
            enc_file = encrypt_file(filename)
            selected = batch_detail[f'{batch_id}']

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
                "┣ 📛 <code>{}</code>\n"
                "┣ 💵 ₹{}\n"
                "┣ 🖼 <a href=\"{}\">Thumbnail</a>\n"
                "┣ 📅 Start: <i>None</i>\n"
                "┗ ⏳ Expiry: <i>None</i></n\n"
                "<b><pre>📊 Content:</b>\n"
                "    🔗 Total: <code>{}</code>\n"
                "    🎥 Videos: <code>{}</code>\n"
                "    📄 PDFs: <code>{}</code></pre>\n\n"
                "<b>⏱ Time Taken:</b> <i>0.00</i>\n"
                "<b>🏆 Extracted By:</b> {}"
            ).format(
                selected['name'],
                selected['price'],
                selected['thumbnail'],
                total,
                videos,
                pdfs,
                mention
            )
            
            # caption = (
            #     f"📚 Batch Name: {selected['name']}\n"
            #     f"🆔 Batch ID: {batch_id.text}\n"
            #     f"💰 Price: ₹{selected['price']}\n"
            #     f"🖼 Thumbnail: [Click Here]({selected['thumbnail']})\n"
            #     f"🔒 All URLs are encrypted\n"
            # )

            await bot.send_document(message.chat.id, document=enc_file, caption=caption, thumb=image)
            await bot.send_document(LOGS_CHANNEL, document=filename, caption=caption, thumb=image)
            os.remove(filename)
            os.remove(enc_file)
        except Exception as e:  # Changed from 'exception' to 'Exception'
            await message.reply(f"Error: {e}")
    
    except ValueError as e:
        await message.reply(f"Error parsing JSON: {e}")
