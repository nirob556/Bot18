# pretty_verify_bot.py
# প্রয়োজন: pip install pyTelegramBotAPI
import telebot
from telebot import types
import sqlite3
import time
from datetime import datetime

# ========== CONFIG (এখানে নিজের ভ্যালু বসাও) ==========
BOT_TOKEN = "8371666572:AAGvdLmzlEi-NEoFgSfJwli17VmQpked8-M"
# চ্যানেল লিস্ট — public username হিসেবে @name বা numeric channel id ব্যবহার করো
CHANNELS = ["@vidoe66", "@vidoe55", "@vidoe88"]

# ভেরিফাই হলে ইউজারকে যে লিংকগুলো দেখাবে (নিজে বদলাবে)
LINK_LAYLA = "https://www.revenuecpmgate.com/i7pd0pg6?key=51e488e96a25bdded506db61a1e879c1"
LINK_OTHER = "https://www.revenuecpmgate.com/ecixkfkxp?key=e5afcf213bd677e460eaf971ad6f862a"
VIDEO_LINK_TEMPLATE = "https://www.revenuecpmgate.com/jxgvbk9x4?key=7a6c389891030baabd6368f0fcff5b3f"

# OWNER numeric telegram id (তুমি) — OWNER কে ডিফল্ট admin হিসেবে যোগ করা হবে
OWNER_ID = 7224513731

DB_PATH = "verified_users.db"
# ======================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


# ---------------- Database ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS verified (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            photo_file_id TEXT,
            verified_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    """)
    # OWNER কে admin বানাই (ignore যদি আগে থাকে)
    cur.execute("INSERT OR IGNORE INTO admins(user_id) VALUES(?)", (OWNER_ID,))
    conn.commit()
    conn.close()


def save_verified(user_id, username, first, last, photo_file_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO verified(user_id, username, first_name, last_name, photo_file_id, verified_at)
        VALUES(?,?,?,?,?,?)
    """, (user_id, username, first, last, photo_file_id, int(time.time())))
    conn.commit()
    conn.close()


def get_verified_all():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, first_name, last_name, photo_file_id, verified_at FROM verified")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_admin(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO admins(user_id) VALUES(?)", (user_id,))
    conn.commit()
    conn.close()


def remove_admin(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def list_admins():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def is_admin(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    r = cur.fetchone()
    conn.close()
    return bool(r)


# ---------------- Utilities ----------------
def channels_join_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        # URL button — ইউজারকে চ্যানেলে নিয়ে যাবে
        kb.add(types.InlineKeyboardButton(text=f"Join {ch}", url=f"https://t.me/{ch.lstrip('@')}"))
    # Verify button
    kb.add(types.InlineKeyboardButton(text="✅ Verify", callback_data="verify_join"))
    return kb


def links_keyboard_for_user(user_id):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text="লায়লার লিংক", url=LINK_LAYLA))
    kb.add(types.InlineKeyboardButton(text="ওথই লিংক", url=LINK_OTHER))
    kb.add(types.InlineKeyboardButton(text="ওল ভিডিও লিংক", url=VIDEO_LINK_TEMPLATE.format(user_id=user_id)))
    return kb


# ---------------- Handlers ----------------
@bot.message_handler(commands=['start'])
def cmd_start(m: types.Message):
    txt = ("🔥 টিকটকারদের🥵 ভাইরাল লিংক পেতে চাইলে প্রথমে নিচের ৩টা চ্যানেলে জয়েন করো মামা পুরো ফাটাফাটি লিংক🥵 সামনে বাচ্চাদের লিংক দিবো 😵‍💫এই বটেই ।\n\n"
           "তারপর ✅ Verify টিপো — না হলে লিংক পাবেন না🥳।")
    kb = channels_join_keyboard()
    bot.send_message(m.chat.id, txt, reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def callback_verify(call: types.CallbackQuery):
    user = call.from_user
    chat_id = user.id

    # চ্যানেলগুলোতে মেম্বারশিপ চেক
    not_member = []
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, chat_id)
            status = member.status
            if status in ("left", "kicked"):
                not_member.append(ch)
        except Exception as e:
            # bot may not have access to check private channel — treat as not member
            not_member.append(ch)

    if not_member:
        text = "তুমি এখনো নিচের চ্যানেল(গুলো)-এ নেই:\n" + "\n".join(not_member)
        text += "\n\nঅনুগ্রহ করে জয়েন করে আবার Verify চাপো।"
        # ছোট alert ও edit message করে ইউজারকে দেখাই
        bot.answer_callback_query(call.id, text="সব চ্যানেলে জয়েন করো", show_alert=True)
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=text, reply_markup=channels_join_keyboard())
        except Exception:
            pass
        return

    # সব চ্যানেলে যেই থাকলে ভেরিফাই সফল
    try:
        # পুরোনো মেসেজ ডিলিট (প্রাইভেট চ্যাটে সম্ভব না হলে ignore)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception:
        pass

    # প্রোফাইল ফটো সংগ্রহ
    photo_file_id = None
    try:
        photos = bot.get_user_profile_photos(user.id)
        if photos.total_count > 0:
            photo_file_id = photos.photos[0][-1].file_id
    except Exception:
        photo_file_id = None

    save_verified(user.id, getattr(user, "username", None), getattr(user, "first_name", ""), getattr(user, "last_name", ""), photo_file_id)

    kb = links_keyboard_for_user(user.id)
    bot.send_message(chat_id=user.id, text="✅ Verification successful! নিচে তোমার লিংকগুলো:", reply_markup=kb)


