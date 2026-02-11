import os
import requests
from threading import Thread
from io import BytesIO

from flask import Flask
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes


TOKEN = os.getenv("BOT_TOKEN")

IMG_DOMAIN = "https://img.ophim.live/uploads/movies/"


########################################
# FIX IMAGE FUNCTION
########################################

def get_image(poster):

    if not poster:
        return None

    try:

        # nếu là link đầy đủ
        if poster.startswith("http"):
            url = poster
        else:
            url = IMG_DOMAIN + poster

        res = requests.get(url, timeout=10)

        if res.status_code == 200:
            return BytesIO(res.content)

    except Exception as e:
        print("Image error:", e)

    return None


########################################
# START
########################################

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        " BOT XEM PHIM\n\n"
        " Cách dùng:\n\n"
        "/phim tên_phim\n"
        "Ví dụ:\n"
        "/phim naruto\n\n"
        "/topfilm → xem phim hot"
    )

    await update.message.reply_text(text)


########################################
# SEARCH
########################################

async def phim(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "Ví dụ:\n/phim naruto"
        )
        return

    keyword = " ".join(context.args)

    url = f"https://ophim1.com/v1/api/tim-kiem?keyword={keyword}"

    data = requests.get(url).json()

    items = data["data"]["items"]

    if not items:
        await update.message.reply_text("Không tìm thấy")
        return

    for item in items:

        slug = item.get("slug")
        name = item.get("name")
        poster = item.get("poster_url")

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "Xem tập",
                callback_data=f"M|{slug}"
            )
        ]])

        img = get_image(poster)

        try:

            if img:

                await update.message.reply_photo(
                    photo=img,
                    caption=name,
                    reply_markup=keyboard
                )

            else:

                await update.message.reply_text(
                    name,
                    reply_markup=keyboard
                )

        except Exception as e:
            print("Send error:", e)


########################################
# TOP FILM
########################################

async def topfilm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = "https://ophim1.com/v1/api/home"

    data = requests.get(url).json()

    movies = data["data"]["items"]

    count = 0

    for item in movies:

        if count >= 10:
            break

        slug = item.get("slug")
        name = item.get("name")
        poster = item.get("poster_url")

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "Xem tập",
                callback_data=f"M|{slug}"
            )
        ]])

        img = get_image(poster)

        try:

            if img:

                await update.message.reply_photo(
                    photo=img,
                    caption=name,
                    reply_markup=keyboard
                )

            else:

                await update.message.reply_text(
                    name,
                    reply_markup=keyboard
                )

            count += 1

        except Exception as e:
            print("Topfilm error:", e)


########################################
# BUTTON
########################################

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split("|")


    if data[0] == "M":

        slug = data[1]

        url = f"https://ophim1.com/v1/api/phim/{slug}"

        json_data = requests.get(url).json()

        episodes = json_data["data"]["item"]["episodes"]

        keyboard = []

        for group in episodes:

            for ep in group["server_data"]:

                ep_name = ep["name"]

                keyboard.append([
                    InlineKeyboardButton(
                        ep_name,
                        callback_data=f"E|{slug}|{ep_name}"
                    )
                ])

        await query.message.reply_text(
            "Chọn tập:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    elif data[0] == "E":

        slug = data[1]
        ep_name = data[2]

        url = f"https://ophim1.com/v1/api/phim/{slug}"

        json_data = requests.get(url).json()

        episodes = json_data["data"]["item"]["episodes"]

        for group in episodes:

            for ep in group["server_data"]:

                if ep["name"] == ep_name:

                    link = ep["link_m3u8"]

                    await query.message.reply_text(
                        f"{slug} - {ep_name}\n\n{link}"
                    )

                    return


########################################
# WEB SERVER (RENDER FREE)
########################################

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot running"


def run_web():

    port = int(os.environ.get("PORT", 10000))

    web.run(
        host="0.0.0.0",
        port=port
    )


########################################
# RUN BOT
########################################


def run_bot():

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot = ApplicationBuilder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("help", start))
    bot.add_handler(CommandHandler("phim", phim))
    bot.add_handler(CommandHandler("topfilm", topfilm))

    bot.add_handler(CallbackQueryHandler(button))

    print("Bot running...")

    loop.run_until_complete(bot.initialize())
    loop.run_until_complete(bot.start())
    loop.run_until_complete(bot.updater.start_polling())

    loop.run_forever()


########################################
# MAIN
########################################

if __name__ == "__main__":

    Thread(target=run_bot).start()

    run_web()