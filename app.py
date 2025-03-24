from flask import Flask, render_template, request, jsonify, session
import json
import logging
import os
import datetime
import time
import re
import threading
from dotenv import load_dotenv
import telebot
from telebot import types
import urllib.parse

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настройки Telegram-бота
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7611972902:AAGn_OlH9cDqtr1RT95VTzPclC_cj2rAloU')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '6951859094')
SECRET_KEY = os.getenv('SECRET_KEY', 'assenizator-nn-secret-key-2025')

# Базовый адрес (ваш адрес, от которого будет строиться маршрут)
BASE_ADDRESS = "ул. Монастырка, 15, Нижний Новгород, Нижегородская обл., Россия, 603016"
# Примерные координаты базового адреса (для Яндекс Навигатора)
BASE_COORDINATES = "56.27569,43.88983"

# Файл для хранения заказов
ORDERS_FILE = 'orders.json'

# Инициализация приложения Flask
app = Flask(__name__, static_folder='static')
app.secret_key = SECRET_KEY

# Инициализация бота Telegram
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Хранилище заказов
orders = {}

# Функции для работы с данными

def load_orders():
    """Загрузка заказов из файла"""
    global orders
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, 'r', encoding='utf-8') as file:
                orders = json.load(file)
            logger.info(f"Загружено {len(orders)} заказов из файла")
        except Exception as e:
            logger.error(f"Ошибка при загрузке заказов: {e}")
            orders = {}
    else:
        orders = {}

def save_orders():
    """Сохранение заказов в файл"""
    try:
        with open(ORDERS_FILE, 'w', encoding='utf-8') as file:
            json.dump(orders, file, ensure_ascii=False, indent=4)
        logger.info(f"Сохранено {len(orders)} заказов в файл")
    except Exception as e:
        logger.error(f"Ошибка при сохранении заказов: {e}")

def generate_order_id():
    """Генерация ID заказа"""
    now = datetime.datetime.now()
    date_part = now.strftime('%Y%m%d')
    
    # Ищем максимальный номер заказа за текущий день
    max_num = 0
    for order_id in orders.keys():
        if order_id.startswith(date_part):
            try:
                num = int(order_id.split('-')[1])
                if num > max_num:
                    max_num = num
            except:
                pass
    
    return f"{date_part}-{max_num + 1}"

def get_navigation_links(address):
    """Создание рабочих ссылок для различных навигационных приложений с проверкой валидности адреса"""
    # Проверка минимальной длины адреса
    if not address or len(address.strip()) < 5:
        # Возвращаем только веб-ссылки для коротких адресов
        return {
            "yandex_maps": f"https://yandex.ru/maps/?mode=search&text={urllib.parse.quote(address)}",
            "google_maps": f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"
        }
    
    encoded_address = urllib.parse.quote(address)
    
    # Для веб-сервисов адрес всегда можно использовать
    yandex_maps = f"https://yandex.ru/maps/?mode=routes&rtext={BASE_COORDINATES}~{encoded_address}&rtt=auto"
    google_maps = f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(BASE_ADDRESS)}&destination={encoded_address}&travelmode=driving"
    
    return {
        "yandex_maps": yandex_maps,  # Яндекс Карты (веб)
        "google_maps": google_maps,  # Google Maps (веб)
    }

def format_order_message(order_id, order):
    """Форматирование сообщения о заказе"""
    message = f"""
<b>🆕 ЗАКАЗ #{order_id}</b>

<b>👤 Клиент:</b> {order['name']}
<b>📞 Телефон:</b> {order['phone']}
<b>📍 Адрес:</b> {order.get('address', 'Не указан')}
<b>🚚 Услуга:</b> {order.get('service_type', 'Откачка септика')}
<b>📝 Комментарий:</b> {order.get('comment', 'Нет')}
<b>⏰ Создан:</b> {order.get('created_at', 'Неизвестно')}
"""
    return message

