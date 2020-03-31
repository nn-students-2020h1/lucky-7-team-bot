#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import logging
import json
import random
from timeit import default_timer as timer
import requests
import datetime
from imdb import IMDb
from setup import PROXY, TOKEN
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater, CallbackQueryHandler
from classes import Logs, CSVStats


date = datetime.date.today().strftime("%m-%d-%Y")
bot = Bot(
    token=TOKEN,
    base_url=PROXY,  # delete it if connection via VPN
)
# Enable logging
joke_id = ""
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
        logs = Logs("logs.json")
        logs.addLog(new_log)
        return function(*args, **kwargs)

    return wrapper


@add_log
def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    text = f"""
Hello, {update.effective_user.first_name}!
Nice to see you here!
If you need help, enter /help command.
"""
    update.message.reply_text(text=text)


@add_log
def chat_help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    text = """ 
    Supported commands:
/start - start bot 
/help - show supported commands
/history - show last five logs
/fact - get the most popular fact about cats 
/movie - get random movie from top-250 IMDb
/corona_stats - get top-5 infected countries 
/pokemon - get info and image of random pokemon
/joke - bot will make you laugh (probably)
"""
    update.message.reply_text(text)


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
    logs = Logs("logs.json")
    logslist = logs.getLastFiveLogs()
    for log in logslist:
        response = ""
        for key, value in log.items():
            response = response + f'{key}: {value}\n'
        update.message.reply_text(response)


def test(update: Update, context: CallbackContext):
    new_log = {
        "user": update.effective_user.first_name,
        "function": "anonym",
        "message": "test",
        "time": update.message.date.strftime("%d-%b-%Y (%H:%M:%S.%f)")
    }
    logs = Logs("logs.json")
    loglist = []
    for _ in range(100000):
        loglist.append(new_log)
    logs.addLogs(loglist)


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
    random_movie = top[random.randint(0, 249)]
    id = 'tt' + random_movie.movieID
    info = requests.get(f'http://www.omdbapi.com/?apikey=5a5643&i={id}')
    info = json.loads(info.text)
    # poster = requests.get(f'http://img.omdbapi.com/?apikey=5a5643&i={id}')
    text = f"""
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
def pokemon(update: Update, context: CallbackContext):
    num = random.randint(1, 807)
    pokemon_info = requests.get(f'https://pokeapi.co/api/v2/pokemon/{num}/')
    pokemon_info = json.loads(pokemon_info.text)
    text = f"""
