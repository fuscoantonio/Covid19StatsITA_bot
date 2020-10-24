'''
Created on 24 ott 2020

@author: some idiot
'''

import os
from flask import Flask, request
import telebot
from telebot import types
import requests
from telebot.types import ReplyKeyboardRemove

TOKEN = '' #set token
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
dev_id = '' #set dev_id
STATS = {'Nazionale': 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-andamento-nazionale-latest.json',
         'Regionale': 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-regioni-latest.json',
         'Provincia': 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province-latest.json'}
UPDATES = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-note.json'
is_covidstats_active = False
is_area_active = False
current_stats = None
areas = None
current_area = None
current_choice = None


@bot.message_handler(commands=['updates'])
def covid_updates(message):
    try:
        resp = requests.get(UPDATES).json()
        msg = 'data: ' + resp[-1]['data'] + '\n' + resp[-1]['note']
        bot.send_message(message.chat.id, msg)
    except Exception as e:
        print(e)
    
@bot.message_handler(commands=['covid_stats'])
def covid_stats(message):
    global is_covidstats_active
    try:
        bot.send_message(message.chat.id, "Scegli il tipo di statistiche", reply_markup=main_stats_markup())
        is_covidstats_active = True
    except Exception as e:
        print(e)
        

def main_stats_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    options = STATS.keys()
    for i in options:
        markup.add(types.KeyboardButton(i))
    return markup


def area_stats_markup(choice):
    global areas, current_area, current_stats
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    current_stats = get_stats(choice)
    if choice == 'Regionale':
        current_area = 'denominazione_regione'
    else:
        current_area = 'denominazione_provincia'
    areas = []
    for i in range(len(current_stats)):
        areas.append(current_stats[i][current_area])
        markup.add(types.KeyboardButton(current_stats[i][current_area]))
    return markup
    

@bot.message_handler(func=lambda message: is_covidstats_active)
def select_stats(message):
    global is_covidstats_active, is_area_active, current_choice
    if message.text in STATS.keys():
        current_choice = message.text
        if message.text == 'Regionale':
            bot.send_message(message.chat.id, 'Scegli una regione', reply_markup=area_stats_markup(message.text))
            is_area_active = True
        elif message.text == 'Provincia':
            bot.send_message(message.chat.id, 'Scegli una provincia', reply_markup=area_stats_markup(message.text))
            is_area_active = True
        else:
            stats = get_stats(message.text)[0]
            stats = format_stats(stats)
            send_stats(message, stats)
    else:
        try:
            bot.send_message(message.chat.id, 'Comando non riconosciuto', reply_markup=ReplyKeyboardRemove())
        except Exception as e:
            print(e)
    is_covidstats_active = False
            
            
@bot.message_handler(func=lambda message: is_area_active)
def select_area(message):
    global areas, current_area, current_stats
    if message.text in areas:
        for i, item in enumerate(current_stats):
            if message.text == item[current_area]:
                stats = current_stats[i]
                break
        stats = format_stats(stats)
        send_stats(message, stats)
    else:
        try:
            bot.send_message(message.chat.id, 'Comando non riconosciuto', reply_markup=ReplyKeyboardRemove())
        except Exception as e:
            print(e)
    is_area_active = False
    
    
def send_stats(message, stats):
    try:
        bot.send_message(message.chat.id, stats, reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        print(e)
    

def get_stats(choice):
    global current_stats
    for option in STATS.keys():
        if choice == option:
            try:
                resp = requests.get(STATS[option]).json()
                break;
            except Exception as e:
                print(e)
    return resp


def format_stats(stats):
    global current_choice
    formatted_stats = 'dati aggiornati al: ' +str(stats['data']) + '\ntotale_casi: ' + str(stats['totale_casi']) + '\n'
    if current_choice == 'Nazionale' or current_choice == 'Regionale':
        counter = 0
        for i in stats:
            if counter > 5:
                if i == 'totale_casi':
                    continue
                formatted_stats += i + ': ' + str(stats[i]) + '\n'
            else:
                counter += 1
        
    return formatted_stats
        

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://covidstats-bot.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    #bot.remove_webhook()
    #bot.polling()
    webhook()
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
