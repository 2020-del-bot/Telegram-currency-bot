import telebot
import requests
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = 'uid'
bot = telebot.TeleBot(BOT_TOKEN)
PHOTOS_PATH = 'photos'


def get_all_rates():
    """Возвращает словарь с курсами всех валют к рублю"""
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    response = requests.get(url, timeout=10)
    data = response.json()
    return data['Valute']


def menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('🇺🇸 Доллар (USD)', callback_data='usd'),
        InlineKeyboardButton('🇪🇺 Евро (EUR)', callback_data='eur'),
        InlineKeyboardButton('🇬🇧 Фунт (GBP)', callback_data='gbp'),
        InlineKeyboardButton('🇨🇳 Юань (CNY)', callback_data='cny'),
        InlineKeyboardButton('🇯🇵 Йена (JPY)', callback_data='jpy'),
        InlineKeyboardButton('🇨🇭 Франк (CHF)', callback_data='chf'),
        InlineKeyboardButton('🇨🇦 Доллар (CAD)', callback_data='cad'),
        InlineKeyboardButton('🇦🇺 Доллар (AUD)', callback_data='aud'),
        InlineKeyboardButton('🇰🇿 Тенге (KZT)', callback_data='kzt'),
        InlineKeyboardButton('🇧🇾 Рубль (BYN)', callback_data='byn')
    )
    return keyboard


def reply_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton('/help'),
        KeyboardButton('/perevod')
    )
    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    welcome_photo = os.path.join(PHOTOS_PATH, 'welcome.jpg')
    text = "Привет! Я валютный помощник\n\nАктуальные курсы 10 валют к рублю\nКаждая валюта сопровождается фото\n\nВыбери валюту из меню:"

    if os.path.exists(welcome_photo):
        with open(welcome_photo, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=text, reply_markup=reply_keyboard())
    else:
        bot.send_message(message.chat.id, text, reply_markup=reply_keyboard())
    
    # Отправляем инлайн-меню с валютами
    bot.send_message(message.chat.id, "👇 Выбери валюту:", reply_markup=menu())


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "📚 **Справка по использованию бота:**\n\n"
        "/start - запустить бота и показать меню\n"
        "/help - показать эту справку\n"
        "/perevod - конвертировать валюту\n"
        "Примеры:\n"
        "/perevod 100 USD - в рубли\n"
        "/perevod 100 USD EUR - из долларов в евро\n\n"
        "💰 **Как узнать курс:**\n"
        "Просто нажми на кнопку с нужной валютой в меню!\n\n"
        "📋 **Доступные валюты:**\n"
        "USD, EUR, GBP, CNY, JPY, CHF, CAD, AUD, KZT, BYN, RUB\n\n"
        "📊 **Источник данных:** Центральный Банк РФ"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown', reply_markup=reply_keyboard())
    bot.send_message(message.chat.id, "👇 Выбери валюту:", reply_markup=menu())


