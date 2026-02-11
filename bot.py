import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

IMG_DOMAIN = "https://img.ophim.live/uploads/movies/"


########################################
# START / HELP
########################################

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "🎬 BOT XEM PHIM\n\n"

        "📖 Cách sử dụng:\n\n"

        "🔎 Tìm phim:\n"
        "/phim tên_phim\n"
        "Ví dụ:\n"
        "/phim naruto\n\n"

        "🔥 Xem phim hot:\n"
        "/topfilm\n\n"

        "💡 Sau khi chọn phim → bấm 'Xem tập'"
    )

    await update.message.reply_text(text)


########################################
# TÌM PHIM
########################################

async def phim(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "❌ Bạn chưa nhập tên phim\n\nVí dụ:\n/phim naruto"
        )
        return

    keyword = " ".join(context.args)

    url = f"https://ophim1.com/v1/api/tim-kiem?keyword={keyword}"

    res = requests.get(url)
    data = res.json()

    items = data["data"]["items"]

    if not items:
        await update.message.reply_text("❌ Không tìm thấy phim")
        return

    for item in items:

        slug = item["slug"]
        name = item["name"]

        poster = item.get("poster_url")

        image_url = IMG_DOMAIN + poster if poster else None

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🎬 Xem tập",
                    callback_data=f"M|{slug}"
                )
            ]
        ])

        if image_url:
            await update.message.reply_photo(
                photo=image_url,
                caption=f"🎬 {name}",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                f"🎬 {name}",
                reply_markup=keyboard
            )


########################################
# TOP FILM HOT
########################################

async def topfilm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = "https://ophim1.com/v1/api/home"

    res = requests.get(url)
    data = res.json()

    groups = data["data"]["items"]

    count = 0

    for group in groups:

        for item in group["items"]:

            if count >= 5:
                return

            slug = item["slug"]
            name = item["name"]

            poster = item.get("poster_url")

            image_url = IMG_DOMAIN + poster if poster else None

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🎬 Xem tập",
                        callback_data=f"M|{slug}"
                    )
                ]
            ])

            if image_url:
                await update.message.reply_photo(
                    photo=image_url,
                    caption=f"🔥 {name}",
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text(
                    f"🔥 {name}",
                    reply_markup=keyboard
                )

            count += 1


########################################
# BUTTON CLICK
########################################

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split("|")


    ########################################
    # CLICK PHIM → HIỆN TẬP
    ########################################

    if data[0] == "M":

        slug = data[1]

        url = f"https://ophim1.com/v1/api/phim/{slug}"

        res = requests.get(url)
        json_data = res.json()

        episodes = json_data["data"]["item"]["episodes"]

        keyboard = []

        for ep_group in episodes:

            for ep in ep_group["server_data"]:

                ep_name = ep["name"]

                keyboard.append([
                    InlineKeyboardButton(
                        f"▶ {ep_name}",
                        callback_data=f"E|{slug}|{ep_name}"
                    )
                ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            "📺 Chọn tập:",
            reply_markup=reply_markup
        )


    ########################################
    # CLICK TẬP → GỬI LINK
    ########################################

    elif data[0] == "E":

        slug = data[1]
        ep_name = data[2]

        url = f"https://ophim1.com/v1/api/phim/{slug}"

        res = requests.get(url)
        json_data = res.json()

        episodes = json_data["data"]["item"]["episodes"]

        for ep_group in episodes:

            for ep in ep_group["server_data"]:

                if ep["name"] == ep_name:

                    link = ep["link_m3u8"]

                    await query.message.reply_text(
                        f"🎬 {slug} - {ep_name}\n\n▶ {link}"
                    )

                    return


########################################
# MAIN
########################################

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("phim", phim))
    app.add_handler(CommandHandler("topfilm", topfilm))

    app.add_handler(CallbackQueryHandler(button))

    print("Bot đang chạy...")
    app.run_polling()


if __name__ == "__main__":
    main()