# /ck — admin only: ভেরিফায়েড লিস্ট দেখাবে
@bot.message_handler(commands=['ck'])
def cmd_ck(m: types.Message):
    uid = m.from_user.id
    if not is_admin(uid):
        bot.reply_to(m, "❌ তোমার অনুমতি নেই। (admin ছাড়া ব্যবহার করা যাবে না)")
        return

    rows = get_verified_all()
    if not rows:
        bot.reply_to(m, "কোনো ভেরিফায়েড ইউজার পাওয়া যায়নি।")
        return

    bot.reply_to(m, f"🔎 ভেরিফায়েড ইউজার সংখ্যা: {len(rows)} — এখন তালিকা পাঠাচ্ছি...")
    for r in rows:
        user_id, username, first_name, last_name, photo_file_id, verified_at = r
        t = datetime.utcfromtimestamp(verified_at).strftime("%Y-%m-%d %H:%M:%S (UTC)")
        txt = (f"ID: <code>{user_id}</code>\n"
               f"নাম: {first_name} {last_name}\n"
               f"Username: @{username if username else '-'}\n"
               f"Verified at: {t}")
        try:
            if photo_file_id:
                bot.send_photo(m.chat.id, photo=photo_file_id, caption=txt)
            else:
                bot.send_message(m.chat.id, txt)
        except Exception:
            bot.send_message(m.chat.id, txt)


# /admin <user_id> — OWNER only: নতুন admin যোগ
@bot.message_handler(commands=['admin'])
def cmd_admin(m: types.Message):
    if m.from_user.id != OWNER_ID:
        bot.reply_to(m, "এই কমান্ডটি শুধুমাত্র OWNER ব্যবহার করতে পারবে।")
        return

    parts = m.text.strip().split()
    if len(parts) != 2:
        bot.reply_to(m, "ব্যবহার: /admin <user_id>")
        return

    try:
        new_admin_id = int(parts[1])
    except ValueError:
        bot.reply_to(m, "সঠিক numeric user_id পাঠাও।")
        return

    add_admin(new_admin_id)
    bot.reply_to(m, f"✅ User <code>{new_admin_id}</code> কে admin বানানো হলো।")


# /removeadmin <user_id> — OWNER only: admin রিমুভ
@bot.message_handler(commands=['removeadmin'])
def cmd_remove_admin(m: types.Message):
    if m.from_user.id != OWNER_ID:
        bot.reply_to(m, "এই কমান্ডটি শুধুমাত্র OWNER ব্যবহার করতে পারবে।")
        return

    parts = m.text.strip().split()
    if len(parts) != 2:
        bot.reply_to(m, "ব্যবহার: /removeadmin <user_id>")
        return

    try:
        rem_id = int(parts[1])
    except ValueError:
        bot.reply_to(m, "সঠিক numeric user_id পাঠাও।")
        return

    if rem_id == OWNER_ID:
        bot.reply_to(m, "OWNER নিজেকে রিমুভ করতে পারবে না।")
        return

    if not is_admin(rem_id):
        bot.reply_to(m, f"User <code>{rem_id}</code> এখনো admin নয়।", parse_mode="HTML")
        return

    remove_admin(rem_id)
    bot.reply_to(m, f"✅ User <code>{rem_id}</code> কে admin তালিকা থেকে বাদ দেয়া হলো।", parse_mode="HTML")


# /listadmins — অ্যাডমিন তালিকা দেখাবে
@bot.message_handler(commands=['listadmins'])
def cmd_list_admins(m: types.Message):
    admins = list_admins()
    if not admins:
        bot.reply_to(m, "কোনো admin নাই।")
        return
    text = "🔐 Admins:\n" + "\n".join([f"- <code>{a}</code>" for a in admins])
    bot.reply_to(m, text, parse_mode="HTML")


# /help
@bot.message_handler(commands=['help'])
def cmd_help(m: types.Message):
    help_text = (
        "/start — ভেরিফিকেশন শুরু\n"
        "/ck — ভেরিফায়েড তালিকা (admin only)\n"
        "/listadmins — admin তালিকা\n"
        "/admin <user_id> — OWNER দ্বারা admin বানানো\n"
        "/removeadmin <user_id> — OWNER দ্বারা admin রিমুভ করা\n"
    )
    bot.reply_to(m, help_text)


# Catch-all for safety
@bot.message_handler(func=lambda m: True)
def fallback(m: types.Message):
    # খুব প্রয়োজন হলে কাস্টম রেসপন্স দিতো, এখানে নিট্রাল রেখেছি
    pass


# ---------------- Main ----------------
if __name__ == "__main__":
    init_db()
    print("Bot is running...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout = 60)
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        print("Bot crashed:", e)