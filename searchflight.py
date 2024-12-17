# searchflights.py

import logging
from datetime import datetime

from utils import is_nested_empty, get_language, translate
from flights import return_flights, get_flight_with_booking_token
from telebot import types

logger = logging.getLogger(__name__)

airport_codes = {}
flight_results = {}
search_details = {}

def format_flight_details(flight, chat_id):
    try:
        segments = flight['flights']
        price = flight['price']
        total_duration = flight['total_duration']
        layovers = flight.get('layovers', [])
        stops_info = ""

        if layovers:
            stops_info = f"<b>{translate(chat_id, "layovers")}:</b>\n"
            for layover in layovers:
                stops_info += (f"• {layover['name']} ({layover['id']}), Duration: {layover['duration']} mins "
                               f"{f'({translate(chat_id, "overnight")})' if layover.get('overnight') else ''}\n")

        details = (f"<b>{translate(chat_id, "airline")}:</b> {segments[0]['airline']}\n"
                   f"<b>{translate(chat_id, "total_duration")}:</b> {total_duration} mins\n"
                   f"<b>{translate(chat_id, price)}:</b> ${price}\n"
                   f"{stops_info}\n"
                   f"<b>{translate(chat_id, "flights")}:</b>\n")

        for segment in segments:
            details += (f"\n<b>{segment['airline']} {segment['flight_number']}</b>\n"
                        f"{translate(chat_id, "from")}: {segment['departure_airport']['name']} ({segment['departure_airport']['id']})\n"
                        f"{translate(chat_id, "to")}: {segment['arrival_airport']['name']} ({segment['arrival_airport']['id']})\n"
                        f"{translate(chat_id, "departure")}: {datetime.strptime(segment['departure_airport']['time'], '%Y-%m-%d %H:%M').strftime('%d.%m.%Y %H:%M')}\n"
                        f"{translate(chat_id, "arrival")}: {datetime.strptime(segment['arrival_airport']['time'], '%Y-%m-%d %H:%M').strftime('%d.%m.%Y %H:%M')}\n"
                        f"{translate(chat_id, "duration")}: {segment['duration']} {translate(chat_id, "mins")}\n"
                        f"{translate(chat_id, "travel_class")}: {segment['travel_class']}\n"
                        f"{translate(chat_id, "legroom")}: {segment.get('legroom', 'N/A')}\n"
                        f"{translate(chat_id, "extensions")}: {', '.join(segment.get('extensions', []))}\n"
                        f"{f'({translate(chat_id, "often_delayed_by_over_30_min")})' if segment.get('often_delayed_by_over_30_min') else ''}\n"
                        f"{f'({translate(chat_id, "overnight")})' if segment.get('overnight') else ''}\n")

        return details

    except KeyError as e:
        logger.error("KeyError in format_flight_details: %s", e)
        return "Error in fetching flight details"



def handle_flight_search(bot, chat_id, departure_id, arrival_id, departure_date, return_date=None,
                         departure_token=None):
    """
    Handles the flight search process and sends the results to the user.

    :param bot: The Telegram bot instance.
    :param chat_id: The chat ID to send the messages to.
    :param departure_id: The ID of the departure airport.
    :param arrival_id: The ID of the arrival airport.
    :param departure_date: The departure date.
    :param return_date: The return date (optional).
    :param departure_token: The departure token (optional).
    """
    try:
        search_detail = search_details.get(chat_id)
        if not search_detail:
            bot.send_message(chat_id, {translate(chat_id, "no_search_details")})
            logger.error("Search details not found for chat_id: %s", chat_id)
            return

        departure_city = search_detail.get("departure_city")
        arrival_city = search_detail.get("arrival_city")
        is_one_way = search_detail.get("is_one_way", False)

        search_message = (f"{translate(chat_id, "searching")} {arrival_city} {translate(chat_id, "to")} {departure_city} {translate(chat_id, "on")} {return_date}..."
                          if departure_token else
                          f"{translate(chat_id, "searching_for")} {translate(chat_id, "one_way") if is_one_way else ''}{translate(chat_id, "flights_from")} {departure_city} {translate(chat_id, "to")} {arrival_city} "
                          f"{translate(chat_id, "on")} {departure_date} {f'{translate(chat_id, "until")} {return_date}' if return_date else ''}...")

        bot.send_message(chat_id, search_message)
        logger.info("Started flight search: %s", search_message)
        flights = return_flights(departure_id, arrival_id, departure_date, return_date, departure_token=departure_token,
                                 is_one_way=is_one_way, lang=get_language(chat_id))
        if flights is None:
            bot.send_message(chat_id, translate(chat_id, "error_fetching_flights"))
            logger.error("Error occurred while fetching flights for chat_id: %s", chat_id)
            return

        send_flight_results(bot, chat_id, flights)
    except Exception as e:
        bot.send_message(chat_id, translate(chat_id, "unexpected_error_flights"))
        logger.exception("Unexpected error in handle_flight_search: %s", e)


