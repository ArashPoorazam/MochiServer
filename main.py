# Libraries
import re
import time
import requests
import telebot
import logging
import mysql.connector
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from telebot import custom_filters

# Files
import Description as Des
import Config as Keys
import Responses as Res

# Configure the logger
logging.basicConfig(
    level=logging.INFO,                                             # Set level to INFO to log startup messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Include timestamp, log level, and message
    handlers=[
        logging.FileHandler("bot.log"),                             # Log messages into a file
        logging.StreamHandler()                                     # Also log messages to the console
    ]
)


# Create a bot object
state_storage = StateMemoryStorage()

bot = telebot.TeleBot(Keys.API_KEY, state_storage=state_storage)
logging.info('Start bot...')


# States
class buy(StatesGroup):
    request = State()
    respond = State()


# Function to escape all special characters with a backslash
def escape_special_characters(text):
    special_characters = r"([\*\_\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])"
    return re.sub(special_characters, r'\\\1', text)


# fetch data
def balance_fetch(user_id):
    try:
        with mysql.connector.connect(**Keys.db_config) as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users WHERE id = %s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchall()
                if result:
                    return result
                else:
                    return [(None, None, None, None, 0)]  # Default balance if user not found

    except Exception as e:
        logging.error(f"Error while fetching data: {e}")
        return [(None, None, None, None, 0)]  # Default balance in case of error


# /start Command
@bot.message_handler(commands=['start'])
def start_command(user_message):
    # check or create user in database
    try:
        with mysql.connector.connect(**Keys.db_config) as connection:
            with connection.cursor() as cursor:
                sql = "INSERT INTO users (id, username, first_name, last_name) VALUES (%s, %s, %s, %s)"
                values = (user_message.chat.id, user_message.chat.username, user_message.chat.first_name, user_message.chat.last_name)
                cursor.execute(sql, values)
                connection.commit()

                token = user_message.text.split()
                if len(token) > 1:
                    sql = "UPDATE users SET balance = balance + 40000 WHERE id = %s"
                    cursor.execute(sql, (user_message.chat.id,))
                    connection.commit()

        logging.info(f"User {user_message.chat.id} added to database")

    except mysql.connector.Error as err:
        logging.error(f"User already exist: {err}")
        bot.send_message(user_message.chat.id, "بازگشت به منو 🏡")

    # Create Buttons
    first_button = telebot.types.InlineKeyboardButton('🔑 کانفیگ تستی', callback_data='start_test')
    second_button = telebot.types.InlineKeyboardButton('🛒 خرید کانفیگ', callback_data='start_buy')
    third_button = telebot.types.InlineKeyboardButton('👩‍🧑‍🦰 پروفایل من', callback_data='start_profile')
    fourth_button = telebot.types.InlineKeyboardButton('📋 راهنمای استفاده', callback_data='start_help')
    fifth_button = telebot.types.InlineKeyboardButton('🎁 تخفیف ریفرال', callback_data='start_discount')
    sixth_button = telebot.types.InlineKeyboardButton('💰 افزایش موجودی', callback_data='start_funds')
    seventh_button = telebot.types.InlineKeyboardButton('💻 Admin Panel 💻', callback_data='admin')
    eighth_button = telebot.types.InlineKeyboardButton('🌟 VIP 🌟', callback_data='vip')
    nineth_button = telebot.types.InlineKeyboardButton('❤️ Mahsa ❤️', callback_data='mahsa')

    glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    if user_message.chat.id in Keys.ADMIN_ID:
        glass_markup.add(seventh_button)
        glass_markup.add(eighth_button, nineth_button, first_button, second_button, third_button, fourth_button, fifth_button, sixth_button)

    elif user_message.chat.id in Keys.VIPS_ID:
        glass_markup.add(eighth_button)
        glass_markup.add(first_button, second_button, third_button, fourth_button, fifth_button, sixth_button)

    elif user_message.chat.id == Keys.MAHSA_ID:
        glass_markup.add(nineth_button)
        glass_markup.add(first_button, second_button, third_button, fourth_button, fifth_button, sixth_button)

    else:
        glass_markup.add(first_button, second_button, third_button, fourth_button, fifth_button, sixth_button)

    bot.send_message(chat_id=user_message.chat.id, text=Des.start_description, reply_markup=glass_markup)
    bot.delete_state(user_id=user_message.from_user.id, chat_id=user_message.chat.id)


