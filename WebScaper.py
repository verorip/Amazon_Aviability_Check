import requests
import re
from auth_token import token
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
from sys import  platform
import functools

if 'win' in platform:
     from auth_token import token
else:
    token = os.environ['TOKEN']

time=20

h = {
        'authority': 'www.amazon.it',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-GB,it-IT;q=0.9,it;q=0.8',
    }



def add_to_dict(line):
    line = line.split('http')
    urls[line[0]]='http'+line[1]

urls=dict()

with open('urls.txt') as fp:
     content = fp.readlines()
     for line in content:
         add_to_dict(line)


active_chat_id=[]


def callback_patrol(context: telegram.ext.CallbackContext):
    for key in urls:
        page=requests.get(urls[key], headers=h)
        if re.search('value="Aggiungi al carrello"', page.text):
            context.bot.send_message(chat_id=context.job.context, text=key+' founded!')
        else:
            context.bot.send_message(chat_id=context.job.context, text=key+'  nope!')

def extract_number(text):
     return text.split()[1].strip()

def start_watching(update: telegram.Update, context: telegram.ext.CallbackContext):
    print("starting!")
    if not update.message.chat_id in active_chat_id:
        active_chat_id.append(update.message.chat_id)
        context.bot.send_message(chat_id=update.message.chat_id,
                          text='Start watching. Update every: ' + str(int(time/60)) + ' mins')
        context.job_queue.run_repeating(callback_patrol, time, context=update.message.chat_id)
    else:
        context.bot.send_message(chat_id=update.message.chat_id,
                          text='Already watching for you')
def stop_watching(update: telegram.Update, context: telegram.ext.CallbackContext):
    print('stopping')
    active_chat_id.remove(update.message.chat_id)
    context.bot.send_message(chat_id=update.message.chat_id,
                      text='Stopped!')
    context.job_queue.stop()

def help(update: telegram.Update, context: telegram.ext.CallbackContext):
    print('help')
    context.bot.send_message(chat_id=update.message.chat_id,
                      text='use /start to start check viability\n/stop to stop check the aviability\n/time [int] to set how many seconds you want bot check')

def set_time(update: telegram.Update, context: telegram.ext.CallbackContext):
    print('time')

    try:
        val = int(extract_number(update.message.text))
        print(val)
    except Exception as error:
        context.bot.send_message(chat_id=update.message.chat_id,
                          text='formato non corretto, inserire numeri senza virgola (secondi)')
        print(error)
        return
    time = val
    context.bot.send_message(chat_id=update.message.chat_id,
                      text='tempo settato a ' + str(val))


def insert_watch(update: telegram.Update, context: telegram.ext.CallbackContext):
    print('insert ', update.message.text.split())
    if 'http' in update.message.text.split()[-1] and len(update.message.text.split())>=2:
        key = functools.reduce(lambda a,b: a+b, update.message.text.split()[1:-1])
        value = update.message.text.split()[-1]
        urls[key]=value
        context.bot.send_message(chat_id=update.message.chat_id,
                          text='aggiunto {0} con link {1} alla ricerca\n'.format(key, value), disable_web_page_preview=True)
    else:
        context.bot.send_message(chat_id=update.message.chat_id,
                          text='No link inside message or wrong format. Insert name and link separated from whitespaces')




if __name__=='__main__':
    updater = Updater(token)
    updater.dispatcher.add_handler(CommandHandler('start', start_watching, pass_job_queue=True))
    updater.dispatcher.add_handler(CommandHandler('stop', stop_watching, pass_job_queue=True))
    updater.dispatcher.add_handler(CommandHandler('time', set_time))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('update', insert_watch))
    updater.start_polling()
    print('bot running')
