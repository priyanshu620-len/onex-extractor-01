import os
import re
import uuid
import asyncio
import aiohttp
from datetime import datetime
import pytz
from pyrogram import Client, filters

from Extractor import app
from config import PREMIUM_LOGS, join, BOT_TEXT

API_URL = "https://api.classplusapp.com"
INDIA_TZ = pytz.timezone("Asia/Kolkata")


def get_current_time_str() -> str:
    return datetime.now(INDIA_TZ).strftime("%d %b %Y • %I:%M %p")


def extract_media_url(item: dict) -> str:
    """Extracts media/document URL across all known Classplus JSON response structures."""
    direct_keys = [
        "url",
        "encryptedUrl",
        "downloadUrl",
        "documentUrl",
        "streamUrl",
        "videoUrl",
        "hlsUrl",
        "rawUrl"
    ]
    for key in direct_keys:
        val = item.get(key)
        if val and isinstance(val, str) and val.strip().startswith("http"):
            return val.strip()

    resources = item.get("resources")
    if isinstance(resources, list) and resources:
        for res in resources:
            if isinstance(res, dict):
                for key in direct_keys:
                    val = res.get(key)
                    if val and isinstance(val, str) and val.strip().startswith("http"):
                        return val.strip()
    elif isinstance(resources, dict):
        for key in direct_keys:
            val = resources.get(key)
            if val and isinstance(val, str) and val.strip().startswith("http"):
                return val.strip()

    for nested_obj_key in ["media", "attachment", "file"]:
        nested_obj = item.get(nested_obj_key)
        if isinstance(nested_obj, dict):
            for key in direct_keys:
                val = nested_obj.get(key)
                if val and isinstance(val, str) and val.strip().startswith("http"):
                    return val.strip()

    return ""


