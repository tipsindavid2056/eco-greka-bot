import telebot
from telebot import types
import os

# Конфигурация
BOT_TOKEN = "8528658688:AAHTvP1HFVOI5lhDmrlIRlIBfv7kGFqfy5A"
MANAGER_CHAT_ID = 100885885
CARD_NUMBER = "1111"  # Замените на реальный номер карты

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище данных пользователей
user_data = {}

def get_main_menu():
    """Главное меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("💰 Цена"))
    markup.add(types.KeyboardButton("🛒 Оформить доставку"))
    return markup

def get_payment_menu():
    """Меню после оплаты"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("✅ Оплатил"))
    markup.add(types.KeyboardButton("🔙 Назад"))
    return markup

def get_contact_location_menu():
    """Меню для отправки контакта и геолокации"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📱 Отправить контакт", request_contact=True))
    markup.add(types.KeyboardButton("📍 Отправить геолокацию", request_location=True))
    markup.add(types.KeyboardButton("🔙 Назад"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    """Приветствие"""
    user_data[message.chat.id] = {}
    
    welcome_text = """
🌿 *Добро пожаловать в магазин Эко-грелок!*

Наши грелки:
• 100% натуральные материалы
• Безопасны для здоровья
• Долго сохраняют тепло

Выберите действие в меню ниже 👇
"""
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

@bot.message_handler(func=lambda m: m.text == "💰 Цена")
def show_price(message):
    """Показать цену"""
    price_text = """
💰 *Цена: 250 000 сум*

🌿 Эко-грелка из натуральных материалов

✅ В стоимость входит:
• Грелка
• Упаковка
• Доставка по городу

Нажмите "🛒 Оформить доставку" чтобы заказать!
"""
    bot.send_message(message.chat.id, price_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🛒 Оформить доставку")
def start_order(message):
    """Начать оформление заказа"""
    user_data[message.chat.id] = {'step': 'waiting_payment'}
    
    order_text = f"""
🛒 *Оформление заказа*

💳 *Данные для оплаты:*
Карта: `{CARD_NUMBER}`
Сумма: *250 000 сум*

Переведите оплату и нажмите "✅ Оплатил"
"""
    bot.send_message(
        message.chat.id, 
        order_text, 
        parse_mode="Markdown",
        reply_markup=get_payment_menu()
    )

@bot.message_handler(func=lambda m: m.text == "✅ Оплатил")
def payment_confirmed(message):
    """Подтверждение оплаты"""
    user_data[message.chat.id]['step'] = 'waiting_contact'
    
    text = """
✅ *Отлично!*

Теперь отправьте ваш контакт и геолокацию для доставки:

👇 Нажмите кнопки ниже
"""
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=get_contact_location_menu()
    )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    """Обработка контакта"""
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {}
    
    user_data[message.chat.id]['phone'] = message.contact.phone_number
    user_data[message.chat.id]['name'] = message.contact.first_name or "Не указано"
    user_data[message.chat.id]['contact_received'] = True
    
    bot.send_message(message.chat.id, "📱 Контакт получен! Теперь отправьте геолокацию 📍")
    
    check_order_complete(message.chat.id)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    """Обработка геолокации"""
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {}
    
    user_data[message.chat.id]['latitude'] = message.location.latitude
    user_data[message.chat.id]['longitude'] = message.location.longitude
    user_data[message.chat.id]['location_received'] = True
    
    bot.send_message(message.chat.id, "📍 Геолокация получена!")
    
    check_order_complete(message.chat.id)

def check_order_complete(chat_id):
    """Проверка завершения заказа"""
    data = user_data.get(chat_id, {})
    
    if data.get('contact_received') and data.get('location_received'):
        # Заказ принят
        bot.send_message(
            chat_id,
            "✅ *Заказ принят!*\n\n📦 Отправляем ваш заказ!\n\nСпасибо за покупку! 🌿",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        
        # Уведомление менеджеру
        send_order_to_manager(chat_id, data)
        
        # Очистка данных
        user_data[chat_id] = {}

def send_order_to_manager(chat_id, data):
    """Отправка заказа менеджеру"""
    order_text = f"""
🆕 *НОВЫЙ ЗАКАЗ!*

👤 *Клиент:* {data.get('name', 'Не указано')}
📱 *Телефон:* {data.get('phone', 'Не указано')}
🆔 *Chat ID:* {chat_id}

💰 *Сумма:* 250 000 сум
📦 *Товар:* Эко-грелка

📍 *Геолокация:* Отправлена отдельно
"""
    
    try:
        bot.send_message(MANAGER_CHAT_ID, order_text, parse_mode="Markdown")
        
        # Отправляем геолокацию менеджеру
        if data.get('latitude') and data.get('longitude'):
            bot.send_location(
                MANAGER_CHAT_ID,
                latitude=data['latitude'],
                longitude=data['longitude']
            )
    except Exception as e:
        print(f"Ошибка отправки менеджеру: {e}")

@bot.message_handler(func=lambda m: m.text == "🔙 Назад")
def go_back(message):
    """Вернуться в главное меню"""
    user_data[message.chat.id] = {}
    bot.send_message(
        message.chat.id,
        "🏠 Главное меню",
        reply_markup=get_main_menu()
    )

@bot.message_handler(func=lambda m: True)
def handle_other(message):
    """Обработка прочих сообщений"""
    bot.send_message(
        message.chat.id,
        "Пожалуйста, используйте кнопки меню 👇",
        reply_markup=get_main_menu()
    )

if __name__ == "__main__":
    print("🤖 Бот запущен...")
    bot.infinity_polling()