@bot.message_handler(commands=['perevod'])
def convert_command(message):
    parts = message.text.split()
    if len(parts) == 1:
        bot.send_message(message.chat.id,
                         "Введи:\n/perevod 100 USD - конвертация в рубли\n/perevod 100 USD EUR - из любой в любую",
                         reply_markup=reply_keyboard())
        return

    try:
        amount = float(parts[1])
        
        if len(parts) == 3:
            currency = parts[2].upper()
            perevod_v_rub(message.chat.id, amount, currency)
        elif len(parts) == 4:
            from_currency = parts[2].upper()
            to_currency = parts[3].upper()
            convert_any_to_any(message.chat.id, amount, from_currency, to_currency)
        else:
            bot.send_message(message.chat.id,
                             "Неверный формат!\nПримеры:\n/perevod 100 USD\n/perevod 100 USD EUR",
                             reply_markup=reply_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Сумма должна быть числом", reply_markup=reply_keyboard())


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.startswith('/'):
        return

    parts = message.text.split()
    if len(parts) == 2:
        try:
            amount = float(parts[0])
            currency = parts[1].upper()
            perevod_v_rub(message.chat.id, amount, currency)
        except ValueError:
            bot.send_message(message.chat.id,
                             "Неверный формат!\nВведи: сумму и код валюты через пробел\nНапример: 100 USD",
                             reply_markup=reply_keyboard())
    elif len(parts) == 3:
        try:
            amount = float(parts[0])
            from_currency = parts[1].upper()
            to_currency = parts[2].upper()
            convert_any_to_any(message.chat.id, amount, from_currency, to_currency)
        except ValueError:
            bot.send_message(message.chat.id,
                             "Неверный формат!\nВведи: сумма из_валюты в_валюту\nНапример: 100 USD EUR",
                             reply_markup=reply_keyboard())
    else:
        bot.send_message(message.chat.id,
                         "Используй кнопки внизу экрана\nИли введи: 100 USD или 100 USD EUR",
                         reply_markup=reply_keyboard())


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    currency_map = {
        'usd': 'USD', 'eur': 'EUR', 'gbp': 'GBP', 'cny': 'CNY',
        'jpy': 'JPY', 'chf': 'CHF', 'cad': 'CAD', 'aud': 'AUD',
        'kzt': 'KZT', 'byn': 'BYN'
    }

    if call.data in currency_map:
        get_fiat_rate(call.message, currency_map[call.data])

    bot.answer_callback_query(call.id)


def perevod_v_rub(chat_id, amount, currency):
    """Конвертация из валюты в рубли с фото"""
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=10)
        data = response.json()

        if currency not in data['Valute']:
            bot.send_message(chat_id, f"Валюта {currency} не найдена", reply_markup=reply_keyboard())
            return

        rate = data['Valute'][currency]['Value']
        nominal = data['Valute'][currency]['Nominal']
        rub_amount = amount * (rate / nominal)

        currency_names = {
            'USD': 'Доллар США', 'EUR': 'Евро', 'GBP': 'Фунт стерлингов',
            'CNY': 'Китайский юань', 'JPY': 'Японская йена', 'CHF': 'Швейцарский франк',
            'CAD': 'Канадский доллар', 'AUD': 'Австралийский доллар',
            'KZT': 'Казахстанский тенге', 'BYN': 'Белорусский рубль'
        }

        currency_name = currency_names.get(currency, currency)

        text = (f"💱 Результат конвертации:\n\n"
                f"{amount:.2f} {currency} ({currency_name})\n"
                f"= {rub_amount:.2f} 🇷🇺 Российских рублей (RUB)\n\n"
                f"📈 Курс: 1 {currency} = {(rate / nominal):.4f} RUB\n"
                f"📊 Источник: Центральный Банк РФ")

        bot.send_message(chat_id, text, reply_markup=reply_keyboard())

    except Exception as e:
        bot.send_message(chat_id, "Ошибка получения курса. Попробуй позже.", reply_markup=reply_keyboard())