# Handling requests
@bot.callback_query_handler(func=lambda call: call.data == "answer")
def answer(call):
    pattern = r"Recived a message from: (\d+)"  # Extract user id from the message
    user_id_match = re.findall(pattern=pattern, string=call.message.caption if call.message.caption else call.message.text)
    
    if not user_id_match:
        bot.send_message(chat_id=call.message.chat.id, text="User ID not found in the message.")
        return
    
    user = user_id_match[0]

    bot.send_message(chat_id=call.message.chat.id, text=f"Send your answer to: {user}", reply_markup=telebot.types.ForceReply())
    bot.set_state(user_id=call.from_user.id, state=buy.respond, chat_id=call.message.chat.id)


# User info and actions
@bot.callback_query_handler(func=lambda call: call.data.startswith('user_'))
def user_info(call):
    user_id = call.data.split('_')[1]
    
    try:
        with mysql.connector.connect(**Keys.db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, username, first_name, last_name, balance FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if user:
                    text = f"""👤 اطلاعات کاربر:
                    🌐 شناسه کاربری: {user[0]}
                    🍀 یوزرنیم: {user[1]}
                    🍷 نام: {user[2]}
                    🍷 نام خانوادگی: {user[3]}
                    💰 موجودی: {user[4]}"""

                    edit_button = telebot.types.InlineKeyboardButton("✏️ ویرایش اطلاعات", callback_data=f"edit_{user[0]}")
                    block_button = telebot.types.InlineKeyboardButton("🚫 مسدود کردن", callback_data=f"block_{user[0]}")
                    back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='admin')

                    glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                    glass_markup.add(edit_button, block_button)
                    glass_markup.add(back_button)

                    bot.send_message(chat_id=call.message.chat.id, text=text, reply_markup=glass_markup)
                else:
                    bot.send_message(chat_id=call.message.chat.id, text="❌ کاربر یافت نشد.")

    except Exception as e:
        logging.error(f"Error while fetching user info: {e}")
        bot.send_message(chat_id=call.message.chat.id, text="❌ خطا در دریافت اطلاعات کاربر.")


# Edit user info
@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_'))
def edit_user(call):
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        logging.error(f"Error while deleting message: {e}")

    user_id = call.data.split('_')[1]
    bot.send_message(chat_id=call.message.chat.id, text=f"✏️ اطلاعات جدید کاربر {user_id} را وارد کنید (فرمت: username,first_name,last_name,balance):")
    bot.set_state(user_id=call.from_user.id, state=buy.request, chat_id=call.message.chat.id)
    Keys.edit_user_id = user_id


