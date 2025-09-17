import requests
import asyncio
import time
import json
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

BOT_TOKEN = "7470984428:AAH7UDG2Xj7UPvhUNNEJCv6X-RddfeKzVEg"
API_URL = "https://aditya-ff-like-api.vercel.app/like"
REGION = "ind"
DATA_FILE = "uids.json"

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@dp.message_handler(commands=["start"])
async def start_cmd(msg: types.Message):
    data = load_data()
    if str(msg.chat.id) not in data:
        data[str(msg.chat.id)] = []
        save_data(data)
    await msg.answer(
        "👋 <b>Welcome!</b>\n\n"
        "➕ <code>/adduid &lt;uid&gt;</code> - Add UID\n"
        "📋 <code>/myuids</code> - Show UIDs\n"
        "🗑 <code>/deluid &lt;uid&gt;</code> - Delete one UID\n"
        "🔥 <code>/clearuids</code> - Remove all UIDs"
    )

@dp.message_handler(commands=["adduid"])
async def add_uid(msg: types.Message):
    uid = msg.get_args().strip()
    if not uid.isdigit():
        return await msg.reply("⚠️ Enter valid numeric UID.\nExample: `/adduid 1942776004`", parse_mode="Markdown")
    data = load_data()
    user_uids = data.get(str(msg.chat.id), [])
    if uid not in user_uids:
        user_uids.append(uid)
        data[str(msg.chat.id)] = user_uids
        save_data(data)
        await msg.answer(f"✅ UID <b>{uid}</b> added successfully!")
    else:
        await msg.answer(f"ℹ️ UID <b>{uid}</b> already exists.")

@dp.message_handler(commands=["myuids"])
async def my_uids(msg: types.Message):
    data = load_data()
    uids = data.get(str(msg.chat.id), [])
    if not uids:
        return await msg.answer("❌ You have not added any UID yet.\nUse `/adduid <uid>` to add one.")
    await msg.answer("📌 <b>Your UIDs:</b>\n\n" + "\n".join([f"➡️ {u}" for u in uids]))

@dp.message_handler(commands=["deluid"])
async def del_uid(msg: types.Message):
    uid = msg.get_args().strip()
    data = load_data()
    uids = data.get(str(msg.chat.id), [])
    if uid in uids:
        uids.remove(uid)
        data[str(msg.chat.id)] = uids
        save_data(data)
        await msg.answer(f"🗑 UID <b>{uid}</b> removed successfully.")
    else:
        await msg.answer("⚠️ UID not found in your list.")

@dp.message_handler(commands=["clearuids"])
async def clear_uids(msg: types.Message):
    data = load_data()
    data[str(msg.chat.id)] = []
    save_data(data)
    await msg.answer("🔥 All your UIDs have been cleared.")

async def run_uids_between():
    start_time = datetime.now().replace(hour=6, minute=30, second=0, microsecond=0)
    end_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    if datetime.now() > end_time:
        return
    data = load_data()
    all_tasks = []
    for chat_id, uids in data.items():
        for uid in uids:
            all_tasks.append((chat_id, uid))
    if not all_tasks:
        return
    total_seconds = (end_time - start_time).seconds
    delay_per_task = total_seconds / len(all_tasks)
    print(f"Total tasks: {len(all_tasks)}, Delay per task: {delay_per_task:.2f} sec")
    for i, (chat_id, uid) in enumerate(all_tasks):
        await process_uid(chat_id, uid)
        if i < len(all_tasks) - 1:
            await asyncio.sleep(delay_per_task)

async def process_uid(chat_id, uid):
    try:
        response = requests.get(f"{API_URL}?uid={uid}&server_name={REGION}")
        res_json = response.json()
        print(f"UID {uid} => {res_json}")
        if res_json.get("status") == 1:
            message = (
                f"🎉 <b>Auto Likes Success</b>\n\n"
                f"✅ UID: <code>{uid}</code>\n\n"
                f"<b>Response JSON:</b>\n<code>{res_json}</code>"
            )
        else:
            message = (
                f"⚠️ Auto Likes Failed for UID: <code>{uid}</code>\n\n"
                f"<b>Response JSON:</b>\n<code>{res_json}</code>"
            )
        await bot.send_message(int(chat_id), message)
    except Exception as e:
        print(f"Error for UID {uid}: {e}")

async def scheduler_loop():
    while True:
        now = datetime.now().strftime("%H:%M")
        if now == "06:30":
            await run_uids_between()
        await asyncio.sleep(60)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler_loop())
    executor.start_polling(dp, skip_updates=True)
