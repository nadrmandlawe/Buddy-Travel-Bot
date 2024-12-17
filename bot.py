# bot.py

import logging
import threading
import time
from datetime import datetime
from dateutil import parser
import telebot
from config import TELEGRAM_TOKEN
from gemini import get_airports, recommend_attractions_and_tips
from searchflight import search_details, handle_flight_search, flight_results, handle_booking_search,format_flight_details
from checklist_functions import (
    show_checklist, ask_to_modify_checklist, handle_modify_checklist_response_callback,
    handle_item_addition, handle_item_deletion, handle_status_change_callback,
    handle_status_update_selection, user_states, new_checklist, checklist_response_call
)
from utils import get_language, set_language, translate

# Initialize the bot with your token
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Setup logging
logging.basicConfig(
    format="[%(levelname)s %(lineno)d] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

user_state = {}

# Define the /start and /help command handlers
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message: telebot.types.Message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(telebot.types.KeyboardButton('🇺🇲 English'), telebot.types.KeyboardButton('עברית 🇮🇱'), telebot.types.KeyboardButton('🇷🇺 Русский'),telebot.types.KeyboardButton('العربية 🇸🇦'))
    bot.send_message(chat_id, "Please choose your language  \n אנא בחר את שפתך  \n الرجاء اختيار لغة \n Пожалуйста, выберите язык   ", reply_markup=markup)

# Handle language selection
@bot.message_handler(func=lambda message: message.text in ['🇺🇲 English','🇷🇺 Русский' , 'עברית 🇮🇱','العربية 🇸🇦'])
def set_user_language(message: telebot.types.Message):
    chat_id = message.chat.id
    if message.text == '🇺🇲 English':
        set_language(chat_id, 'en')
    elif message.text == 'עברית 🇮🇱':
        set_language(chat_id, 'he')
    elif message.text == '🇷🇺 Русский':
        set_language(chat_id, 'ru')
    elif message.text == 'العربية 🇸🇦':
        set_language(chat_id, 'ar')

    lang = get_language(chat_id)
    welcome_message = translate(chat_id, 'welcome_message')
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        telebot.types.InlineKeyboardButton(translate(chat_id, 'flight_tickets'), callback_data="search_flight"),
        telebot.types.InlineKeyboardButton(translate(chat_id, 'checklist_journey'), callback_data="checklist"),
        telebot.types.InlineKeyboardButton(translate(chat_id, 'dest_recommend'), callback_data="ask_destination")
    )
    cover_image_path = './assets/cover.webp'
    with open(cover_image_path, 'rb') as photo:
        bot.send_photo(chat_id, photo, caption=welcome_message, reply_markup=markup)

# Define the /checklist command handler
@bot.message_handler(commands=['checklist'])
def handle_checklist(message: telebot.types.Message):
    chat_id = message.chat.id
    lang = get_language(chat_id)
    checklist_prompt = translate(chat_id, 'checklist_prompt')

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton(translate(chat_id, 'show_checklist'), callback_data="show_checklist"),
        telebot.types.InlineKeyboardButton(translate(chat_id, 'start_checklist'), callback_data="start_new_checklist"),
    )

    bot.send_message(chat_id, checklist_prompt, reply_markup=markup)
    user_states[chat_id] = "waiting_for_checklist_response"





@bot.message_handler(commands=['language'])
def handle_language(message: telebot.types.Message):
    chat_id = message.chat.id
    language_selection_prompt = translate(chat_id, 'language_selection_prompt')
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(telebot.types.KeyboardButton('🇺🇲 English'), telebot.types.KeyboardButton('עברית 🇮🇱'), telebot.types.KeyboardButton('🇷🇺 Русский'), telebot.types.KeyboardButton('العربية 🇸🇦'))
    bot.send_message(chat_id, language_selection_prompt, reply_markup=markup)