async def register_fallback(
    session: aiohttp.ClientSession,
    headers: dict,
    org_id: str,
    org_name: str,
    mobile: str,
    otp: str,
    session_id: str,
    fingerprint_id: str
) -> str | None:
    """Helper to handle registration when login returns 201/409."""
    email = f"{uuid.uuid4().hex}@gmail.com"
    payload = {
        "contact": {
            "email": email,
            "countryExt": "91",
            "mobile": mobile
        },
        "fingerprintId": fingerprint_id,
        "name": "Student",
        "orgId": org_id,
        "orgName": org_name,
        "otp": otp,
        "sessionId": session_id,
        "type": 1,
        "viaEmail": 0,
        "viaSms": 1
    }
    try:
        async with session.post(f"{API_URL}/v2/users/register", json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("data", {}).get("token")
    except Exception as e:
        print(f"Registration error: {e}")
    return None


@app.on_message(filters.command(["cp"]))
async def classplus_handler(client: Client, message):
    details = await client.ask(
        message.chat.id,
        "<blockquote><b>✦ C L A S S P L U S  •  E X T R A C T O R ✦</b>\n\n"
        "Send your credentials in this format:\n"
        "<code>ORG_CODE*Mobile</code>\n\n"
        "<i>Or paste your direct access token directly.</i></blockquote>"
    )
    user_input = details.text.strip()

    token = None
    org_name = None

    async with aiohttp.ClientSession() as session:
        if "*" in user_input:
            try:
                org_code, mobile = user_input.split("*", 1)
                device_id = uuid.uuid4().hex

                headers = {
                    "Accept": "application/json, text/plain, */*",
                    "region": "IN",
                    "accept-language": "en",
                    "Content-Type": "application/json;charset=utf-8",
                    "Api-Version": "51",
                    "device-id": device_id
                }

                # Step 1: Fetch Org Details
                async with session.get(f"{API_URL}/v2/orgs/{org_code}", headers=headers) as resp:
                    if resp.status != 200:
                        return await message.reply("<blockquote><b>✗ Error:</b> Invalid Organization Code.</blockquote>")
                    org_data = await resp.json()
                    org_id = org_data["data"]["orgId"]
                    org_name = org_data["data"]["orgName"]

                # Step 2: Generate OTP
                otp_payload = {
                    "countryExt": "91",
                    "orgCode": org_name,
                    "viaSms": "1",
                    "mobile": mobile,
                    "orgId": org_id,
                    "otpCount": 0
                }

                async with session.post(f"{API_URL}/v2/otp/generate", json=otp_payload, headers=headers) as resp:
                    if resp.status != 200:
                        return await message.reply("<blockquote><b>✗ Error:</b> OTP generation failed. Check your mobile number.</blockquote>")
                    otp_data = await resp.json()
                    session_id = otp_data["data"]["sessionId"]

                # Step 3: Ask User for OTP
                user_otp_msg = await client.ask(
                    message.chat.id,
                    "<blockquote><b>🔐 Verification Required</b>\n\n"
                    "Enter the 4/6-digit OTP sent to your registered number:</blockquote>",
                    timeout=300
                )

                if not user_otp_msg.text.strip().isdigit():
                    return await message.reply("<blockquote><b>✗ Error:</b> OTP must contain numbers only.</blockquote>")

                otp = user_otp_msg.text.strip()
                fingerprint_id = uuid.uuid4().hex

                # Step 4: Verify OTP
                verify_payload = {
                    "otp": otp,
                    "countryExt": "91",
                    "sessionId": session_id,
                    "orgId": org_id,
                    "fingerprintId": fingerprint_id,
                    "mobile": mobile
                }

                async with session.post(f"{API_URL}/v2/users/verify", json=verify_payload, headers=headers) as resp:
                    if resp.status == 200:
                        verify_data = await resp.json()
                        token = verify_data.get("data", {}).get("token")
                    elif resp.status in (201, 409):
                        token = await register_fallback(
                            session, headers, org_id, org_name, mobile, otp, session_id, fingerprint_id
                        )

                if not token:
                    return await message.reply("<blockquote><b>✗ Error:</b> Verification failed. Invalid OTP or session expired.</blockquote>")

                await message.reply_text(
                    "<blockquote><b>✓ Authentication Successful</b>\n\n"
                    "<b>Token:</b>\n"
                    f"<code>{token}</code></blockquote>"
                )
                await client.send_message(
                    PREMIUM_LOGS,
                    "<blockquote><b>✦ New Login Session</b>\n\n"
                    f"<b>App:</b> <code>{org_name}</code>\n"
                    f"<b>Token:</b> <code>{token}</code></blockquote>"
                )

            except Exception as e:
                return await message.reply(f"<blockquote><b>✗ Exception:</b> <code>{str(e)}</code></blockquote>")

        elif len(user_input) > 20:
            token = user_input
            await client.send_message(PREMIUM_LOGS, f"<blockquote><b>✦ Direct Token Session</b>\n<code>{token}</code></blockquote>")
        else:
            return await message.reply("<blockquote><b>✗ Error:</b> Invalid input format provided.</blockquote>")

        # Step 5: Fetch Course Batches
        auth_headers = {
            "x-access-token": token,
            "user-agent": "Mobile-Android",
            "app-version": "1.4.65.3",
            "api-version": "29",
            "device-id": "39F093FF35F201D9"
        }

        async with session.get(f"{API_URL}/v2/courses?tabCategoryId=1", headers=auth_headers) as resp:
            if resp.status != 200:
                return await message.reply("<blockquote><b>✗ Error:</b> Unable to fetch courses with this session.</blockquote>")
            res_data = await resp.json()
            courses = res_data.get("data", {}).get("courses", [])

        if not courses:
            return await message.reply("<blockquote><b>✗ Notice:</b> No enrolled batches/courses found.</blockquote>")

        if not org_name:
            shareable_link = courses[0].get("shareableLink", "")
            if "courses.store" in shareable_link:
                org_name = shareable_link.split(".")[0].split("//")[-1]
            elif "//" in shareable_link and len(shareable_link.split("//")[1].split(".")) > 1:
                org_name = shareable_link.split("//")[1].split(".")[1]
            else:
                org_name = "Classplus"

        courses_dict = {str(c["id"]): c["name"] for c in courses}
        await prompt_and_extract_batches(client, message, session, auth_headers, courses_dict, org_name)


async def prompt_and_extract_batches(
    client: Client,
    message,
    session: aiohttp.ClientSession,
    auth_headers: dict,
    courses: dict,
    org_name: str
):
    text = "<b>Available Batches</b>\n\n"
    course_list = []
    for idx, (course_id, course_name) in enumerate(courses.items(), start=1):
        text += f"<code>{idx:02d}.</code> {course_name}\n"
        course_list.append((idx, course_id, course_name))

    await client.send_message(PREMIUM_LOGS, f"<blockquote>{text}</blockquote>")

    selected_input = await client.ask(
        message.chat.id,
        f"<blockquote>{text}\n<b>Send the batch number to begin extraction:</b></blockquote>",
        timeout=180
    )

    if not selected_input.text.strip().isdigit():
        return await message.reply("<blockquote><b>✗ Error:</b> Please provide a valid index number.</blockquote>")

    selected_idx = int(selected_input.text.strip())
    if not (1 <= selected_idx <= len(course_list)):
        return await message.reply("<blockquote><b>✗ Error:</b> Batch index out of range.</blockquote>")

    _, selected_course_id, selected_course_name = course_list[selected_idx - 1]

    status_msg = await message.reply(
        "<blockquote>⚡ <b>Extracting course index structure...</b>\n"
        f"<b>Target:</b> <code>{selected_course_name}</code></blockquote>"
    )

    # Recursive Course Extractor with Full Pagination
    async def process_course_contents(course_id: str, folder_id: int = 0, folder_path: str = "") -> list:
        result = []
        limit = 100
        offset = 0

        while True:
            url = f"{API_URL}/v2/course/content/get?courseId={course_id}&folderId={folder_id}&limit={limit}&offset={offset}"
            try:
                async with session.get(url, headers=auth_headers) as resp:
                    if resp.status != 200:
                        break
                    data = await resp.json()
                    course_data = data.get("data", {}).get("courseContent", [])
            except Exception as e:
                print(f"Error reading folder {folder_id}: {e}")
                break

            if not course_data:
                break

            tasks = []
            for item in course_data:
                content_type = str(item.get("contentType", ""))
                sub_id = item.get("id")
                sub_name = item.get("name", "Untitled Content").replace(":", " -")

                if content_type == "1":
                    new_folder_path = f"{folder_path}{sub_name} - "
                    tasks.append(process_course_contents(course_id, sub_id, new_folder_path))
                else:
                    media_url = extract_media_url(item)
                    if media_url:
                        result.append(f"{folder_path}{sub_name}: {media_url}\n")

            if tasks:
                sub_contents = await asyncio.gather(*tasks)
                for sub_list in sub_contents:
                    result.extend(sub_list)

            if len(course_data) < limit:
                break

            offset += limit

        return result

    # Live Videos Extractor with Pagination
    async def fetch_live_videos(course_id: str) -> list:
        outputs = []
        limit = 100
        offset = 0

        while True:
            url = f"{API_URL}/v2/course/live/list/videos?type=2&entityId={course_id}&limit={limit}&offset={offset}"
            try:
                async with session.get(url, headers=auth_headers) as resp:
                    if resp.status != 200:
                        break
                    j = await resp.json()
                    video_list = j.get("data", {}).get("list", [])
            except Exception as e:
                print(f"Error fetching live videos: {e}")
                break

            if not video_list:
                break

            for video in video_list:
                name = video.get("name", "Live Video").replace(":", " -")
                video_url = extract_media_url(video)
                if video_url:
                    outputs.append(f"[LIVE] {name}: {video_url}\n")

            if len(video_list) < limit:
                break

            offset += limit

        return outputs

    extracted_data, live_videos = await asyncio.gather(
        process_course_contents(selected_course_id),
        fetch_live_videos(selected_course_id)
    )
    extracted_data.extend(live_videos)

    if not extracted_data:
        return await status_msg.edit_text("<blockquote><b>✗ Notice:</b> No media files or documents found in this batch.</blockquote>")

    clean_name = re.sub(r'[\t:/+#|@*.\\]', '', selected_course_name).replace('_', ' ')
    file_path = f"{clean_name}.txt"

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(extracted_data)

    video_count = sum(1 for line in extracted_data if any(x in line.lower() for x in [".mp4", ".m3u8", "video", "master.m3u8"]))
    pdf_count = sum(1 for line in extracted_data if any(x in line.lower() for x in [".pdf", ".doc", ".epub"]))
    total_links = len(extracted_data)
    other_count = total_links - (video_count + pdf_count)

    bot_user = await client.get_me()

    # Aesthetic Telegram Blockquote Card Caption
    caption = (
        "<blockquote>"
        "╭──  <b>COURSE EXTRACTION REPORT</b>  ──╮\n"
        f"│ 🏷️ <b>Platform  :</b> <code>{org_name}</code>\n"
        f"│ 📦 <b>Batch     :</b> <code>{selected_course_name}</code>\n"
        f"│ 🕒 <b>Timestamp :</b> <code>{get_current_time_str()}</code>\n"
        "├──────────────────────────\n"
        "│ 📊 <b>Resource Breakdown :</b>\n"
        f"│   ├ 🎥 <b>Videos   :</b> <code>{video_count}</code>\n"
        f"│   ├ 📄 <b>PDFs     :</b> <code>{pdf_count}</code>\n"
        f"│   ├ 📁 <b>Others   :</b> <code>{other_count}</code>\n"
        f"│   └ 🔗 <b>Total    :</b> <code>{total_links}</code>\n"
        "╰──────────────────────────╯\n"
        f"⚡ <b>Engine :</b> @{bot_user.username}\n"
        f"<code>{BOT_TEXT}</code>"
        "</blockquote>"
    )

    await client.send_document(message.chat.id, file_path, caption=caption)
    await client.send_document(PREMIUM_LOGS, file_path, caption=caption)

    if os.path.exists(file_path):
        os.remove(file_path)
    await status_msg.delete()
