#!/usr/bin/env python3.10
import json
import logging
import time
from typing import Dict

from loguru import logger

from telegram import Update

from telegram.ext import CallbackContext, CommandHandler, Updater

from logic import action_with_each_coin

from schemas import Ratios, Settings, ValidationError

from settings import TOKEN


# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# logger = logging.getLogger(__name__)

logger.add(
    "bot.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="1 week",
    compression="zip",
)


def start(update: Update) -> None:
    """Sends explanation on how to use the bot."""
    update.message.reply_text("Hi! Use /set <seconds> to set a timer")


def read_settings(name_file: str) -> Dict[str, float]:
    """
    Read settings file

    :param name_file: file name, defaults to "settings.json"
    :type name_file: str
    :raises TypeError: does not match the schema
    :raises TypeError: does not match the schema
    :return: dictionary with ratios
    :rtype: dict[str, float]
    """
    with open(name_file, "r", encoding="utf8") as settings_file:
        # settings_data = json.loads(settings_file.read())
        try:
            settings_data = Settings.parse_raw(settings_file.read())
            # print(settings_data.dict())
        except ValidationError as e:
            raise TypeError(f"'{name_file}' does not match the schema {e.json()}")

    settings_dict = {
        "up_to_ratio": 1 + settings_data.raise_up_to / 100,
        "down_to_ratio": 1 - settings_data.down_to / 100,
        "stop_loss_ratio": 1 - settings_data.stop_loss / 100,
        "min_price_ratio": 1 + settings_data.stop_loss / 100,
    }
    try:
        Ratios(**settings_dict)
    except ValidationError as e:
        raise TypeError(f"'settings_dict' does not match the schema {e.json()}")

    return settings_dict


def start_trade(context: CallbackContext) -> None:
    """Start while

    :param context: default value
    :type context: CallbackContext
    """
    user_settings = read_settings("settings.json")

    with open("storage.json", "r", encoding="utf8") as my_coins_data:
        my_coins = json.loads(my_coins_data.read())

    send, final_message = action_with_each_coin(my_coins, user_settings)

    if send:
        job = context.job
        text = "\n".join(final_message)
        context.bot.send_message(job.context, text=text)
        logger.error(text)


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def change(update: Update, context: CallbackContext) -> None:
    try:
        # args[0] should contain the time for the timer in secondsargs[0]
        data = context.args[0].split(",")
        key = data[0]
        value = data[1]

        with open("settings.json", "r+", encoding="utf8") as settings_file:
            settings_data = json.loads(settings_file.read())

            settings_data[key] = value

            settings_file.seek(0)
            settings_file.write(json.dumps(settings_data, sort_keys=True, indent=2))
            settings_file.truncate()

        text = "Change successfully set!"

        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text("Usage: /change raise,5")


def set_timer(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = int(context.args[0])
        if due < 0:
            update.message.reply_text("Sorry we can not go back to future!")
            return

        context.job_queue.run_repeating(start_trade, due, context=chat_id, name=str(chat_id))

        text = "Timer successfully set!"
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text("Usage: /set <seconds>")


def unset(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    update.message.reply_text(text)


def main() -> None:
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", start))
    dispatcher.add_handler(CommandHandler("set", set_timer))
    dispatcher.add_handler(CommandHandler("change", change))
    dispatcher.add_handler(CommandHandler("unset", unset))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":

    user_settings = read_settings("settings.json")

    # START WHILE
    logger.info("while True")
    try:
        while True:
            logger.info("Iteration")
            with open("storage.json", "r", encoding="utf8") as my_coins_data:
                my_coins = json.loads(my_coins_data.read())

            with open("state.json", "r", encoding="utf8") as my_coins_data:
                my_state = json.loads(my_coins_data.read())

            send, final_message = action_with_each_coin(my_coins, user_settings, my_state)

            if send:
                # job = context.job
                text = "\n".join(final_message)
                # context.bot.send_message(job.context, text=text)
                logger.error(text)

            logger.info("END Iteration")
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Stopped by user")
