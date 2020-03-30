#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import logging
import json
import csv
import random
from timeit import default_timer as timer
import requests
import datetime
from imdb import IMDb
from setup import PROXY, TOKEN
from telegram import Bot, Update,InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater, CallbackQueryHandler

date = datetime.date.today().strftime("%m-%d-%Y")
bot = Bot(
        token=TOKEN,
        base_url=PROXY,  # delete it if connection via VPN
    )
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.


def average_time(function):
    def inner(update: Update, context: CallbackContext):
        t = timer()
        res = function(update, context)
        t = (timer() - t)
        update.message.reply_text(f'Время: {t} s!')
        return res
    return inner

# TODO: количество логов в истории
# TODO: вывод логов только одного юзера, а не всех
# TODO: вывод всех логов по ключу


def add_log(function):
    def wrapper(*args, **kwargs):
        message = 'button' if args[0].message is None else args[0].message.text
        new_log = {
            "user": args[0].effective_user.first_name,
            "function": function.__name__,
            "message": message,
            "time": args[0].effective_message.date.strftime("%d-%b-%Y (%H:%M:%S.%f)")
        }
        with open("logs.json", "a") as write_file:
            write_file.write(json.dumps(new_log)+"\n")
        return function(*args, **kwargs)
    return wrapper


@add_log
def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text(f'Привет, {update.effective_user.first_name}!')


@add_log
def chat_help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Введи команду /start для начала. ')


@add_log
def echo(update: Update, context: CallbackContext):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


@add_log
def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {context.error}')


def history(update: Update, context: CallbackContext):
    """Send a message when the command /logs is issued."""
    with open("logs.json", "r") as read_file:
        data = read_file.readlines()
        if len(data) > 5:
            data = data[-1:-6:-1]
        for elems in data:
            log = json.loads(elems)
            response = ""
            for key, value in log.items():
                response = response + f'{key}: {value}\n'
            update.message.reply_text(response)


def test(update: Update, context: CallbackContext):
    new_log = {
        "user": update.effective_user.first_name,
        "function": "anonym",
        "message": "test",
        "time": update.message.date.strftime("%d-%b-%Y (%H:%M:%S.%f)" )
    }
    with open("logs.json", "a") as write_file:
        for _ in range(100000):
            write_file.write(json.dumps(new_log) + "\n")


@add_log
def fact(update: Update, context: CallbackContext):
    maximum = 0
    upvoted_text = ''
    r = requests.get('https://cat-fact.herokuapp.com/facts')
    answer = json.loads(r.text)
    for i in answer['all']:
        if i['upvotes'] > maximum:
            maximum = i['upvotes']
            upvoted_text = i['text']
    update.message.reply_text(upvoted_text)


@add_log
def movie(update: Update, context: CallbackContext):
    ia = IMDb()
    top = ia.get_top250_movies()
    random_movie = top[random.randint(0,249)]
    id = 'tt' + random_movie.movieID
    info = requests.get(f'http://www.omdbapi.com/?apikey=5a5643&i={id}')
    info = json.loads(info.text)
    # poster = requests.get(f'http://img.omdbapi.com/?apikey=5a5643&i={id}')
    text =  f"""
    Title: {random_movie.data['title']}
Genre: {info["Genre"]}
Year: {random_movie.data['year']}
Director: {info["Director"]}
Runtime: {info["Runtime"]}
IMDb rating: {random_movie.data['rating']}
Top 250 rank: {random_movie.data['top 250 rank']}
Link: https://www.imdb.com/title/{id}/
    """
    update.message.reply_text(text=text, disable_web_page_preview=False)


@add_log
def coronastats(update: Update, context: CallbackContext):
    global date
    r = requests.get(f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{date}.csv')
    if r.status_code != 200:
        keyboard = [[InlineKeyboardButton("Да, покажи данные за предыдущий день", callback_data="True"),
                     InlineKeyboardButton("Нет, спасибо", callback_data="False")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if date == datetime.date.today().strftime("%m-%d-%Y"):
            bot.send_message(chat_id=update.effective_chat['id'], text=f"Что-то пошло не так. Возможно, данные за {date} еще не появились. Хотите посмотреть данные за предыдущий день?", reply_markup=reply_markup)
        else:
            bot.edit_message_text(chat_id=update.effective_message.chat_id, message_id=update.effective_message.message_id, text=f"Что-то пошло не так. Возможно, данные за {date} еще не появились. Хотите посмотреть данные за предыдущий день?", reply_markup=reply_markup)
    else:
        with open("todaystats.csv", "w") as f:
            f.write(r.text)
        with open("todaystats.csv", "r") as f:
            stats = csv.DictReader(f)
            top_five = []
            for row in stats:
                place = row["Province_State"] + " " + row["Country_Region"]
                new_infected = int(row["Confirmed"]) - int(row["Deaths"]) - int(row["Recovered"])
                if len(top_five) == 0:
                    top_five.append((place, new_infected))
                else:
                    for i in range(len(top_five)):
                        if top_five[i][1] <= new_infected:
                            top_five.insert(i, (place, new_infected))
                            break
            text = "Топ зараженных провинций:\n"
            for i in range(5):
                text += f'{i + 1}. {top_five[i][0]} - {top_five[i][1]} заражённых\n'
            bot.edit_message_text(chat_id=update.effective_message.chat_id, message_id=update.effective_message.message_id,  text=f"Статистика заражённых COVID-19 за {date}\n{text}")
            date = datetime.date.today().strftime("%m-%d-%Y")


def button(update, context):
    query = update.callback_query
    if query['data'] == 'False':
        global bot
        bot.send_message(chat_id=update.callback_query.message.chat['id'], text='Хорошо :)')
    else:
        global date
        date = (datetime.datetime.strptime(date, "%m-%d-%Y") - datetime.timedelta(days=1)).strftime("%m-%d-%Y")
        coronastats(update, context)

def main():

    updater = Updater(bot=bot, use_context=True)

    # on different commands - answer in Telegram
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', chat_help))
    updater.dispatcher.add_handler(CommandHandler('history', history))
    updater.dispatcher.add_handler(CommandHandler('test', test))
    updater.dispatcher.add_handler(CommandHandler('fact', fact))
    updater.dispatcher.add_handler(CommandHandler('coronastats', coronastats))
    updater.dispatcher.add_handler(CommandHandler('movie', movie))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
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