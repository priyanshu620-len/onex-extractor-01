import os
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
import requests, json, subprocess, re, sys, string, random, time, datetime, logging
from subprocess import getstatusoutput
from pyrogram import Client, filters
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import ApiCallError, FloodWait, MessageNotModified
from pyromod import listen
from pyrogram.types import User, Message
import tgcrypto
import down
from urllib import request
import glob, aiohttp, asyncio, aiofiles, shutil
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64encode, b64decode
from random import randint, randrange

headerscp = {
           'api-version':'29',
           'app-version':'1.4.73.1',
           'build-number':'29',
           'connection':'Keep-Alive',
           'content-type':'application/json',
           'device-details':'REDMI_Note_9_SDK-30',
           'host':'api.classplusapp.com',
           'region':'IN',
           'user-agent':'Mobile-Android',
           'x-chrome-version':'112.0.5615.136',
           'x-webview-version':'112.0.5615.136', }

def parsename(name: str):
    name_r = name.replace("||", "_").replace("/", "_").replace(":", "-").replace("|", "_").replace('"', '_').replace(';', '_').strip()
    return name_r

async def get_cp_token(bot: Client, m: Message, otm, ct1):
    editable = await bot.send_message(ct1,f"**Send your Credentials in This Format :**\n{otm}*OrgCode")
    input: Message = await bot.listen(editable.chat.id) 
    raw_text = input.text
    await input.delete(True)
    rname = ''.join(random.choice(string.digits+string.ascii_lowercase) for _ in range(16))
    rnameb = ''.join(random.choice(string.digits+string.ascii_lowercase+string.ascii_uppercase) for _ in range(11))
    rnamec = ''.join(random.choice(string.digits+string.ascii_lowercase+string.ascii_uppercase) for _ in range(32))
    headerscp.update({'device-id':rname,})
    headersa = {"User-Agent": "Mobile-Android",}  
    mdata = {"countryExt": "91", 
    "eventType": "login", 
    "otpHash": rnameb,
    }
    data1 = {
      "fingerprintId": rnamec, 
      "countryExt": "91",
      }
    try:
        if "*" in raw_text:
           em, ps = raw_text.split("*")
           print(em,ps)
           rs = requests.get(f"https://api.classplusapp.com/v2/orgs/{ps}",headers=headersa).json()
           mk = rs['message']
           if rs['status'] == 'success':
              r1, r2= rs['data']['orgId'], rs['data']['orgName']
           else:
              await editable.edit(f"Error ❌\n**Reason :** `{mk}`")
              return                    
           if '@' in em:
              mdata.update({"email": str(em),'viaEmail': '1',"orgId": r1,})
              data1.update({"email": str(em),"orgId": r1,})
           else:
              mdata.update({"mobile": str(em),"viaSms": 1,"orgId": r1,})
              data1.update({"mobile": str(em),"orgId": r1,})
           try:
              mr = requests.post('https://api.classplusapp.com/v2/otp/generate',headers=headerscp,json=mdata,).json()
              md = mr['message']
              if mr['status'] == 'success':
                 ssid = str(mr['data']['sessionId'])
                 stt, mms = mr['status'], mr['message']
                 await editable.edit(f"**{mms} to {otm}. :** `{em}`\n**Now Send OTP**")
              else:
                 await editable.edit(f"Error ❌\n**Reason :** `{md}`")
                 return
              input2: Message = await bot.listen(editable.chat.id)
              otpa = input2.text
              await input2.delete(True)
              data1.update({"otp": str(otpa), "sessionId": ssid,})
              try:
                 mra = requests.post('https://api.classplusapp.com/v2/users/verify',headers=headerscp,json=data1,).json()
                 #pprint(mra)
                 mm = mra['message']
                 if mra['status'] == 'success':
                    usd = mra['data']['user']['exists']
                    if usd ==1:
                       uid, tokk = mra['data']['user'], mra['data']['token']
                       print('Token : '+tokk)
                       await editable.edit(f"**{mm} ✅**\n**Token :-**\n`{tokk}`")
                    else:
                       await editable.edit(f"**Error ❌\n`Lol🤣 User Doesn't Exist`**")
                       return
                 else:
                    await editable.edit(f"**Login Failed ❌**\n**Reason :-**\n`{mm}`")
                    return
              except Exception as e:
                 await bot.send_message(ct1,e)
           except Exception as e:
              await bot.send_message(ct1,e)
        else:
           await editable.edit(f"**Error ❌\nSend in this Format :`{otm}*OrgCode`**")
           return
    except Exception as e:
      await bot.send_message(ct1,e)
 
