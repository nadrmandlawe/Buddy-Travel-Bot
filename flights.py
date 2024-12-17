# flights.py

from serpapi import GoogleSearch
import config
import logging

logger = logging.getLogger(__name__)

def return_flights(departure_id, arrival_id, departure_date, return_date=None, departure_token=None, is_one_way=False, lang="en"):
    """
    Fetches flight information from Google Flights API based on the provided parameters.
    :param departure_id: The ID of the departure airport.
    :param arrival_id: The ID of the arrival airport.
    :param departure_date: The departure date.
    :param return_date: The return date (optional).
    :param departure_token: The departure token (optional).
    :param is_one_way: Boolean indicating if the flight is one-way.
    :return: A list of flights with their respective booking or departure tokens.
    """
    try:
        params = {
            "engine": "google_flights",
            "type": "2" if is_one_way else "1",
            "hl": {lang},
            "gl": "il",
            "currency": "USD",
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "outbound_date": departure_date,
            "api_key": config.GOOGLE_FLIGHTS_API
        }

        if not is_one_way and return_date:
            params["return_date"] = return_date

        if departure_token:
            params["departure_token"] = departure_token

        search = GoogleSearch(params)
        result = search.get_dict()

        flights = []
        best_flights = result.get("best_flights", [])
        other_flights = result.get("other_flights", [])

        for flight in best_flights:
            flight_info = {
                'flight': flight,
                'token': flight.get('departure_token', None) if not is_one_way else flight.get('booking_token', None)
            }
            flights.append(flight_info)

        for flight in other_flights:
            flight_info = {
                'flight': flight,
                'token': flight.get('departure_token', None) if not is_one_way else flight.get('booking_token', None)
            }
            flights.append(flight_info)

        logger.info(f"Fetched {len(flights)} flights for departure_id: {departure_id}, arrival_id: {arrival_id}")
        return flights

    except Exception as e:
        logger.exception(f"Error fetching flights for departure_id: {departure_id}, arrival_id: {arrival_id}: {e}")
        return None

def get_flight_with_booking_token(departure_id, arrival_id, departure_date, return_date, booking_token, is_one_way=False):
    """
    Fetches flight information from Google Flights API based on the provided booking token.

    :param departure_id: The ID of the departure airport.
    :param arrival_id: The ID of the arrival airport.
    :param departure_date: The departure date.
    :param return_date: The return date.
    :param booking_token: The booking token for the flight.
    :param is_one_way: Boolean indicating if the flight is one-way.
    :return: The flight information as a dictionary.
    """
    try:
        params = {
            "engine": "google_flights",
            "type": "2" if is_one_way else "1",
            "hl": "en",
            "gl": "il",
            "currency": "USD",
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "outbound_date": departure_date,
            "booking_token": booking_token,
            "api_key": config.GOOGLE_FLIGHTS_API
        }

        if not is_one_way and return_date:
            params["return_date"] = return_date

        search = GoogleSearch(params)
        result = search.get_dict()

        logger.info(f"Fetched flight details for booking_token: {booking_token}")
        return result

    except Exception as e:
        logger.exception(f"Error fetching flight details for booking_token: {booking_token}: {e}")
        return None