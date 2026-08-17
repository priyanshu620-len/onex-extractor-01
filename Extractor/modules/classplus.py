import os
import re
import string
import random
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyromod import listen
import down

HEADERS_CP = {
    'api-version': '29',
    'app-version': '1.4.73.1',
    'build-number': '29',
    'connection': 'Keep-Alive',
    'content-type': 'application/json',
    'device-details': 'REDMI_Note_9_SDK-30',
    'host': 'api.classplusapp.com',
    'region': 'IN',
    'user-agent': 'Mobile-Android',
    'x-chrome-version': '112.0.5615.136',
    'x-webview-version': '112.0.5615.136',
}

def parsename(name: str) -> str:
    for char in ["||", "/", ":", "|", '"', ";"]:
        name = name.replace(char, "-" if char == ":" else "_")
    return name.strip()

async def get_cp_token(bot: Client, m: Message, otm: str, ct1: int):
    editable = await bot.send_message(ct1, f"**Send your Credentials in This Format :**\n{otm}*OrgCode")
    try:
        user_input: Message = await bot.listen(editable.chat.id)
        raw_text = user_input.text.strip()
        await user_input.delete(True)

        if "*" not in raw_text:
            await editable.edit(f"**Error ❌\nSend in this Format : `{otm}*OrgCode`**")
            return

        em, org_code = raw_text.split("*", 1)
        rname = ''.join(random.choices(string.digits + string.ascii_lowercase, k=16))
        rnameb = ''.join(random.choices(string.digits + string.ascii_letters, k=11))
        rnamec = ''.join(random.choices(string.digits + string.ascii_letters, k=32))

        req_headers = {**HEADERS_CP, 'device-id': rname}
        auth_headers = {"User-Agent": "Mobile-Android"}

        async with aiohttp.ClientSession() as session:
            # 1. Fetch Organization Details
            async with session.get(f"https://api.classplusapp.com/v2/orgs/{org_code}", headers=auth_headers) as resp:
                rs = await resp.json()

            if rs.get('status') != 'success':
                await editable.edit(f"Error ❌\n**Reason :** `{rs.get('message')}`")
                return

            org_id = rs['data']['orgId']
            contact_field = "email" if "@" in em else "mobile"
            via_flag = "viaEmail" if "@" in em else "viaSms"

            mdata = {
                "countryExt": "91",
                "eventType": "login",
                "otpHash": rnameb,
                "orgId": org_id,
                contact_field: str(em),
                via_flag: 1
            }

            # 2. Generate OTP
            async with session.post('https://api.classplusapp.com/v2/otp/generate', headers=req_headers, json=mdata) as resp:
                mr = await resp.json()

            if mr.get('status') != 'success':
                await editable.edit(f"Error ❌\n**Reason :** `{mr.get('message')}`")
                return

            session_id = str(mr['data']['sessionId'])
            await editable.edit(f"**{mr.get('message')} to {otm} :** `{em}`\n**Now Send OTP**")

            # 3. Receive and Verify OTP
            otp_input: Message = await bot.listen(editable.chat.id)
            otpa = otp_input.text.strip()
            await otp_input.delete(True)

            verify_data = {
                "fingerprintId": rnamec,
                "countryExt": "91",
                "orgId": org_id,
                contact_field: str(em),
                "otp": str(otpa),
                "sessionId": session_id,
            }

            async with session.post('https://api.classplusapp.com/v2/users/verify', headers=req_headers, json=verify_data) as resp:
                mra = await resp.json()

            if mra.get('status') == 'success' and mra['data'].get('user', {}).get('exists') == 1:
                tokk = mra['data']['token']
                await editable.edit(f"**{mra.get('message')} ✅**\n**Token :-**\n`{tokk}`")
            else:
                reason = mra.get('message', "User Doesn't Exist")
                await editable.edit(f"**Login Failed ❌**\n**Reason :-**\n`{reason}`")

    except Exception as e:
        await bot.send_message(ct1, f"**Error:** `{str(e)}`")


