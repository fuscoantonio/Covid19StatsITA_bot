'''
Created on 24 ott 2020
@author: Antonio Fusco
GitHub: https://github.com/fuscoantonio/
'''

import os
from flask import Flask, request
import telebot
from telebot import types
import requests

TOKEN = '' #set token
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
STATS = {'Nazionale': 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-andamento-nazionale-latest.json',
         'Regionale': 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-regioni-latest.json',
         'Provincia': 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province-latest.json'}
UPDATES = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-note.json'


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
    try:
        bot.send_message(message.chat.id, "Scegli il tipo di statistiche", reply_markup=main_stats_markup())
    except Exception as e:
        print(e)
        

def main_stats_markup():
    markup = types.InlineKeyboardMarkup()
    for i in STATS.keys():
        markup.add(types.InlineKeyboardButton(i, callback_data=i))
    return markup


def area_stats_markup(choice, generic_area):
    stats = get_stats(choice)
    ordered_list = []
    for i in stats:
        area = i[generic_area]
        if 'In fase' not in area and 'Fuori Regione' not in area:
            ordered_list.append(area)
    ordered_list = sorted(ordered_list)
    markup = add_inline_buttons(ordered_list, choice, 0)
    if choice == 'Regionale':
        return markup
    else:
        markup2 = add_inline_buttons(ordered_list, choice, 100)
        return [markup, markup2]


def add_inline_buttons(list, choice, start):
    markup = types.InlineKeyboardMarkup()
    counter = 0
    buttons = [1, 2]
    for index, area in enumerate(list[start:]):
        if index == 100:
            break
        data = area+ ' -'+ choice
        if counter < 2:
            buttons[counter] = types.InlineKeyboardButton(area, callback_data=data)
            counter += 1
        else:
            markup.add(buttons[0], buttons[1])
            buttons[0] = types.InlineKeyboardButton(area, callback_data=data)
            counter = 1
            if area == list[-1] and (len(list) % 2) != 0:
                markup.add(buttons[0])
    return markup
    
    
@bot.callback_query_handler(func=lambda call: call.data=='Nazionale')
def nation_stats(call):
    stats = get_stats(call.data)[0]
    stats = format_stats(stats, call.data)
    send_stats(call.message, stats)
            
            
@bot.callback_query_handler(func=lambda call: call.data=='Regionale' or call.data=='Provincia')
def select_area(call):
    if call.data == 'Regionale':
        msg = 'Scegli la regione'
        generic_area = 'denominazione_regione'
        bot.send_message(call.message.chat.id, msg,
                         reply_markup=area_stats_markup(call.data, generic_area))
    else:
        msg = 'Scegli la provincia'
        generic_area = 'denominazione_provincia'
        markups = area_stats_markup(call.data, generic_area)
        bot.send_message(call.message.chat.id, msg,
                     reply_markup=markups[0])
        bot.send_message(call.message.chat.id, '-',
                     reply_markup=markups[1])
    
    
@bot.callback_query_handler(func=lambda call: '-Regionale' in call.data or '-Provincia' in call.data)
def area_stats(call):
    choice = call.data[:call.data.index(' ')]
    option = 'Regionale' if '-Regionale' in call.data else 'Provincia'
    generic_area = 'denominazione_regione' if '-Regionale' in call.data else 'denominazione_provincia'
    stats = get_stats(option)
    stats = get_specific_stats(choice, stats, generic_area)
    stats = format_stats(stats, option)
    send_stats(call.message, stats)
    
    
def get_specific_stats(choice, stats, generic_area):
    for item in stats:
        if choice in item[generic_area]:
            return item


def send_stats(message, stats):
    try:
        bot.send_message(message.chat.id, stats)
    except Exception as e:
        print(e)
    

def get_stats(choice):
    for option in STATS.keys():
        if choice == option:
            try:
                resp = requests.get(STATS[option]).json()
                break;
            except Exception as e:
                print(e)
    return resp


def format_stats(stats, choice):
    formatted_stats = 'dati aggiornati al: ' + str(stats['data']) + '\n'
    for index, i in enumerate(stats):
        if index == 0:
            continue
        formatted_stats += i + ': ' + str(stats[i]) + '\n'
        
    return formatted_stats


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='' + TOKEN) #set webhook url
    return "!", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.polling()
    #webhook()
    #server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