# Define the /recommendations command handler
@bot.message_handler(commands=['recommendations'])
def handle_recommendations(message: telebot.types.Message):
    chat_id = message.chat.id
    lang = get_language(chat_id)
    bot.send_message(chat_id, translate(chat_id, 'ask_destination'))
    bot.register_next_step_handler(message, handle_destination_input)

# Define the /searchflight command handler
@bot.message_handler(commands=['searchflight'])
def search_flight(message: telebot.types.Message):
    chat_id = message.chat.id
    username = message.from_user.username
    logger.info(f"> New flight search at #{chat_id}. username: {username}")
    bot.send_message(chat_id,translate(chat_id, 'flight_search_details'))
    user_state[chat_id] = 'waiting_for_flight_details'

# Handle incoming messages for flight search details
@bot.message_handler(func=lambda message: user_state.get(message.chat.id) in ['waiting_for_flight_details'])
def handle_message(message: telebot.types.Message):
    chat_id = message.chat.id
    username = message.from_user.username
    text = message.text
    logger.info(f"= Got on chat #{chat_id}/{username!r}: {text!r}")

    if user_state.get(chat_id) == 'waiting_for_flight_details':
        flight_details = [detail.strip() for detail in text.split(",")]

        if len(flight_details) not in [3, 4]:
            bot.send_message(chat_id,translate(chat_id, 'provide_all_details_warning'))
            return

        departure_city, arrival_city = flight_details[:2]

        try:
            departure_date = parser.parse(flight_details[2], dayfirst=True)
            return_date = parser.parse(flight_details[3], dayfirst=True).strftime('%Y-%m-%d') if len(
                flight_details) == 4 else None

            if return_date and departure_date > parser.parse(return_date):
                bot.send_message(chat_id, translate(chat_id, 'arrival_date_warning'))
                return

        except ValueError:
            bot.send_message(chat_id, translate(chat_id, 'correct_format_warning'))
            return

        if departure_date < datetime.now():
            bot.send_message(chat_id, translate(chat_id, 'departure_date_warning'))
            return

        departure_id, arrival_id = get_airports(departure_city), get_airports(arrival_city)

        if departure_id == "NO_RESULT" or arrival_id == "NO_RESULT":
            bot.send_message(chat_id,
                             f"translate(chat_id, 'airport_not_found_warning') {departure_city if departure_id == 'NO_RESULT' else arrival_city}.")
            return

        search_details[chat_id] = {
            "departure_city": departure_city,
            "arrival_city": arrival_city,
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "departure_date": departure_date.strftime('%Y-%m-%d'),
            "return_date": return_date,
            "is_one_way": len(flight_details) == 3
        }
        handle_flight_search(bot, chat_id, departure_id, arrival_id, departure_date.strftime('%Y-%m-%d'), return_date)

        user_state[chat_id] = None
    # else:
    #     bot.send_message(chat_id, "Please use the /help command to see the list of the commands.",
    #                      parse_mode='Markdown')

# Define the callback query handler for button presses
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    lang = get_language(chat_id)
    if call.data == "search_flight":
        # Trigger the search_flight command when the inline button is pressed
        search_flight(call.message)
    elif call.data == "checklist":
        # Call checklist_response_call to prompt the user
        checklist_response_call(bot, chat_id)
        # Set user state to indicate waiting for checklist response
        user_states[chat_id] = "waiting_for_checklist_response"
    elif call.data == "show_checklist":
        if user_states.get(chat_id) == "waiting_for_checklist_response":
            show_checklist(bot, chat_id)
            ask_to_modify_checklist(bot, chat_id)
            user_states[chat_id] = None  # Reset the state

    elif call.data == "start_new_checklist":
        if user_states.get(chat_id) == "waiting_for_checklist_response":
            new_checklist(bot, call)
            show_checklist(bot, chat_id)
            ask_to_modify_checklist(bot, chat_id)
            user_states[chat_id] = None  # Reset the state
        else:
            bot.send_message(chat_id, "Alright! If you need anything else, just let me know.")
        # show_checklist(bot, chat_id)
        # ask_to_modify_checklist(bot, chat_id)
    elif call.data == "ask_destination":
        bot.send_message(chat_id, translate(chat_id, 'ask_destination'))
        bot.register_next_step_handler(call.message, handle_destination_input)
    elif call.data in ["add_item", "delete_item", "update_status", "keep_as_is"]:
        handle_modify_checklist_response_callback(bot, call)
    elif call.data in ["done", "not_done"]:
        handle_status_change_callback(bot, call)
    elif call.data.startswith('flight_'):
        handle_flight_selection(call)


