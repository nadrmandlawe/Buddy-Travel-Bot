# # checklist_functions.py

import logging
from database import get_or_create_checklist, add_item_to_checklist, delete_item_from_checklist, update_item_status, get_checklists_collection
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from utils import translate

# Initialize logger
logger = logging.getLogger(__name__)

# State management for tracking user interactions
user_states = {}

def new_checklist(bot: TeleBot, call):
    chat_id = call.message.chat.id
    collection = get_checklists_collection()
    collection.delete_one({"chat_id": chat_id})
    # Create a new checklist with default items
    default_items = [
        {"name": translate(chat_id, "passport"), "status": "❌"},
        {"name": translate(chat_id, "tickets"), "status": "❌"},
        {"name": translate(chat_id, "boarding_pass"), "status": "❌"},
        {"name": translate(chat_id, "hotel_reservation"), "status": "❌"},
        {"name": translate(chat_id, "travel_insurance"), "status": "❌"}
    ]
    new_checklist = {"chat_id": chat_id, "items": default_items}
    collection.insert_one(new_checklist)
    bot.send_message(chat_id, translate(chat_id, 'confirm_new_checklist'))
    bot.answer_callback_query(call.id)  # Use call.id here


def checklist_response_call(bot: TeleBot , chat_id):
    markup = InlineKeyboardMarkup(row_width=1)  # Set row width to 1 for vertical layout
    show_checklist_btn = InlineKeyboardButton(translate(chat_id, 'show_checklist'), callback_data="show_checklist")
    new_checklist_btn = InlineKeyboardButton(translate(chat_id, 'start_checklist'), callback_data="start_new_checklist")
    no_thanks_btn = InlineKeyboardButton(translate(chat_id, 'maybe_later'), callback_data="no_thanks")
    markup.add(show_checklist_btn, new_checklist_btn, no_thanks_btn)
    bot.send_message(chat_id, translate(chat_id, 'assist_you'), reply_markup=markup)

def show_checklist(bot: TeleBot, chat_id):
    """Display the user's checklist."""
    checklist = get_or_create_checklist(chat_id)
    items = ""
    for item in checklist["items"]:
        if isinstance(item, dict) and "name" in item and "status" in item:
            icon = item["status"]  # Status should be stored as "✅" or "❌"
            items += f"- {icon} {item['name']}\n"
        else:
            logger.error(f"Invalid item format in checklist: {item}")
    bot.send_message(chat_id, f"{translate(chat_id, 'checklist')}\n{items}")

def ask_to_modify_checklist(bot: TeleBot, chat_id):
    """Prompt the user with options to modify the checklist."""
    markup = InlineKeyboardMarkup()
    add_btn = InlineKeyboardButton(f"➕ {translate(chat_id, 'add')}", callback_data="add_item")
    delete_btn = InlineKeyboardButton(f"🗑 {translate(chat_id, 'delete')}", callback_data="delete_item")
    update_status_btn = InlineKeyboardButton(f"🔄 {translate(chat_id, 'update')}", callback_data="update_status")
    keep_btn = InlineKeyboardButton(f"👌 {translate(chat_id, 'keep_as_is')}", callback_data="keep_as_is")
    markup.add(add_btn, delete_btn, update_status_btn, keep_btn)
    bot.send_message(chat_id, translate(chat_id, 'modify_checklist_prompt'), reply_markup=markup)

def handle_modify_checklist_response_callback(bot: TeleBot, call):
    """Handle user's response to modify the checklist."""
    chat_id = call.message.chat.id
    response = call.data

    if response == "add_item":
        bot.send_message(chat_id, translate(chat_id, 'send_item_add'))
        user_states[chat_id] = "waiting_for_item"
    elif response == "delete_item":
        bot.send_message(chat_id, translate(chat_id, 'send_item_delete'))
        user_states[chat_id] = "waiting_for_item_delete"
    elif response == "update_status":
        show_items_for_status_update(bot, chat_id)
        user_states[chat_id] = "waiting_for_status_update"
    else:
        bot.send_message(chat_id, translate(chat_id, 'checklist_unchanged'))
    bot.answer_callback_query(call.id)

def handle_item_addition(bot: TeleBot, message):
    """Handle the addition of a new item to the checklist."""
    chat_id = message.chat.id
    item = message.text.strip()
    if item:
        add_item_to_checklist(chat_id, item)
        bot.send_message(chat_id, f"{translate(chat_id, 'item_added')} '{item}'")
        show_checklist(bot, chat_id)
        ask_to_modify_checklist(bot, chat_id)
    else:
        bot.send_message(chat_id, translate(chat_id, 'specify_item_add'))
    user_states[chat_id] = None  # Reset the state

def handle_item_deletion(bot: TeleBot, message):
    """Handle the deletion of an item from the checklist."""
    chat_id = message.chat.id
    item = message.text.strip()
    if item:
        delete_item_from_checklist(chat_id, item)
        bot.send_message(chat_id, f"{translate(chat_id, 'item_removed')} '{item}'")
        show_checklist(bot, chat_id)
        ask_to_modify_checklist(bot, chat_id)
    else:
        bot.send_message(chat_id, translate(chat_id, 'specify_item_delete'))
    user_states[chat_id] = None  # Reset the state

def show_items_for_status_update(bot: TeleBot, chat_id):
    """Show items to the user for status update selection."""
    checklist = get_or_create_checklist(chat_id)
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    for item in checklist["items"]:
        if isinstance(item, dict) and "name" in item and "status" in item:
            button_text = f"{item['name']} ({item['status']})"
            markup.add(KeyboardButton(button_text))
    bot.send_message(chat_id, translate(chat_id, 'select_item_update'), reply_markup=markup)

def handle_status_change_callback(bot: TeleBot, call):
    """Handle the status change of an item."""
    chat_id = call.message.chat.id
    item_name = user_states[chat_id]["item_name"]

    if call.data == 'done':
        update_item_status(chat_id, item_name, "✅")  # Store the emoji directly
        bot.send_message(chat_id, f"{translate(chat_id, 'item_marked_done')} '{item_name}'")
    elif call.data == 'not_done':
        update_item_status(chat_id, item_name, "❌")  # Store the emoji directly
        bot.send_message(chat_id, f"{translate(chat_id, 'item_marked_not_done')} '{item_name}'")

    show_checklist(bot, chat_id)
    ask_to_modify_checklist(bot, chat_id)
    user_states[chat_id] = None  # Reset the state

def handle_status_update_selection(bot: TeleBot, message):
    """Handle the user's selection for updating item status."""
    chat_id = message.chat.id
    item_text = message.text.strip()
    item_name = item_text.split(" (")[0]

    markup = InlineKeyboardMarkup()
    mark_done_btn = InlineKeyboardButton(f"✅ {translate(chat_id, 'mark_done')}", callback_data='done')
    mark_not_done_btn = InlineKeyboardButton(f"❌ {translate(chat_id, 'mark_not_done')}", callback_data='not_done')
    markup.add(mark_done_btn, mark_not_done_btn)

    bot.send_message(chat_id, translate(chat_id, 'change_item_status').format(item_name=item_name), reply_markup=markup)
    user_states[chat_id] = {"state": "waiting_for_status_change", "item_name": item_name}