Name: {pokemon_info['name'].capitalize()}
Height: {pokemon_info['height']}
Weight: {pokemon_info['weight']}
Type: {pokemon_info['types'][0]['type']['name']}
"""
    bot.send_message(chat_id=update.effective_chat['id'], text=text)
    bot.send_photo(chat_id=update.effective_chat['id'], photo=pokemon_info['sprites']['front_default'])


@add_log
def corona_stats(update: Update, context: CallbackContext):
    csvStat = CSVStats("todaystats.csv")
    if csvStat.status_code != 200:
        keyboard = [[InlineKeyboardButton("Да, покажи данные за предыдущий день", callback_data="True"),
                     InlineKeyboardButton("Нет, спасибо", callback_data="False")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if CSVStats.date == datetime.date.today().strftime("%m-%d-%Y"):
            bot.send_message(chat_id=update.effective_chat['id'],
                              text=f"Что-то пошло не так. Возможно, данные за {CSVStats.date} еще не появились. Хотите посмотреть данные за предыдущий день?",
                              reply_markup=reply_markup)
        else:
            bot.edit_message_text(chat_id=update.effective_message.chat_id,
                                   message_id=update.effective_message.message_id,
                                   text=f"Что-то пошло не так. Возможно, данные за {CSVStats.date} еще не появились. Хотите посмотреть данные за предыдущий день?",
                                   reply_markup=reply_markup)
    else:
        top_five = csvStat.getTopFiveProvinces()
        text = "Топ зараженных провинций:\n"
        for i in range(5):
            text += f'{i + 1}. {top_five[i]["province"]} - {top_five[i]["new infected"]} заражённых\n'
        bot.edit_message_text(chat_id=update.effective_message.chat_id, message_id=update.effective_message.message_id,
                               text=f"Статистика заражённых COVID-19 за {CSVStats.date}\n{text}")
        CSVStats.date = datetime.date.today().strftime("%m-%d-%Y")


@add_log
def joke(update: Update, context: CallbackContext):
    url = "https://joke3.p.rapidapi.com/v1/joke"
    headers = {
        'x-rapidapi-host': "joke3.p.rapidapi.com",
        'x-rapidapi-key': "837031bcd7msh57190d81a3d0374p19228ejsn5404ac1dd13a"
    }
    global joke_id
    response = json.loads(requests.request("GET", url, headers=headers).text)
    joke_id = response["id"]
    content = response["content"]
    likes = response["upvotes"]
    dislikes = response["downvotes"]
    keyboard = [[InlineKeyboardButton(f"Like ❤️ {likes}", callback_data="Like"),
                 InlineKeyboardButton(f"Dislike 💔 {dislikes}", callback_data="Dislike"),
                 InlineKeyboardButton("More jokes", callback_data="More jokes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=update.effective_chat['id'], text=content, reply_markup=reply_markup)


def button_corona(update, context):
    query = update.callback_query
    if query['data'] == 'False':
        global bot
        bot.send_message(chat_id=update.callback_query.message.chat['id'], text='Хорошо :)')
    else:
        global date
        CSVStats.date = (datetime.datetime.strptime(date, "%m-%d-%Y") - datetime.timedelta(days=1)).strftime(
            "%m-%d-%Y")
        corona_stats(update, context)


def button_joke(update, context):
    query = update.callback_query
    if query['data'] == 'Like' or query['data'] == "Dislike":
        global joke_id
        url = f"https://joke3.p.rapidapi.com/v1/joke/{joke_id}/upvote" if query['data'] == 'Like' else f"https://joke3.p.rapidapi.com/v1/joke/{joke_id}/downvote"
        payload = ""
        headers = {
            'x-rapidapi-host': "joke3.p.rapidapi.com",
            'x-rapidapi-key': "837031bcd7msh57190d81a3d0374p19228ejsn5404ac1dd13a",
            'content-type': "application/x-www-form-urlencoded"
        }
        response = requests.request("POST", url, data=payload, headers=headers)
        response = json.loads(response.text)
        content = response["content"]
        likes = response["upvotes"]
        dislikes = response["downvotes"]
        keyboard = [[InlineKeyboardButton(f"Like ❤️ {likes}", callback_data="Like"),
                     InlineKeyboardButton(f"Dislike 💔 {dislikes}", callback_data="Dislike"),
                     InlineKeyboardButton("More jokes", callback_data="More jokes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "You ❤️ it!" if query['data'] == 'Like' else "You 💔️ it!"
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text=text)
        bot.edit_message_text(message_id=update.callback_query.message.message_id, chat_id=update.callback_query.message.chat.id, text=content, reply_markup=reply_markup)
    elif query['data'] == 'More jokes':
        joke(update, context)


def main():
    updater = Updater(bot=bot, use_context=True)

    # on different commands - answer in Telegram
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', chat_help))
    updater.dispatcher.add_handler(CommandHandler('history', history))
    updater.dispatcher.add_handler(CommandHandler('test', test))
    updater.dispatcher.add_handler(CommandHandler('fact', fact))
    updater.dispatcher.add_handler(CommandHandler('corona_stats', corona_stats))
    updater.dispatcher.add_handler(CommandHandler('movie', movie))
    updater.dispatcher.add_handler(CommandHandler('joke', joke))
    updater.dispatcher.add_handler(CommandHandler('pokemon', pokemon))

    updater.dispatcher.add_handler(CallbackQueryHandler(button_corona, pattern='(True|False)'))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_joke, pattern='(Like|Dislike|More jokes)'))

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