def get_airport_name_from_flight(flight, is_departure=True):
    """
    Retrieves the airport name from a flight segment and caches it.

    :param flight: The flight segment information.
    :param is_departure: Boolean indicating if the airport is the departure airport.
    :return: The airport name.
    """
    try:
        segment = flight['flights'][0]
        airport_code = segment['departure_airport']['id'] if is_departure else segment['arrival_airport']['id']
        airport_name = segment['departure_airport']['name'] if is_departure else segment['arrival_airport']['name']

        if airport_code not in airport_codes:
            airport_codes[airport_code] = airport_name

        return airport_codes[airport_code]
    except KeyError as e:
        logger.error("KeyError in get_airport_name_from_flight: %s", e)
        return "Unknown"


def send_flight_results(bot, chat_id, flights):
    """
    Sends the flight search results to the user.

    :param bot: The Telegram bot instance.
    :param chat_id: The chat ID to send the messages to.
    :param flights: The flight search results.
    """
    try:
        if not is_nested_empty(flights):
            flight_results[chat_id] = flights

            keyboard = types.InlineKeyboardMarkup()
            main_airports = set()

            for i, flight_info in enumerate(flight_results[chat_id]):
                flight = flight_info['flight']
                segments = flight['flights']
                price = flight['price']

                departure_airport_code = segments[0]['departure_airport']['id']
                arrival_airport_code = segments[-1]['arrival_airport']['id']
                departure_time = segments[0]['departure_airport']['time']
                arrival_time = segments[-1]['arrival_airport']['time']

                get_airport_name_from_flight({'flights': [segments[0]]}, is_departure=True)
                get_airport_name_from_flight({'flights': [segments[-1]]}, is_departure=False)
                main_airports.add(departure_airport_code)
                main_airports.add(arrival_airport_code)

                num_of_stops = len(segments) - 1
                stops_indicator = f" ({num_of_stops})" if num_of_stops > 0 else ""

                button_text = (
                    f"🗓️ {departure_airport_code} - {arrival_airport_code}"
                    f" 🛫 {datetime.strptime(departure_time, '%Y-%m-%d %H:%M').strftime('%H:%M')}"
                    # f"🛬 {datetime.strptime(arrival_time, '%Y-%m-%d %H:%M').strftime('%d.%m.%y %H:%M')}\n"
                    f" | ${price}"
                )

                callback_data = f"flight_{i}_depart" if flight_info['token'] and flight_info['token'].startswith(
                    "WyJ") else f"flight_{i}_return"
                button = types.InlineKeyboardButton(text=button_text, callback_data=callback_data)
                keyboard.add(button)

            airport_info = "\n".join(
                [f"• {code} - {name}" for code, name in airport_codes.items() if code in main_airports])

            bot.send_message(chat_id,
                             f"✈️ <b>{translate(chat_id, "available_flights")}:</b>\n\n{airport_info}\n\n(1), (2), {translate(chat_id, "etc")}. - {translate(chat_id, "number_of_stops")}",
                             parse_mode='HTML', reply_markup=keyboard)
            logger.info("Sent flight results to chat_id: %s", chat_id)
        else:
            bot.send_message(chat_id,
                             translate(chat_id, "flights_didnt_find"),
                             parse_mode='HTML')
            logger.info("No flights found for chat_id: %s", chat_id)
    except Exception as e:
        bot.send_message(chat_id, translate(chat_id, "unexpected_error_flights"))
        logger.exception("Unexpected error in send_flight_results: %s", e)


def handle_booking_search(bot, chat_id, booking_token, is_one_way=False):
    """
    Handles the booking search process and sends the booking details to the user.

    :param bot: The Telegram bot instance.
    :param chat_id: The chat ID to send the messages to.
    :param booking_token: The booking token to search for.
    :param is_one_way: Boolean indicating if the booking is for a one-way flight.
    """
    try:
        search_detail = search_details.get(chat_id)
        if not search_detail:
            bot.send_message(chat_id, translate(chat_id, "no_search_details"))
            logger.error("Search details not found for chat_id: %s", chat_id)
            return

        departure_id = search_detail.get("departure_id")
        arrival_id = search_detail.get("arrival_id")
        departure_date = search_detail.get("departure_date")
        return_date = search_detail.get("return_date")

        bot.send_message(chat_id, translate(chat_id, "searching_booking"))
        logger.info("Started booking search for chat_id: %s", chat_id)

        flights = get_flight_with_booking_token(departure_id, arrival_id, departure_date, return_date, booking_token,
                                                is_one_way)
        if flights is None:
            bot.send_message(chat_id, {translate(chat_id, "error_fetching_booking")})
            logger.error("Error occurred while fetching booking details for chat_id: %s", chat_id)
            return

        prettify_html_file = flights.get("search_metadata", {}).get("prettify_html_file")
        if prettify_html_file:
            bot.send_message(chat_id, f"{translate(chat_id, "booking_details")}: {prettify_html_file}")
        else:
            logger.info("No prettify_html_file found for chat_id: %s", chat_id)
    except Exception as e:
        bot.send_message(chat_id, translate(chat_id, "unexpected_error_flights"))
        logger.exception("Unexpected error in handle_booking_search: %s", e)