async def get_textcp(bot: Client, m: Message, ct2: int):
    editable = await bot.send_message(ct2, "**Now, Send Token**")
    try:
        user_input: Message = await bot.listen(editable.chat.id)
        tokk = user_input.text.strip()
        await user_input.delete(True)

        headers = {
            "X-Access-Token": tokk,
            "User-Agent": "Mobile-Android",
            "Api-Version": "40"
        }

        bat = down.get_batch(tokk)
        if '✳️' not in str(bat):
            await editable.edit(f"`No Courses Found` ❌" if len(str(bat)) < 5 else f"Error ❌\n**Reason : **`{bat}`")
            return

        fff = "**CourseID ✳️ CourseName**"
        await editable.edit(f"**Your Purchased Courses :-\n{fff}\n\n{bat}\n\nSend CourseId(s) (comma-separated):**")

        batch_input: Message = await bot.listen(editable.chat.id)
        batch_ids = [cid.strip() for cid in batch_input.text.split(",") if cid.strip()]
        await batch_input.delete(True)

        async with aiohttp.ClientSession() as session:
            for cid in batch_ids:
                async with session.get(f"https://api.classplusapp.com/v2/course/{cid}", headers=headers) as resp:
                    rt = await resp.json()

                if rt.get('status') != 'success':
                    await bot.send_message(ct2, f"Error fetching `{cid}` ❌\n**Reason : **`{rt.get('message')}`")
                    continue

                rtt = rt['data']['course']
                bname = rtt['details']['name']
                thumb = rtt['details'].get('imageUrl', '')
                resources = rtt.get('resources', {})
                files_count = resources.get('files', 0)
                videos_count = resources.get('videos', 0)

                await editable.edit(
                    f"**Generating Txt For :**\n\n"
                    f"**Batch :** `{cid}` - {bname}\n\n"
                    f"**Files :** `{files_count}` 📂  |  **Videos :** `{videos_count}` 🎬\n\n"
                    f"**Thumbnail :** `{thumb}`"
                )

                params = {'courseId': cid, 'folderId': '0'}
                async with session.get('https://api.classplusapp.com/v2/course/content/get', params=params, headers=headers) as resp:
                    resa = await resp.json()

                if resa.get('status') != 'success':
                    await bot.send_message(ct2, f"Failed retrieving content for `{cid}`: `{resa.get('message')}`")
                    continue

                course_contents = resa.get('data', {}).get('courseContent', [])
                links_data = []

                for item in course_contents:
                    c_type = item.get('contentType')
                    name = str(item.get('name', '')).replace("/", "-").replace(":", "-")

                    if c_type == 1:
                        try:
                            content_id = str(item['id'])
                            content_course_id = str(item['contentCourseId'])
                            folder_links = down.get_folder_content(tokk, content_course_id, cid, content_id)
                            links_data.append(folder_links)
                        except Exception:
                            continue
                    else:
                        url = str(item.get('url', ''))
                        if url:
                            links_data.append(f"{name}:{url}\n")

                content_str = "".join(links_data)
                if not content_str.strip():
                    await bot.send_message(ct2, f"No Links Found for Batch `{cid}` ❌")
                    continue

                clean_bname = parsename(bname)
                filename = f"{cid} - {clean_bname}.txt"

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content_str)

                await asyncio.sleep(1)

                caption = (
                    f"📌 **Batch Details:**\n"
                    f"┌───📚 **Batch:** {bname}\n"
                    f"└──────────────────────────\n\n"
                    f"📂 **Batch Info:**\n"
                    f"┌───📲 **Application:** Classplus\n"
                    f"└──────────────────────────\n\n"
                    f"📂 **Content Overview:**\n"
                    f"┌───🔗 **Total Links:** {videos_count + files_count}\n"
                    f"│    ├ 🎥 **Videos:** {videos_count} 📹\n"
                    f"│    └ 📄 **PDFs:** {files_count} 📁\n"
                    f"└──────────────────────────"
                )

                await bot.send_document(ct2, filename, caption=caption)
                if os.path.exists(filename):
                    os.remove(filename)

        await editable.delete(True)
        await bot.send_message(ct2, "**Done ✅✅**")

    except Exception as e:
        await bot.send_message(ct2, f"**Fatal Error:** `{str(e)}`")