# Block user
@bot.callback_query_handler(func=lambda call: call.data.startswith('block_'))
def block_user(call):
    user_id = call.data.split('_')[1]
    
    try:
        with mysql.connector.connect(**Keys.db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                connection.commit()

        bot.send_message(chat_id=call.message.chat.id, text="🚫 کاربر با موفقیت مسدود شد.")
    
    except Exception as e:
        logging.error(f"Error while blocking user: {e}")
        bot.send_message(chat_id=call.message.chat.id, text="❌ خطا در مسدود کردن کاربر.")


# Callbacks
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        logging.error(f"Error while deleting message: {e}")

    # Back home
    if call.data == 'BACK_HOME':
        # Create Buttons
        first_button = telebot.types.InlineKeyboardButton('🔑 کانفیگ تستی', callback_data='start_test')
        second_button = telebot.types.InlineKeyboardButton('🛒 خرید کانفیگ', callback_data='start_buy')
        third_button = telebot.types.InlineKeyboardButton('👩‍🧑‍🦰 پروفایل من', callback_data='start_profile')
        fourth_button = telebot.types.InlineKeyboardButton('📋 راهنمای استفاده', callback_data='start_help')
        fifth_button = telebot.types.InlineKeyboardButton('🎁 تخفیف ریفرال', callback_data='start_discount')
        sixth_button = telebot.types.InlineKeyboardButton('💰 افزایش موجودی', callback_data='start_funds')
        seventh_button = telebot.types.InlineKeyboardButton('💻 Admin Panel 💻', callback_data='admin')
        eighth_button = telebot.types.InlineKeyboardButton('🌟 VIP 🌟', callback_data='vip')
        nineth_button = telebot.types.InlineKeyboardButton('❤️ Mahsa ❤️', callback_data='mahsa')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)

        if call.message.chat.id in Keys.ADMIN_ID:
            glass_markup.add(seventh_button)
            glass_markup.add(eighth_button, nineth_button, first_button, second_button, third_button, fourth_button, fifth_button, sixth_button)

        elif call.message.chat.id in Keys.VIPS_ID:
            glass_markup.add(eighth_button)
            glass_markup.add(first_button, second_button, third_button, fourth_button, fifth_button, sixth_button)

        elif call.message.chat.id == Keys.MAHSA_ID:
            glass_markup.add(nineth_button)
            glass_markup.add(first_button, second_button, third_button, fourth_button, fifth_button, sixth_button)

        else:
            glass_markup.add(first_button, second_button, third_button, fourth_button, fifth_button, sixth_button)

        bot.send_message(chat_id=call.message.chat.id, text=Des.start_description, reply_markup=glass_markup)
        # bot.delete_state(user_id=call.message.from_user.id, chat_id=call.message.chat.id)

    # Buy config
    elif call.data == 'start_buy':
        first_button = telebot.types.InlineKeyboardButton('اتریش 🇦🇹', callback_data='buy_NL')
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='BACK_HOME')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(first_button)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text=Des.buy_one_description, reply_markup=glass_markup)

    # Test config
    elif call.data == 'start_test':
        first_button = telebot.types.InlineKeyboardButton('ایرانسل - رایتل 🎏️', callback_data='request_test')
        second_button = telebot.types.InlineKeyboardButton('همراه اول - مخابرات 🎏', callback_data='request_test')
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='BACK_HOME')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(first_button, second_button)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text=Des.test_config_description, reply_markup=glass_markup)

    
    # Request test
    elif call.data == 'request_test':
        try:
            with mysql.connector.connect(**Keys.db_config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT test_config_used FROM users WHERE id = %s", (call.from_user.id,))
                    result = cursor.fetchone()
                    
                    if result and result[0]:
                        bot.answer_callback_query(call.id, "❌ شما قبلاً از کانفیگ تستی استفاده کرده‌اید.", show_alert=False)
                        return

                    # Mark test config as used
                    cursor.execute("UPDATE users SET test_config_used = TRUE WHERE id = %s", (call.from_user.id,))
                    connection.commit()

            # Send request to support
            first_button = telebot.types.InlineKeyboardButton("Send Config", callback_data='answer')
            back_button = telebot.types.InlineKeyboardButton("بازگشت به خانه 🏡", callback_data='BACK_HOME')

            glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            glass_markup.add(first_button)

            back_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            back_markup.add(back_button)

            bot.send_message(chat_id=Keys.SUPPORT_ID, text=f"Recived a message from: {call.from_user.id}\nName: {call.from_user.first_name}\nUsername: @{call.from_user.username}\n\nMessage text: Request Test Config 🏴‍☠", reply_markup=glass_markup)
            bot.send_message(chat_id=call.message.chat.id, text=Des.receipt_description, reply_markup=back_markup)
            
        except Exception as e:
            logging.error(f"Error while checking or updating test config usage: {e}")
            bot.send_message(chat_id=call.message.chat.id, text="❌ خطا از کانفیگ تستی.")

    
    # Profile
    elif call.data == 'start_profile':
        balance = balance_fetch(call.from_user.id)

        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='BACK_HOME')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text=f"""پروفایل من 👩‍🦰🧑‍🦰

🌐 شناسه کاربری: {call.from_user.id}
🍀 یوزرنیم: {call.from_user.username}
🍷 نام: {call.from_user.first_name}
💰 موجودی: {balance[0][4]}

-----------------------------------------------------------------------

کانفیگ های خریداری شده ⬇
""", reply_markup=glass_markup)

    # help
    elif call.data == 'start_help':
        # Create Buttons
        first_button = telebot.types.InlineKeyboardButton("ios - V2Box",
                                                        url="https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690")
        second_button = telebot.types.InlineKeyboardButton("android - V2ay",
                                                        url="https://play.google.com/store/apps/details?id=com.v2ray.ang&hl=en&gl=US")
        third_button = telebot.types.InlineKeyboardButton("windows - V2rayN",
                                                        url="https://sourceforge.net/projects/v2rayn.mirror/")
        fourth_button = telebot.types.InlineKeyboardButton("mac - Fair",
                                                        url="https://apps.apple.com/us/app/fair-vpn/id1533873488")
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='BACK_HOME')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(first_button, second_button, third_button, fourth_button)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text=Des.help_description, reply_markup=glass_markup)

    # discount
    elif call.data == 'start_discount':
        
        # Create Buttons
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='BACK_HOME')
        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(back_button)

        with open("Mochi_2.mp4", "rb") as video:
            bot.send_video(call.message.chat.id, 
                           video, 
                           caption=f"🎖 لینک رفرال: https://t.me/MochiServer_bot?start={call.from_user.id}" + Des.discount_description,
                           supports_streaming=True, 
                           reply_markup=glass_markup
                           )

    # funds
    elif call.data == 'start_funds':
        # Create Buttons
        first_button = telebot.types.InlineKeyboardButton("50.000 🪙", url="https://zarinp.al/681602")
        second_button = telebot.types.InlineKeyboardButton("110.000 🪙", url="https://zarinp.al/682929")
        third_button = telebot.types.InlineKeyboardButton("150.000 🪙", url="https://zarinp.al/682930")
        fourth_button = telebot.types.InlineKeyboardButton("200.000 🪙", url="https://zarinp.al/682931")
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='BACK_HOME')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(first_button, second_button, third_button, fourth_button)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text=Des.funds_description, reply_markup=glass_markup)

    # buy NL buttons
    elif call.data == 'buy_NL':
        first_button = telebot.types.InlineKeyboardButton('خرید کانفیگ تک نفره 🧜‍♂️', callback_data='NL_alone')
        second_button = telebot.types.InlineKeyboardButton('خرید کانفیگ خانوادگی 👫', callback_data='NL_family')
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='start_buy')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(first_button, second_button)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text=Des.buy_two_description, reply_markup=glass_markup)

    # buy NL alone button
    elif call.data == 'NL_alone':
        first_button = telebot.types.InlineKeyboardButton('ایرانسل - رایتل 🎏️', callback_data='NL_alone_ircell')
        second_button = telebot.types.InlineKeyboardButton('همراه اول - مخابرات 🎏', callback_data='NL_alone_hmaval')
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='buy_NL')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(first_button, second_button)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text=Des.buy_three_description, reply_markup=glass_markup)

    # buy NL alone button
    elif call.data == 'NL_family':
        first_button = telebot.types.InlineKeyboardButton('۳ نفره 👨‍👩‍👦️', callback_data='NL_family_3')
        second_button = telebot.types.InlineKeyboardButton('۵ نفره 👨‍👩‍👧‍👦', callback_data='NL_family_5')
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='buy_NL')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(first_button, second_button)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text=Des.buy_four_description, reply_markup=glass_markup)

    ### Transactions
    # buy NL alone ircell
    elif call.data == 'NL_alone_ircell':
        first_button = telebot.types.InlineKeyboardButton('🌐 پرداخت اینترنتی', url="https://zarinp.al/682933")
        second_button = telebot.types.InlineKeyboardButton('💳 پرداخت با موجودی', callback_data='wallet')
        third_button = telebot.types.InlineKeyboardButton("📨 ارسال رسید", callback_data='receipt')
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='NL_alone')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(first_button, second_button, third_button)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text="قیمت: ۱۵۰.۰۰۰ تومان 🪙"+Des.transaction_description, reply_markup=glass_markup)
        Keys.price = 150000


    # buy NL alone hmaval
    elif call.data == 'NL_alone_hmaval':
        first_button = telebot.types.InlineKeyboardButton('🌐 پرداخت اینترنتی', url="https://zarinp.al/682932")
        second_button = telebot.types.InlineKeyboardButton('💳 پرداخت با موجودی', callback_data='wallet')
        third_button = telebot.types.InlineKeyboardButton("📨 ارسال رسید", callback_data='receipt')
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='NL_alone')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(first_button, second_button, third_button)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text="قیمت: ۱۵۰.۰۰۰ تومان 🪙"+Des.transaction_description, reply_markup=glass_markup)
        Keys.price = 150000


    # buy NL family 3
    elif call.data == 'NL_family_3':
        first_button = telebot.types.InlineKeyboardButton('🌐 پرداخت اینترنتی', url="https://zarinp.al/682934")
        second_button = telebot.types.InlineKeyboardButton('💳 پرداخت با موجودی', callback_data='wallet')
        third_button = telebot.types.InlineKeyboardButton("📨 ارسال رسید", callback_data='receipt')
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='NL_family')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(first_button, second_button, third_button)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text="قیمت: ۴۰۰.۰۰۰ تومان 🪙"+Des.transaction_description, reply_markup=glass_markup)
        Keys.price = 400000


    # buy NL family 5
    elif call.data == 'NL_family_5':
        first_button = telebot.types.InlineKeyboardButton('🌐 پرداخت اینترنتی', url="https://zarinp.al/682935")
        second_button = telebot.types.InlineKeyboardButton('💳 پرداخت با موجودی', callback_data='wallet')
        third_button = telebot.types.InlineKeyboardButton("📨 ارسال رسید", callback_data='receipt')
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='NL_family')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(first_button, second_button, third_button)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text="قیمت: ۶۹۰.۰۰۰ تومان 🪙"+Des.transaction_description, reply_markup=glass_markup)
        Keys.price = 690000


    # wallet
    elif call.data == 'wallet':
        back_button = telebot.types.InlineKeyboardButton("بازگشت به خانه 🏡", callback_data='BACK_HOME')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(back_button)

        balance = balance_fetch(call.from_user.id)
        if balance[0][4] >= Keys.price:
            # Update balance
            try:
                with mysql.connector.connect(**Keys.db_config) as connection:
                    with connection.cursor() as cursor:
                        sql = "UPDATE users SET balance = balance - %s WHERE id = %s"
                        cursor.execute(sql, (Keys.price, call.from_user.id))
                        connection.commit()

                logging.info(f"User {call.from_user.id} balance updated")
                bot.send_message(chat_id=call.message.chat.id, text=Des.receipt_description, reply_markup=glass_markup)

                # Send request to support
                first_button = telebot.types.InlineKeyboardButton("Send Config", callback_data='answer')
                glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                glass_markup.add(first_button)

                bot.send_message(chat_id=Keys.SUPPORT_ID, text=f"Recived a message from: {call.from_user.id}\nName: {call.from_user.first_name}\nUsername: @{call.from_user.username}\n\nMessage text:\n{escape_special_characters(f'Payment successful, please send the config.')}\nAmount paid: {Keys.price} تومان", reply_markup=glass_markup)
                Keys.texts[call.from_user.id] = {'type': 'text', 'text': f'Payment successful, please send the config. Amount paid: {Keys.price} تومان'}

            except mysql.connector.Error as err:
                logging.error(f"Error while updating balance: {err}")
                bot.send_message(chat_id=call.message.chat.id, text="❌ خطا در پرداخت. 🪙", reply_markup=glass_markup)

        else:
            bot.send_message(chat_id=call.message.chat.id, text="❌ موجودی شما کافی نمیباشد. 🪙", reply_markup=glass_markup)


    # receipt
    elif call.data == 'receipt':
        bot.send_message(chat_id=call.message.chat.id , text="📸 عکس رسید پرداخت خود را ارسال کنید.\n📨 یا شناسه پرداخت خود را بنویسید.\n\n⬇⬇⬇") #, reply_markup=glass_markup)
        bot.set_state(user_id=call.from_user.id, state=buy.request, chat_id=call.message.chat.id)


    # Admin panel
    elif call.data == 'admin':
        # Fetch user list from the database
        try:
            with mysql.connector.connect(**Keys.db_config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT id, username, first_name, last_name, balance FROM users")
                    users = cursor.fetchall()
                    
                    user_buttons = []
                    for user in users:
                        user_buttons.append(telebot.types.InlineKeyboardButton(f"{user[2]} ({user[0]})", callback_data=f"user_{user[0]}"))

                    back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='BACK_HOME')
                    glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                    glass_markup.add(*user_buttons)
                    glass_markup.add(back_button)

                    bot.send_message(chat_id=call.message.chat.id, text=Des.admin_description, reply_markup=glass_markup)

        except Exception as e:
            logging.error(f"Error while fetching users: {e}")
            bot.send_message(chat_id=call.message.chat.id, text="❌ خطا در دریافت لیست کاربران.")

    # VIPS
    elif call.data == 'vip':
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='BACK_HOME')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text=Des.VIP_description, reply_markup=glass_markup)
        with open("VIP.png", "rb") as picture:
            bot.send_photo(call.message.chat.id, picture, caption=Keys.vip_config)


    # Mahsa
    elif call.data == 'mahsa':
        back_button = telebot.types.InlineKeyboardButton("❌ بازگشت", callback_data='BACK_HOME')

        glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        glass_markup.add(back_button)

        bot.send_message(chat_id=call.message.chat.id, text=Des.mahsa_description, reply_markup=glass_markup)
        with open("Mahsa.png", "rb") as picture:
            bot.send_photo(call.message.chat.id, picture, caption=Keys.mahsa_config)


    else:
        bot.answer_callback_query(call.id, "🔴🔴🔴 Unknown 🔴🔴🔴", show_alert=False)


