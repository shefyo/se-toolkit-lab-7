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
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

    config = load_config()
    token = config.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing in .env.bot.secret")

    async def handle_update(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message:
            return
        text = update.message.text or ""
        response = route_message(text)
        await update.message.reply_text(response)

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", handle_update))
    app.add_handler(CommandHandler("help", handle_update))
    app.add_handler(CommandHandler("health", handle_update))
    app.add_handler(CommandHandler("labs", handle_update))
    app.add_handler(CommandHandler("scores", handle_update))
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
