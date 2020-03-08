#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import logging
import json
from datetime import datetime

from setup import PROXY, TOKEN
from telegram import Bot, Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.


def addlogging(function):
    def wrapper(*args, **kwargs):
        new_log = {
            "user": args[0].effective_user.first_name,
            "function": function.__name__,
            "message": args[0].message.text,
            "time": args[0].message.date.strftime("%d-%b-%Y (%H:%M:%S.%f)")
        }
        id = datetime.today().timestamp()  # у каждого лога свой +- уникальный  id
        log_to_update = {}  # без костыля не кошерно. log_to_update нужен для обновления logs.json
        try:
            with open("logs.json", "r") as f:
                # по каким-то причинам не позволяет записывать в файл и одновременно читать из него
                # пытаюсь сделать через "а" - перебрасывает в excepti. как убрать свистопляски с лишним костылем и избравиться от блока finally?
                file_content = f.read()
                log_to_update = json.loads(file_content)
                log_to_update[id] = new_log
        except:  # если logs.json пустой
            log_to_update = {id: new_log}
        finally:
            with open("logs.json", "w") as write_file:
                json.dump(log_to_update, write_file)
        return function(*args, **kwargs)
    return wrapper


@addlogging
def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text(f'Привет, {update.effective_user.first_name}!')


@addlogging
def chat_help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Введи команду /start для начала. ')


@addlogging
def echo(update: Update, context: CallbackContext):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


@addlogging
def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {context.error}')


def history(update: Update, context: CallbackContext):
    """Send a message when the command /logs is issued."""
    with open("logs.json", "r") as read_file:
        data = list(json.load(read_file).values())
        if len(data) > 5:
            data = data[-1:-6:-1]
        for log in data:
            response = ""
            for key, value in log.items():
                response = response + f'{key}: {value}\n'
            update.message.reply_text(response)



def main():
    bot = Bot(
        token=TOKEN,
        base_url=PROXY,  # delete it if connection via VPN
    )
    updater = Updater(bot=bot, use_context=True)

    # on different commands - answer in Telegram
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', chat_help))
    updater.dispatcher.add_handler(CommandHandler('history', history))

    # on noncommand i.e message - echo the message on Telegram
    updater.dispatcher.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    logger.info('Start Bot')
    LOGS = []
    main()