async def get_textcp(bot: Client, m: Message, ct2):
    editable = await bot.send_message(ct2,f"Now, Send **Token**")
    input: Message = await bot.listen(editable.chat.id) 
    raw_text2 = input.text
    tokk = raw_text2
    print(tokk)
    await input.delete(True)
    headers = {"X-Access-Token": f"{tokk}",
            "User-Agent": "Mobile-Android",
            "Api-Version": "40"}
    try:
       bat = down.get_batch(tokk)
       print(bat)
       if '✳️' in bat:
          FFF = "**CourseID ✳️ CourseName**"
          editable1 = await editable.edit(f"**Your Purchased Courses :-\n{FFF}\n\n**{bat}**\n\n**Send CourseId : **")
       elif len(bat)<5:
          await editable.edit(f"`No Courses Found` ❌")
          return
       else:
          await editable.edit(f"Error ❌\n**Reason : **`{bat}`")
          return
       try:
          input2: Message = await bot.listen(editable.chat.id)
          batchids = input2.text
          await input2.delete(True)
          xv = batchids.split(',')
          for y in range(0, len(xv)):
              cid = xv[y]
              rt = requests.get(f"https://api.classplusapp.com/v2/course/{cid}", headers=headers).json()
              mdh = rt['message']
              if rt['status'] == 'success':
                 rtt = rt['data']['course']
                 bname, thumb = rtt['details']['name'], rtt['details']['imageUrl']
                 resources = rtt['resources']
                 files, videos = resources['files'], resources['videos']
                 await editable.edit(f"**Geneterating Txt For :\n\nBatch : `{cid}` - {bname}\n\nFiles : `{files}` 📂  |  Videos : `{videos}` 🎬\n\nThumbnail :** `{thumb}`")
              else:
                 await editable.edit(f"Error ❌\n**Reason : **`{mdh}`")
                 return
              try:
                 bnm = bname.replace(":","-").replace("/","_")
                 filename = f"{cid} - {bnm}.txt"
                 capt = f"Batch ID - {cid}"
                 params = {'courseId': cid,'folderId': '0'}                 
                 resa = requests.get('https://api.classplusapp.com/v2/course/content/get', params=params, headers=headers).json()
                 rmsg = resa['message']
                 if resa['status'] == 'success':
                    try:
                       rc = resa['data']['courseContent']
                       df = ""
                       for rc in rc:
                           ct = rc['contentType']
                           nm = str(rc['name']).replace("/","-").replace(":","-")
                           if ct == 1:
                              try:
                                 lnk2, ccid2 = str(rc['id']), str(rc['contentCourseId'])
                                 df += down.get_folder_content(tokk,ccid2,cid,lnk2)
                              except Exception as e:
                                 continue
                           else:
                              try:
                                 ln = str(rc['url'])
                                 nn = f"{nm}:{ln}\n"
                                 df += nn
                              except Exception as e:
                                 continue
                    except Exception as e:
                      continue
                 else:
                    await editable.edit(f"Error ❌\n**Reason : **`{rmsg}`")
                    return
                 try:
                    if len(df)>0:
                        with open(f"{filename}",'wt') as f:
                            f.write(df)
                        time.sleep(1)
                        caption = (
                              f"📌 Batch Details:\n"
                              f"┌───📚 Batch: {bname}\n"
                              f"└──────────────────────────\n\n"
                              f"📂 Batch Info:\n"
                              f"┌───📲 Application: CLass Plus\n"
                              f"└──────────────────────────\n\n"
                              f"📂 Content Overview:\n"
                              f"┌───🔗 Total Links: {videos + files}\n"
                              f"│    ├ 🎥 Videos: {videos} 📹\n"
                              f"│    └ 📄 PDFs: {files} ❌\n"
                              f"└──────────────────────────\n\n"
                              f"🔒 Security Notice:\n"
                              f"┌───🔹 All URLs are encrypted. 🔑\n"
                              f"│    🔹 Use our bot to upload. 🤖\n"
                              f"└──────────────────────────"
                           )

                        await bot.send_document(ct2,filename,caption=caption)
                        os.remove(filename)
                    else:
                        await bot.send_message(ct2,f"No Links Found ❌")
                        return
                 except Exception as e:
                    await bot.send_message(ct2,f"{e}")                     
              except Exception as e:
                await bot.send_message(ct2,e)
                continue                        
       except Exception as e:
          await bot.send_message(ct2,e)  
    except Exception as e:
       await bot.send_message(ct2,e)
    await editable.delete(True)
    await bot.send_message(ct2,f'**Done✅✅**')