@bot.message_handler(state=buy.request, content_types=['text'])
def update_user_info(user_message):
    try:
        user_id = Keys.edit_user_id
        new_info = user_message.text.split(',')
        if len(new_info) != 4:
            bot.send_message(chat_id=user_message.chat.id, text="❌ فرمت اطلاعات نادرست است.")
            return

        with mysql.connector.connect(**Keys.db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE users SET username = %s, first_name = %s, last_name = %s, balance = %s WHERE id = %s",
                               (new_info[0], new_info[1], new_info[2], new_info[3], user_id))
                connection.commit()

        bot.send_message(chat_id=user_message.chat.id, text="✅ اطلاعات کاربر با موفقیت به‌روزرسانی شد.")
        bot.delete_state(user_id=user_message.from_user.id, chat_id=user_message.chat.id)

    except Exception as e:
        logging.error(f"Error while updating user info: {e}")
        bot.send_message(chat_id=user_message.chat.id, text="❌ خطا در به‌روزرسانی اطلاعات کاربر.")


# Request config
@bot.message_handler(state=buy.request, content_types=['photo', 'text'])
def request_config(user_message):
    # Create Buttons
    first_button = telebot.types.InlineKeyboardButton("Send Config", callback_data='answer')
    back_button = telebot.types.InlineKeyboardButton("بازگشت به خانه 🏡", callback_data='BACK_HOME')

    glass_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    glass_markup.add(first_button)

    back_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    back_markup.add(back_button)

    if user_message.content_type == 'photo':
        caption = user_message.caption if user_message.caption is not None else ""
        bot.send_photo(chat_id=Keys.SUPPORT_ID, photo=user_message.photo[-1].file_id, caption=f"Recived a message from: {user_message.from_user.id}\nName: {user_message.from_user.first_name}\nUsername: @{user_message.from_user.username}\n\nMessage text:\n{escape_special_characters(caption)}", reply_markup=glass_markup)
        bot.send_message(chat_id=user_message.chat.id, text=Des.receipt_description, reply_markup=back_markup)
        Keys.texts[user_message.from_user.id] = {'type': 'photo', 'file_id': user_message.photo[-1].file_id, 'caption': caption}

    elif user_message.content_type == 'text':
        bot.send_message(chat_id=Keys.SUPPORT_ID, text=f"Recived a message from: {user_message.from_user.id}\nName: {user_message.from_user.first_name}\nUsername: @{user_message.from_user.username}\n\nMessage text:\n{escape_special_characters(user_message.text)}", reply_markup=glass_markup)
        bot.send_message(chat_id=user_message.chat.id, text=Des.receipt_description, reply_markup=back_markup)
        Keys.texts[user_message.from_user.id] = {'type': 'text', 'text': user_message.text}

    else:
        bot.send_message(chat_id=user_message.chat.id, text="❌ فقط متن یا عکس پذیرفته میشود. 📸")

    bot.delete_state(user_id=user_message.from_user.id, chat_id=user_message.chat.id)


