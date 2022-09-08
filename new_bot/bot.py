#!/usr/bin/env python3.10
from decimal import Decimal
from distutils.log import error
import json
import logging
import time
from typing import Dict, Tuple
import requests

from loguru import logger

from telegram import Update

from telegram.ext import CallbackContext, CommandHandler, Updater

import binance

from db import create_db, connect_db, History, Log

from logic import action_with_each_coin, action_with_each_coin2, get_klines_for_period, Buy, Sell

from schemas import Ratios, Settings, ValidationError

from settings import TOKEN, TEST


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


def buy_test():
    user_settings = read_settings("settings.json")

    # START WHILE
    logger.info("while True")
    try:
        while True:
            coin_name = "BTC"

            file_name = "state.json"
            if TEST:
                file_name = "state_test.json"
            with open(file_name, "r", encoding="utf8") as my_coins_data:
                my_state = json.loads(my_coins_data.read())

            list_klines = get_klines_for_period(coin_name, limit=60)

            my_buy = Buy(user_settings, coin_name, my_state, list_klines)

            my_buy.start()

            send = my_buy.need_send_message()

            if send:
                # job = context.job
                final_message = my_buy.get_message_text()
                # text = "\n".join(final_message)
                # context.bot.send_message(job.context, text=text)
                # logger.error(text)
                logger.error(final_message)

            logger.info("END Iteration")
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Stopped by user")


def sell_test():
    user_settings = read_settings("settings.json")

    # START WHILE
    logger.info("while True")
    try:
        while True:
            coin_name = "BTC"

            file_name = "state.json"
            if TEST:
                file_name = "state_test.json"
            with open(file_name, "r", encoding="utf8") as my_coins_data:
                my_state = json.loads(my_coins_data.read())

            list_klines = get_klines_for_period(coin_name, limit=60)

            my_sell = Sell(user_settings, coin_name, my_state, list_klines)

            my_sell.start()

            send = my_sell.need_send_message()

            if send:
                # job = context.job
                final_message = my_sell.get_message_text()
                # text = "\n".join(final_message)
                # context.bot.send_message(job.context, text=text)
                # logger.error(text)
                logger.error(final_message)

            logger.info("END Iteration")
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Stopped by user")


def error_processing(sleep_time: int, count: int, err, name) -> Tuple[int, int]:
    count += 1
    logger.info(f"Raise ERROR END Iteration {err}")
    data_base = connect_db()
    data_base.add(Log(error=err, error_type=name))
    data_base.commit()
    # time.sleep(60)
    sleep_time += count // 30
    time.sleep(sleep_time)
    return sleep_time, count


def all_test():
    user_settings = read_settings("settings.json")

    # START WHILE
    logger.info("Start while True")
    try:
        while True:
            count = 0
            sleep_time = 60
            try:
                logger.info("Start Iteration")

                file_name = "storage.json"
                if TEST:
                    file_name = "storage_test.json"
                with open(file_name, "r", encoding="utf8") as my_coins_data:
                    my_coins = json.loads(my_coins_data.read())

                file_name = "state.json"
                if TEST:
                    file_name = "state_test.json"
                with open(file_name, "r", encoding="utf8") as my_coins_data:
                    my_state = json.loads(my_coins_data.read())

                send, final_message = action_with_each_coin2(my_coins, user_settings, my_state)

                if send:
                    # job = context.job
                    # final_message = my_sell.get_message_text()
                    text = "\n".join(final_message)
                    # context.bot.send_message(job.context, text=text)
                    logger.error(text)
                    # logger.error(final_message)

                logger.info("END Iteration")
                time.sleep(60)
                if count:
                    count = 0
                    sleep_time = 60
            except binance.error.ServerError as err:
                sleep_time, count = error_processing(sleep_time, count, err, "ServerError")
                # count += 1
                # logger.info(f"Raise ERROR END Iteration {err}")
                # data_base = connect_db()
                # data_base.add(Log(error=err, error_type="ServerError"))
                # data_base.commit()
                # # time.sleep(60)
                # sleep_time += count // 30
                # time.sleep(sleep_time)
            except ConnectionError as err:
                sleep_time, count = error_processing(sleep_time, count, err, "ConnectionError")
                # count += 1
                # logger.info(f"Raise ERROR END Iteration {err}")
                # data_base = connect_db()
                # data_base.add(Log(error=err, error_type="ConnectionError"))
                # data_base.commit()
                # # time.sleep(60)
                # sleep_time += count // 30
                # time.sleep(sleep_time)
            except requests.exceptions.ConnectionError as err:
                sleep_time, count = error_processing(sleep_time, count, err, "ConnectionError Full desc")
                # count += 1
                # logger.info(f"Raise ERROR END Iteration {err}")
                # data_base = connect_db()
                # data_base.add(Log(error=err, error_type="ConnectionError"))
                # data_base.commit()
                # # time.sleep(60)
                # sleep_time += count // 30
                # time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("Stopped by user")


if __name__ == "__main__":
    create_db()
    all_test()


# def test_db():
#     create_db()
#     coin_name = "BTC"
#     amount = Decimal(0.002)
#     operation_type = "sell"
#     price = Decimal(21000.54)
#     data_base = connect_db()
#     # data_base.add(History(coin_name=coin_name, amount=amount, operation_type=operation_type, price=price))
#     # data_base.commit()
#     result = data_base.query(History).filter(History.coin_name == coin_name).order_by(History.time.desc()).first()
#     print(f"{result=}")


# if __name__ == "__main__":
#     test_db()


# if __name__ == "__main__":

#     user_settings = read_settings("settings.json")

#     # START WHILE
#     logger.info("while True")
#     try:
#         while True:
#             logger.info("Iteration")
#             file_name = "storage.json"
#             if TEST:
#                 file_name = "storage_test.json"
#             with open(file_name, "r", encoding="utf8") as my_coins_data:
#                 my_coins = json.loads(my_coins_data.read())

#             file_name = "state.json"
#             if TEST:
#                 file_name = "state_test.json"
#             with open(file_name, "r", encoding="utf8") as my_coins_data:
#                 my_state = json.loads(my_coins_data.read())

#             send, final_message = action_with_each_coin(my_coins, user_settings, my_state)

#             if send:
#                 # job = context.job
#                 text = "\n".join(final_message)
#                 # context.bot.send_message(job.context, text=text)
#                 logger.error(text)

#             logger.info("END Iteration")
#             time.sleep(60)
#     except KeyboardInterrupt:
#         logger.info("Stopped by user")
#     except Exception as err:
#         logger.error("FUCK!!!!!!!!!!!!!!!!!!!!!!!!!")
#         logger.error(f"{err}")
