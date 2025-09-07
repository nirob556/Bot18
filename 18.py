# pretty_verify_bot.py
# প্রয়োজন: pip install pyTelegramBotAPI
import telebot
from telebot import types
import sqlite3
import time
from datetime import datetime

# ========== CONFIG ==========
BOT_TOKEN = "8371666572:AAGvdLmzlEi-NEoFgSfJwli17VmQpked8-M"
CHANNELS = ["@vidoe66", "@vidoe55", "@vidoe88"]

LINK_LAYLA = "https://www.revenuecpmgate.com/i7pd0pg6?key=51e488e96a25bdded506db61a1e879c1"
LINK_OTHER = "https://www.revenuecpmgate.com/ecixkfkxp?key=e5afcf213bd677e460eaf971ad6f862a"
VIDEO_LINK_TEMPLATE = "https://www.revenuecpmgate.com/jxgvbk9x4?key=7a6c389891030baabd6368f0fcff5b3f"

OWNER_ID = 7224513731
DB_PATH = "verified_users.db"
# ========================================

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
        kb.add(types.InlineKeyboardButton(text=f"Join {ch}", url=f"https://t.me/{ch.lstrip('@')}"))
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

    # সবসময় সাথে সাথে callback answer দাও
    try:
        bot.answer_callback_query(call.id, text="⏳ যাচাই করা হচ্ছে...", show_alert=False)
    except Exception as e:
        print("answer_callback_query error:", e)

    not_member = []
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, chat_id)
            if member.status in ("left", "kicked"):
                not_member.append(ch)
        except Exception:
            not_member.append(ch)

    if not_member:
        text = "❌ এখনো জয়েন করনি:\n" + "\n".join(not_member)
        text += "\n\n👉 জয়েন করে আবার Verify চাপো।"
        try:
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text=text,
                                  reply_markup=channels_join_keyboard())
        except Exception as e:
            print("edit_message error:", e)
        return

    # সব ঠিক থাকলে
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception:
        pass

    photo_file_id = None
    try:
        photos = bot.get_user_profile_photos(user.id)
        if photos.total_count > 0:
            photo_file_id = photos.photos[0][-1].file_id
    except Exception:
        pass

    save_verified(user.id, getattr(user, "username", None),
                  getattr(user, "first_name", ""), getattr(user, "last_name", ""),
                  photo_file_id)

    kb = links_keyboard_for_user(user.id)
    bot.send_message(chat_id=user.id, text="✅ Verification successful! নিচে তোমার লিংকগুলো:", reply_markup=kb)


# /ck
@bot.message_handler(commands=['ck'])
def cmd_ck(m: types.Message):
    if not is_admin(m.from_user.id):
        bot.reply_to(m, "❌ অনুমতি নাই।")
        return
    rows = get_verified_all()
    if not rows:
        bot.reply_to(m, "কোনো ভেরিফায়েড ইউজার নাই।")
        return
    bot.reply_to(m, f"🔎 ভেরিফায়েড ইউজার সংখ্যা: {len(rows)}")
    for r in rows:
        user_id, username, first_name, last_name, photo_file_id, verified_at = r
        t = datetime.utcfromtimestamp(verified_at).strftime("%Y-%m-%d %H:%M:%S UTC")
        txt = (f"ID: <code>{user_id}</code>\n"
               f"নাম: {first_name} {last_name}\n"
               f"Username: @{username if username else '-'}\n"
               f"Verified at: {t}")
        try:
            if photo_file_id:
                bot.send_photo(m.chat.id, photo=photo_file_id, caption=txt)
            else:
                bot.send_message(m.chat.id, txt)
        except Exception as e:
            print("send user info error:", e)


# /admin
@bot.message_handler(commands=['admin'])
def cmd_admin(m: types.Message):
    if m.from_user.id != OWNER_ID:
        bot.reply_to(m, "শুধু OWNER ব্যবহার করতে পারবে।")
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


# /removeadmin
@bot.message_handler(commands=['removeadmin'])
def cmd_remove_admin(m: types.Message):
    if m.from_user.id != OWNER_ID:
        bot.reply_to(m, "শুধু OWNER ব্যবহার করতে পারবে।")
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
        bot.reply_to(m, "OWNER কে রিমুভ করা যাবে না।")
        return
    if not is_admin(rem_id):
        bot.reply_to(m, f"User <code>{rem_id}</code> admin নয়।")
        return
    remove_admin(rem_id)
    bot.reply_to(m, f"✅ User <code>{rem_id}</code> কে admin থেকে বাদ দেয়া হলো।")


# /listadmins
@bot.message_handler(commands=['listadmins'])
def cmd_list_admins(m: types.Message):
    admins = list_admins()
    if not admins:
        bot.reply_to(m, "কোনো admin নাই।")
        return
    text = "🔐 Admins:\n" + "\n".join([f"- <code>{a}</code>" for a in admins])
    bot.reply_to(m, text)


# /help
@bot.message_handler(commands=['help'])
def cmd_help(m: types.Message):
    help_text = (
        "/start — ভেরিফিকেশন শুরু\n"
        "/ck — ভেরিফায়েড লিস্ট (admin only)\n"
        "/listadmins — admin তালিকা\n"
        "/admin <user_id> — admin বানানো (OWNER only)\n"
        "/removeadmin <user_id> — admin রিমুভ (OWNER only)\n"
    )
    bot.reply_to(m, help_text)


# fallback
@bot.message_handler(func=lambda m: True)
def fallback(m: types.Message):
    pass


# ---------------- Main ----------------
if __name__ == "__main__":
    init_db()
    print("Bot is running...")
    while True:  # লুপে চালাই যাতে বট কখনো বন্ধ না হয়
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(3)