# Respond config
@bot.message_handler(state=buy.respond, content_types=['photo', 'text'])
def respond_config(user_message):
    pattern = r"Send your answer to: \d+"
    user_id_match = int(re.findall(pattern=pattern, string=user_message.reply_to_message.text)[0].split()[4])
    
    if not user_id_match:
        bot.send_message(chat_id=user_message.chat.id, text="User ID not found.")
        return

    if user_message.content_type == 'photo':
        caption = user_message.caption if user_message.caption is not None else ""
        bot.send_message(chat_id=user_id_match, text="🛑 کانفیگ زیر را کپی کنید یا QR کد آن را با برنامه V2ray اسکن کنید")
        bot.send_photo(chat_id=user_id_match, photo=user_message.photo[-1].file_id, caption=caption)

    elif user_message.content_type == 'text':
        bot.send_message(chat_id=user_id_match, text="🛑 کانفیگ زیر را کپی کنید یا QR کد آن را با برنامه V2ray اسکن کنید")
        bot.send_message(chat_id=user_id_match, text=user_message.text)
    
    bot.send_message(chat_id=user_message.chat.id, text="Message sent to the user.")
    bot.delete_state(user_id=user_message.from_user.id, chat_id=user_message.chat.id)


# Message response
@bot.message_handler()
def message_response(user_message):
    response = Res.sample_responses(user_message)
    bot.send_message(user_message.chat.id, response)


# Starting the bot and adding the state filter as a custom filter
if __name__ == '__main__':
    bot.add_custom_filter(custom_filters.StateFilter(bot))

    logging.info('start pulling...')
    retry_delay = 5  # Initial delay in seconds

    while True:
        try:
            bot.polling()
        except requests.exceptions.ProxyError as e:
            logging.error(f"Proxy error: {e}")
            logging.info(f'Retrying in {retry_delay} seconds...')
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 300)  # Exponential backoff with a maximum delay of 5 minutes
        except requests.exceptions.RequestException as e:
            logging.error(f"Request exception: {e}")
            logging.info(f'Retrying in {retry_delay} seconds...')
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 300)  # Exponential backoff with a maximum delay of 5 minutes
        else:
            retry_delay = 5  # Reset delay after a successful polling
    logging.info('end pulling...')