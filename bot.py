import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")


########################################

########################################

async def phim(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Dùng: /phim tên_phim")
        return

    keyword = " ".join(context.args)

    url = f"https://ophim1.com/v1/api/tim-kiem?keyword={keyword}"

    res = requests.get(url)
    data = res.json()

    items = data["data"]["items"]

    if not items:
        await update.message.reply_text("Không tìm thấy phim")
        return

    keyboard = []

    for item in items:

        slug = item["slug"]
        name = item["name"]

        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=f"M|{slug}"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Chọn phim:",
        reply_markup=reply_markup
    )


########################################
# xử lý click
########################################

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split("|")

    ########################################
    # click phim → hiện tập
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
                        ep_name,
                        callback_data=f"E|{slug}|{ep_name}"
                    )
                ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            "Chọn tập:",
            reply_markup=reply_markup
        )

    ########################################
    # click tập → gửi video link
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
                        f"{slug} - {ep_name}\n{link}"
                    )

                    return


########################################
# main
########################################

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("phim", phim))
app.add_handler(CallbackQueryHandler(button))

print("Bot đang chạy...")
app.run_polling()