# Handle the checklist modification response
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) in ["waiting_for_item", "waiting_for_item_delete"])
def handle_modify_item(message):
    state = user_states.get(message.chat.id)
    if state == "waiting_for_item":
        handle_item_addition(bot, message)
    elif state == "waiting_for_item_delete":
        handle_item_deletion(bot, message)

# Handle the status update selection
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_status_update")
def handle_update_status(message):
    handle_status_update_selection(bot, message)

# Handle user input for destination recommendations
def handle_destination_input(message):
    chat_id = message.chat.id
    lang = get_language(chat_id)
    destination = message.text.strip()
    if destination:
        threading.Thread(target=send_recommendation, args=(chat_id, destination, lang)).start()
    else:
        bot.send_message(chat_id, translate(chat_id, 'invalid_destination'))

    # send_recommendation(chat_id, destination, lang)


def send_recommendation(chat_id, destination, lang):
    logger.info(f"Getting recommendation for {destination!r}")
    t0 = time.perf_counter()
    message_id = bot.send_message(chat_id, translate(chat_id, 'loading_recommendations')).id
    recommendations = recommend_attractions_and_tips(destination, lang)
    t = time.perf_counter() - t0
    logger.info(f"Got recommendation for {destination!r} in {t:.1f} s")
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=recommendations, parse_mode='HTML')


# Handle flight selection
@bot.callback_query_handler(func=lambda call: call.data.startswith('flight_'))
def handle_flight_selection(call):
    """
    Handles the flight selection from the inline keyboard and displays flight details, followed by booking options.
    """
    try:
        chat_id = call.message.chat.id
        data_parts = call.data.split('_')
        flight_index = int(data_parts[1])

        flight_info = flight_results[chat_id][flight_index]['flight']
        search_detail = search_details[chat_id]
        is_one_way = search_detail["is_one_way"]

        flight_details = format_flight_details(flight_info, chat_id)
        bot.send_message(chat_id, flight_details, parse_mode='HTML')

        search_type = data_parts[2]
        token = None

        if search_type == "depart":
            if is_one_way:
                token = flight_info.get('booking_token')
                if token:
                    handle_booking_search(bot, chat_id, token, is_one_way=True)
                else:
                    logger.error(chat_id, "Booking token not found for this flight.")
                    logger.error("Booking token not found for one-way flight in chat #%s", chat_id)
            else:
                token = flight_info.get('departure_token')
                if token:
                    handle_flight_search(bot, chat_id, search_detail["departure_id"], search_detail["arrival_id"],
                                         search_detail["departure_date"], search_detail["return_date"], token)
                else:
                    logger.error(chat_id, "Departure token not found for this flight.")
                    logger.error("Departure token not found for return flight in chat #%s", chat_id)
        elif search_type == "return":
            token = flight_info.get('booking_token')
            if token:
                handle_booking_search(bot, chat_id, token, is_one_way)
            else:
                logger.error(chat_id, "Booking token not found for this flight.")
                logger.error("Booking token not found for return flight in chat #%s", chat_id)
    except Exception as e:
        bot.send_message(chat_id, translate(chat_id, 'unexpected_error'))
        logger.exception("Unexpected error in handle_flight_selection: %s", e)

# Start the bot
if __name__ == "__main__":
    logger.info("* Start polling...")
    bot.infinity_polling()
    logger.info("* Bye!")
