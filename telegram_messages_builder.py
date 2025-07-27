from datetime import datetime
from parsers import get_all_events
from itertools import chain
from logger import logger
import html


CALENDAR_SYMBOL = '🗓'
BULLET_SYMBOL = '🔹'
URL_SYMBOL = '🔗'
LOCATION_SYMBOL = '📍 '

def escape_html_text(text):
    """Escapes HTML special characters in the given text"""
    return html.escape(text) if text else text


def make_hyperlink_part(url, resource_name, symbol=URL_SYMBOL):
    """Returns a string with a hyperlink to the given URL For use in Telegram messages"""
    return f"{symbol}<a href=\"{url}\">{resource_name}</a>"


def make_strings_for_planlos(events: list[dict]) -> list[str]:
    """
    Returns a list of strings on Planlos Leipzig events for a given date in a format suitable for Telegram messages
    :param events:
    :return:
    """
    logger.info(f"Making strings for Planlos events")
    output_strings = []
    for event in events:
        time = event['time']
        name = event['name']
        if not name:
            logger.warning(f"Event name is missing for {event}")
            continue
        else:
            name = escape_html_text(name)
        place = escape_html_text(event['place'])
        url = event['URL']
        if place:
            place_part = f"\n{LOCATION_SYMBOL}{place}"
        else:
            place_part = ""
        hyperlink_part = make_hyperlink_part(url, 'event link')
        output_strings.append(f"""\
{BULLET_SYMBOL} <b>{time}:</b>
{name}{place_part}
{hyperlink_part}\n\n""")
    return output_strings


def make_strings_for_sachsen_punk(events: list[str]) -> list[str]:
    """
    Returns a list of strings on Sachsen Punk events for a given date in a format suitable for Telegram messages
    :param events:
    :return:
    """
    logger.info(f"Making strings for Sachsen Punk events")
    return [f"{BULLET_SYMBOL} {escape_html_text(event)}\n\n" for event in events]


def make_strings_for_songkick(events: list[dict]) -> list[str]:
    """
    Returns a list of strings on Songkick events for a given date in a format suitable for Telegram messages
    :param events:
    :return:
    """
    logger.info(f"Making strings for Songkick events")
    output_strings = []
    for event in events:
        output_strings.append(f'{BULLET_SYMBOL} ')
        name = event.get('name')
        if not name:
            logger.warning(f"Event name is missing for {event}")
            continue
        else:
            name = escape_html_text(name)
        time = event.get('time')
        venue_url = event.get('venue_URL')
        venue_name = event.get('venue_name')
        if time:
            output_strings.append(f"<b>{time}:</b> ")
        output_strings.append(f"{name}\n")
        if venue_url and venue_name:
            venue_name = escape_html_text(venue_name)
            venue_hyperlink_part = make_hyperlink_part(venue_url, venue_name, LOCATION_SYMBOL)
            output_strings.append(f'{venue_hyperlink_part}   ')
        event_url = event.get("URL")
        if event_url:
            output_strings.append(f" {make_hyperlink_part(event_url, ' event link')}\n\n")
    return output_strings


def messages_generator():
    """
    Generates messages for each date with events from all sources
    :return:
    """
    all_events = get_all_events()
    planlos_events, sachsenpunk_events, songkick_events = all_events.values()
    all_dates = list(set(chain(planlos_events, sachsenpunk_events, songkick_events)))
    all_dates.sort()
    events_dicts_handlers = {
        "🏴 Planlos Leipzig": (planlos_events, make_strings_for_planlos),
        "🤘 Sachsen Punk": (sachsenpunk_events, make_strings_for_sachsen_punk),
        "🎵 Songkick": (songkick_events, make_strings_for_songkick)
    }
    for date in all_dates:
        logger.info(f"Generating message for {date}")
        all_strings = []
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_str = date_obj.strftime("%A, %B %d, %Y")
        all_strings.append(f"{CALENDAR_SYMBOL} {date_str}\n\n")

        for name, (events_dict, handler) in events_dicts_handlers.items():
            if date in events_dict:
                all_strings.append(f"<b>{name}</b>\n")
                all_strings += handler(events_dict[date])
                all_strings.append("\n")
        message_text = ''.join(all_strings)
        logger.info(f"Message for {date} generated successfully with {len(message_text)} characters")
        yield date, message_text


def create_files():
    """
    Creates files with messages for each date
    :return:
    """
    logger.info("Creating files with messages")
    dates_and_messages = messages_generator()
    for date, message in dates_and_messages:
        with open(f"tg_messages/{date}", 'w', encoding='UTF-8') as f:
            logger.info(f"Writing message for {date} to file {f.name}")
            f.write(message)


if __name__ == '__main__':
    create_files()