def get_order_keyboard(order_id):
    """Создание клавиатуры для управления заказом с прямыми кнопками действий"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Кнопки для управления заказом
    markup.add(
        types.InlineKeyboardButton("✅ Выполнено", callback_data=f"complete_{order_id}"),
        types.InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_{order_id}")
    )
    
    # Получаем данные заказа
    if order_id in orders:
        order = orders[order_id]
        
        # Если есть телефон, добавляем кнопку звонка
        if 'phone' in order:
            # Очищаем телефон от лишних символов для ссылки
            clean_phone = re.sub(r'[^\d+]', '', order['phone'])
            if not clean_phone.startswith('+'):
                clean_phone = '+' + clean_phone
                
            markup.add(
                types.InlineKeyboardButton("📞 Позвонить клиенту", callback_data=f"call_{order_id}")
            )
        
        # Если есть адрес, добавляем кнопки навигации
        if 'address' in order and order['address'] and len(order['address'].strip()) >= 5:
            try:
                nav_links = get_navigation_links(order['address'])
                
                # Добавляем только веб-версии навигационных сервисов
                nav_row = [
                    types.InlineKeyboardButton("🗺️ Яндекс Карты", url=nav_links["yandex_maps"]),
                    types.InlineKeyboardButton("🌐 Google Maps", url=nav_links["google_maps"])
                ]
                markup.add(*nav_row)
            except Exception as e:
                logger.error(f"Ошибка при создании навигационных ссылок: {e}")
    
    return markup

def safe_send_telegram_message(order_id, order):
    """Безопасная отправка сообщения в Telegram с несколькими уровнями отката"""
    try:
        # Формируем сообщение для отправки в Telegram
        message_text = format_order_message(order_id, order)
        
        # Создаем клавиатуру с кнопками
        keyboard = get_order_keyboard(order_id)
        
        # Попытка 1: Отправка полного сообщения с форматированием и клавиатурой
        try:
            logger.info(f"Отправка заказа #{order_id} в Telegram (попытка 1: полное форматирование)...")
            sent_msg = bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            logger.info(f"Заказ #{order_id} успешно отправлен в Telegram, message_id: {sent_msg.message_id}")
            return True
        except Exception as e:
            logger.warning(f"Ошибка при отправке заказа (попытка 1): {e}")
            
            # Попытка 2: Отправка с HTML, но без клавиатуры
            try:
                logger.info(f"Отправка заказа #{order_id} в Telegram (попытка 2: без клавиатуры)...")
                sent_msg = bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=message_text,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                logger.info(f"Заказ #{order_id} отправлен без клавиатуры, message_id: {sent_msg.message_id}")
                
                # Отправляем простые кнопки в отдельном сообщении
                simple_keyboard = types.InlineKeyboardMarkup(row_width=2)
                simple_keyboard.add(
                    types.InlineKeyboardButton("✅ Выполнено", callback_data=f"complete_{order_id}"),
                    types.InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_{order_id}")
                )
                bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=f"Действия для заказа #{order_id}:",
                    reply_markup=simple_keyboard
                )
                return True
            except Exception as e:
                logger.warning(f"Ошибка при отправке заказа (попытка 2): {e}")
                
                # Попытка 3: Отправка без HTML-форматирования
                try:
                    logger.info(f"Отправка заказа #{order_id} в Telegram (попытка 3: без форматирования)...")
                    # Создаем упрощенное сообщение без HTML тегов
                    plain_message = f"""
НОВЫЙ ЗАКАЗ #{order_id}

Клиент: {order['name']}
Телефон: {order['phone']}
Адрес: {order.get('address', 'Не указан')}
Услуга: {order.get('service_type', 'Откачка септика')}
Комментарий: {order.get('comment', 'Нет')}
Создан: {order.get('created_at', 'Неизвестно')}
"""
                    sent_msg = bot.send_message(
                        chat_id=TELEGRAM_CHAT_ID,
                        text=plain_message,
                        disable_web_page_preview=True
                    )
                    logger.info(f"Заказ #{order_id} отправлен без форматирования, message_id: {sent_msg.message_id}")
                    return True
                except Exception as e:
                    logger.error(f"Не удалось отправить заказ даже в plain text: {e}")
                    return False
    except Exception as e:
        logger.error(f"Общая ошибка при отправке заказа в Telegram: {e}")
        return False

# Обработчики команд бота

@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обработчик команды /start"""
    welcome_text = """
👋 Здравствуйте!

Это бот для управления заказами компании "Ассенизатор НН".
Здесь вы будете получать уведомления о новых заказах.

<b>Доступные команды:</b>
/start - Начать работу с ботом
/help - Получить справку
/orders - Показать текущие заказы
"""
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML')

