from __future__ import annotations

import argparse
import asyncio

from config import load_config
from handlers import route_message


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=str, help='Run in offline test mode, e.g. --test "/start"')
    return parser.parse_args()


async def telegram_main() -> None:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import (
        Application,
        CallbackQueryHandler,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )

    config = load_config()
    token = config.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing in .env.bot.secret")

    def main_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Health", callback_data="/health")],
            [InlineKeyboardButton("Labs", callback_data="/labs")],
            [InlineKeyboardButton("Scores: Lab 04", callback_data="/scores lab-04")],
            [InlineKeyboardButton("Top students", callback_data="who are the top 5 students in lab 4")],
            [InlineKeyboardButton("Lowest pass rate", callback_data="which lab has the lowest pass rate")],
        ])

    async def handle_update(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message:
            return

        text = update.message.text or ""
        response = route_message(text)

        if text == "/start":
            await update.message.reply_text(response, reply_markup=main_keyboard())
        else:
            await update.message.reply_text(response)

    async def handle_button(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return

        await query.answer()
        text = query.data or ""
        response = route_message(text)
        await query.message.reply_text(response)

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", handle_update))
    app.add_handler(CommandHandler("help", handle_update))
    app.add_handler(CommandHandler("health", handle_update))
    app.add_handler(CommandHandler("labs", handle_update))
    app.add_handler(CommandHandler("scores", handle_update))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_update))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


def main() -> int:
    args = parse_args()
    load_config()

    if args.test is not None:
        print(route_message(args.test))
        return 0

    asyncio.run(telegram_main())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