def convert_any_to_any(chat_id, amount, from_currency, to_currency):
    """Конвертация из любой валюты в любую"""
    try:
        valute = get_all_rates()
        
        if from_currency != 'RUB' and from_currency not in valute:
            bot.send_message(chat_id, f"Валюта {from_currency} не найдена", reply_markup=reply_keyboard())
            return
        if to_currency != 'RUB' and to_currency not in valute:
            bot.send_message(chat_id, f"Валюта {to_currency} не найдена", reply_markup=reply_keyboard())
            return
        
        if from_currency == 'RUB':
            from_rate = 1
            from_nominal = 1
        else:
            from_rate = valute[from_currency]['Value']
            from_nominal = valute[from_currency]['Nominal']
        
        if to_currency == 'RUB':
            to_rate = 1
            to_nominal = 1
        else:
            to_rate = valute[to_currency]['Value']
            to_nominal = valute[to_currency]['Nominal']
        
        rub_amount = amount * (from_rate / from_nominal)
        result_amount = rub_amount / (to_rate / to_nominal)
        
        currency_names = {
            'USD': 'Доллар США', 'EUR': 'Евро', 'GBP': 'Фунт стерлингов',
            'CNY': 'Китайский юань', 'JPY': 'Японская йена', 'CHF': 'Швейцарский франк',
            'CAD': 'Канадский доллар', 'AUD': 'Австралийский доллар',
            'KZT': 'Казахстанский тенге', 'BYN': 'Белорусский рубль', 'RUB': 'Российский рубль'
        }
        
        from_name = currency_names.get(from_currency, from_currency)
        to_name = currency_names.get(to_currency, to_currency)
        
        text = (f"💱 Результат конвертации:\n\n"
                f"{amount:.2f} {from_currency} ({from_name})\n"
                f"= {result_amount:.2f} {to_currency} ({to_name})\n\n"
                f"📈 1 {from_currency} = {(from_rate / from_nominal):.4f} RUB\n"
                f"📈 1 {to_currency} = {(to_rate / to_nominal):.4f} RUB\n"
                f"📊 Источник: Центральный Банк РФ")
        
        bot.send_message(chat_id, text, reply_markup=reply_keyboard())
        
    except Exception as e:
        bot.send_message(chat_id, "Ошибка получения курса. Попробуй позже.", reply_markup=reply_keyboard())


def get_fiat_rate(message, currency):
    """Отправляет курс валюты с фото (как в первом боте)"""
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=10)
        data = response.json()

        if currency not in data['Valute']:
            bot.send_message(message.chat.id, f"Валюта {currency} не найдена", reply_markup=reply_keyboard())
            return

        rate = data['Valute'][currency]['Value']
        nominal = data['Valute'][currency]['Nominal']

        currency_info = {
            'USD': {'name': 'Доллар США', 'flag': '🇺🇸', 'photo': 'usd.jpg'},
            'EUR': {'name': 'Евро', 'flag': '🇪🇺', 'photo': 'eur.jpg'},
            'GBP': {'name': 'Фунт стерлингов', 'flag': '🇬🇧', 'photo': 'gbp.jpg'},
            'CNY': {'name': 'Китайский юань', 'flag': '🇨🇳', 'photo': 'cny.jpg'},
            'JPY': {'name': 'Японская йена', 'flag': '🇯🇵', 'photo': 'jpy.jpg'},
            'CHF': {'name': 'Швейцарский франк', 'flag': '🇨🇭', 'photo': 'chf.jpg'},
            'CAD': {'name': 'Канадский доллар', 'flag': '🇨🇦', 'photo': 'cad.jpg'},
            'AUD': {'name': 'Австралийский доллар', 'flag': '🇦🇺', 'photo': 'aud.jpg'},
            'KZT': {'name': 'Казахстанский тенге', 'flag': '🇰🇿', 'photo': 'kzt.jpg'},
            'BYN': {'name': 'Белорусский рубль', 'flag': '🇧🇾', 'photo': 'byn.jpg'}
        }

        info = currency_info.get(currency, {'name': currency, 'flag': '', 'photo': None})

        text = (f"{info['flag']} {info['name']} ({currency})\n\n"
                f"💵 Номинал: {nominal} {currency}\n"
                f"💰 Курс: {rate:.2f} RUB\n"
                f"📈 1 {currency} = {rate / nominal:.4f} RUB")

        if info['photo']:
            photo_path = os.path.join(PHOTOS_PATH, info['photo'])
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo,
                                   caption=text, reply_markup=reply_keyboard())
            else:
                bot.send_message(message.chat.id, text, reply_markup=reply_keyboard())
        else:
            bot.send_message(message.chat.id, text, reply_markup=reply_keyboard())

    except Exception as e:
        bot.send_message(message.chat.id,
                         "Ошибка получения курса. Попробуй позже.",
                         reply_markup=reply_keyboard())


bot.infinity_polling()