@bot.message_handler(commands=['help'])
def handle_help(message):
    """Обработчик команды /help"""
    help_text = """
<b>📋 Справка по работе с ботом:</b>

<b>Основные команды:</b>
/start - Начать работу с ботом
/help - Эта справка
/orders - Показать текущие заказы

<b>При получении заказа:</b>
• Вы увидите информацию о клиенте
• С помощью кнопок под заказом можно:
  - Отметить заказ как выполненный
  - Отменить заказ
  - Позвонить клиенту (откроется звонилка)
 

<b>Для управления заказами используйте кнопки под сообщениями!</b>
"""
    
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(commands=['orders'])
def handle_orders(message):
    """Обработчик команды /orders - показывает активные заказы"""
    # Получаем активные заказы (без статуса completed или cancelled)
    active_orders = {order_id: order for order_id, order in orders.items() 
                   if not order.get('status') in ['completed', 'cancelled']}
    
    if not active_orders:
        bot.send_message(message.chat.id, "На данный момент нет активных заказов.")
        return
    
    # Отправляем сообщения о каждом активном заказе
    bot.send_message(message.chat.id, f"<b>📋 Активные заказы ({len(active_orders)}):</b>", parse_mode='HTML')
    
    for order_id, order in active_orders.items():
        # Отправляем информацию о заказе
        order_message = format_order_message(order_id, order)
        
        # Создаем клавиатуру с кнопками
        keyboard = get_order_keyboard(order_id)
        
        # Отправляем сообщение
        try:
            sent_msg = bot.send_message(
                chat_id=message.chat.id,
                text=order_message,
                parse_mode='HTML',
                reply_markup=keyboard,
                disable_web_page_preview=True  # Отключаем предпросмотр для ссылок
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке активного заказа #{order_id}: {e}")
            # Пробуем отправить в простом формате
            plain_message = f"""
ЗАКАЗ #{order_id}

Клиент: {order['name']}
Телефон: {order['phone']}
Адрес: {order.get('address', 'Не указан')}
Услуга: {order.get('service_type', 'Откачка септика')}
Комментарий: {order.get('comment', 'Нет')}
Создан: {order.get('created_at', 'Неизвестно')}
"""
            bot.send_message(
                chat_id=message.chat.id,
                text=plain_message,
                disable_web_page_preview=True
            )

# Обработчик callback-запросов от кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    callback_data = call.data
    
    try:
        if callback_data.startswith("complete_"):
            # Обработка завершения заказа
            order_id = callback_data.replace("complete_", "")
            
            if order_id in orders:
                # Отмечаем заказ как выполненный
                orders[order_id]['status'] = 'completed'
                orders[order_id]['completed_at'] = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
                
                # Сохраняем изменения
                save_orders()
                
                # Отправляем подтверждение
                bot.answer_callback_query(call.id, "✅ Заказ отмечен как выполненный")
                
                # Обновляем сообщение с заказом
                try:
                    updated_message = f"{format_order_message(order_id, orders[order_id])}\n\n<b>✅ ВЫПОЛНЕН</b>"
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=updated_message,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Ошибка при обновлении сообщения: {e}")
        
        elif callback_data.startswith("cancel_"):
            # Обработка отмены заказа
            order_id = callback_data.replace("cancel_", "")
            
            if order_id in orders:
                # Отмечаем заказ как отмененный
                orders[order_id]['status'] = 'cancelled'
                orders[order_id]['cancelled_at'] = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
                
                # Сохраняем изменения
                save_orders()
                
                # Отправляем подтверждение
                bot.answer_callback_query(call.id, "❌ Заказ отменен")
                
                # Обновляем сообщение с заказом
                try:
                    updated_message = f"{format_order_message(order_id, orders[order_id])}\n\n<b>❌ ОТМЕНЕН</b>"
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=updated_message,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Ошибка при обновлении сообщения: {e}")
        
        elif callback_data.startswith("call_"):
            # Обработка звонка клиенту
            order_id = callback_data.replace("call_", "")
            
            if order_id in orders and 'phone' in orders[order_id]:
                phone = orders[order_id]['phone']
                
                # Очищаем телефон от лишних символов
                clean_phone = re.sub(r'[^\d+]', '', phone)
                if not clean_phone.startswith('+'):
                    clean_phone = '+' + clean_phone
                
                # Отправляем подтверждение
                bot.answer_callback_query(
                    call.id, 
                    f"Открываю звонилку...",
                    show_alert=False
                )
                
                # Отправляем сообщение с прямой ссылкой на телефонный звонок
                # Эта ссылка должна открыть приложение для звонков с уже набранным номером
                bot.send_message(
                    call.message.chat.id,
                    f'<a href="tel:{clean_phone}">Позвонить клиенту: {phone}</a>',
                    parse_mode='HTML'
                )
    
    except Exception as e:
        logger.error(f"Ошибка при обработке callback: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")

# Flask маршруты

@app.route('/')
def index():
    """Главная страница - наш лендинг"""
    return render_template('index.html')

@app.route('/submit-form', methods=['POST'])
def submit_form():
    """Обработчик отправки формы с отправкой данных в Telegram"""
    try:
        # Проверка защиты от повторной отправки
        form_id = request.form.get('form_id', '')
        session_id = session.get('last_form_id', '')
        
        logger.info(f"Получен новый запрос на создание заказа, form_id: {form_id}")
        
        if form_id and form_id == session_id:
            # Это повторная отправка формы, возвращаем успех без создания нового заказа
            logger.warning(f"Обнаружена повторная отправка формы: {form_id}")
            return jsonify({"success": True, "message": "Заявка уже была отправлена."})
        
        # Получаем данные из формы
        name = request.form.get('name', 'Не указано')
        phone = request.form.get('phone', 'Не указано')
        address = request.form.get('address', 'Не указано')
        service_type = request.form.get('service_type', 'Откачка септика')
        date_time = request.form.get('date_time', '')
        comment = request.form.get('comment', '')
        
        logger.info(f"Получены данные: имя: {name}, телефон: {phone}, адрес: {address}")
        
        # Генерируем уникальный ID заказа
        order_id = generate_order_id()
        
        # Создаем объект заказа
        order = {
            'name': name,
            'phone': phone,
            'address': address,
            'service_type': service_type,
            'date_time': date_time,
            'comment': comment,
            'created_at': datetime.datetime.now().strftime('%d.%m.%Y %H:%M'),
            'status': 'new'  # Добавляем явный статус
        }
        
        # Добавляем заказ в список
        orders[order_id] = order
        logger.info(f"Заказ #{order_id} создан и добавлен в список")
        save_orders()
        logger.info(f"Заказ #{order_id} сохранен в файл")
        
        # Сохраняем ID формы в сессии для защиты от повторной отправки
        session['last_form_id'] = form_id
        
        # Отправляем сообщение в Telegram с использованием безопасной функции
        result = safe_send_telegram_message(order_id, order)
        
        # Возвращаем успех в любом случае для клиента
        return jsonify({"success": True, "message": "Заявка успешно отправлена!"})
    
    except Exception as e:
        logger.error(f"Общая ошибка при обработке формы: {str(e)}")
        return jsonify({"success": False, "message": "Произошла ошибка при отправке заявки. Пожалуйста, позвоните нам."})

@app.errorhandler(404)
def page_not_found(e):
    """Обработчик ошибки 404"""
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Обработчик ошибки 500"""
    logger.error(f"Ошибка сервера: {str(e)}")
    return jsonify({"success": False, "message": "Внутренняя ошибка сервера. Пожалуйста, попробуйте позже."}), 500

# Инициализация данных и настройка Telegram-бота

def init_data():
    """Инициализация данных"""
    load_orders()
    logger.info("Данные успешно загружены")

def start_bot():
    """Запуск бота в режиме polling"""
    # Удаляем текущий webhook, если есть
    try:
        logger.info("Удаление webhook...")
        bot.remove_webhook()
        logger.info("Webhook успешно удален")
    except Exception as e:
        logger.error(f"Ошибка при удалении webhook: {e}")
    
    time.sleep(1)
    
    # Проверяем соединение с Telegram API
    try:
        logger.info("Проверка подключения к API Telegram...")
        me = bot.get_me()
        logger.info(f"Успешное подключение к API Telegram. Имя бота: {me.first_name}, username: @{me.username}")
    except Exception as e:
        logger.error(f"Ошибка при подключении к API Telegram: {e}")
    
    # Запускаем бота в отдельном потоке
    def polling_worker():
        logger.info("Запуск бота в режиме polling")
        
        while True:
            try:
                logger.info("Запуск цикла polling")
                bot.polling(none_stop=True, timeout=60)
            except Exception as e:
                logger.error(f"Ошибка в цикле polling: {e}")
                time.sleep(10)  # Пауза перед повторной попыткой
    
    # Запускаем поток для режима polling
    polling_thread = threading.Thread(target=polling_worker, daemon=True)
    polling_thread.start()
    logger.info("Бот запущен в режиме polling")

if __name__ == '__main__':
    try:
        # Инициализация данных
        init_data()
        
        # Запуск бота
        start_bot()
        
        # Запускаем Flask приложение
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске приложения: {str(e)}")