# gemini.py

import logging

import google.generativeai as genai
from config import GEMINI_API_KEY
from translations import translations

logger = logging.getLogger(__name__)

# Configure the SDK with your API key
genai.configure(api_key=GEMINI_API_KEY)
model_name = 'gemini-1.5-flash'
model = genai.GenerativeModel(model_name)


def generate_content(prompt):
    """Generate content using the Gemini Flash 1.5 model."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating content: {e}")
        return None


def suggest_items_for_destination(destination, lang='en'):
    """Generate suggested items for a travel checklist based on destination."""
    if lang == 'he':
        prompt = f"אנא הצע פריטים חיוניים לארוז לטיול ל{destination}."
    else:
        prompt = f"Suggest essential items to pack for a trip to {destination}."

    response_text = generate_content(prompt)
    if response_text:
        # Assuming the response text is a list of items separated by newlines
        suggestions = response_text.split('\n')
        return [item.strip() for item in suggestions if item.strip()]
    return []


def recommend_attractions_and_tips(destination, lang='en'):
    """Generate travel recommendations and tips for a destination."""
    prompt = (f"Provide top attractions and travel tips for {destination}. Please, use this language (locale) - {lang}."
              f"Format the response in HTML suitable for Telegram. AVOID USING MARKDOWN"
              f"Use only the following HTML tags: <b>, <i>, <a>. "
              f"AVOID USING NEXT TAGS: br, html, head, title, body, div, span, img, table, ul, ol, li, p."
              f"The output should be a Telegram message, not a full HTML page. Please, use emoji")

    response_text = generate_content(prompt)
    if response_text:
        return response_text
    return translations[lang].get('no_recommendations', "No recommendations available at the moment.")


def get_airports(city: str) -> str:
    """
    This function returns IATA code of airports in the city. You can use name of country or IATA code as well.
    :param city: City for search
    :return: IATA codes separated by comma or NO_RESULT if no results are found.
    """
    try:
        response = model.generate_content(
            f"Provide a comma-separated list of 3-letter IATA codes for the top airports in {city}. "
            f"Return \"NO_RESULT\" if no results are found. If you got airport code instead of city or country - just"
            f"return it. If you got country instead of city - provide codes of top-3 airports in this country. Avoid to"
            f"use any other words and symbols. Only IATA codes separated by comma."
        )
        logger.debug(f"Response: {response}")
        if not response or not response.candidates:
            return ""

        content = response.candidates[0].content
        if not content or not content.parts:
            return ""

        return content.parts[0].text

    except IndexError as e:
        logger.error(f"IndexError: {e}. The response might be malformed or empty.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

    return ""
