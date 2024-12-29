import locale
import re
from collections import defaultdict
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from config_handlers import load_config
from date_handlers import get_start_date, get_final_date, move_start_date_in_config_week_forward
from logger import logger

locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

PLANLOS_URL = "https://www.planlos-leipzig.org/"
SACHSENPUNK_URL = "https://sachsenpunk.de/dates/"
SONGKICK_URL = "https://www.songkick.com/metro-areas/28528-germany-leipzig"


def add_spaces(string: str) -> str:
    """
    Adds spaces between time and date in the string
    It applies in Planlos Leipzig events
    :param string:
    :return:
    """
    result = string
    pattern = r'([a-zA-ZÄÃ¤ÖÜäöüß-]+)(\d{2}\.)|(\d{1,2}:\d{2})(\d{2}.\d{2}.\d{4})'
    if re.search(pattern, string):
        result = re.sub(pattern, r'\1\3 \2\4', string)
    return result


def get_soup(url):
    """
    Fetches data from the given URL and returns BeautifulSoup object
    :param url:
    :return:
    """
    try:
        logger.info(f"Fetching data from {url}")
        r = requests.get(url)
        r.raise_for_status()
        logger.info(f"Data from {url} is fetched")
        return BeautifulSoup(r.content, 'html.parser')
    except RequestException as e:
        logger.error(f"An error occurred while fetching data from {url}: {str(e)}")
        return None


def get_entry_content(soup: BeautifulSoup):
    """
    Finds entry-content in the given soup
    :param soup:
    :return:
    """
    try:
        logger.info("Finding entry-content")
        return soup.find('div', {"class": "entry-content"})
    except AttributeError:
        logger.error("No entry-content found")
        return None


def get_website_content(url: str):
    soup = get_soup(url)
    if not soup:
        return None
    return get_entry_content(soup)


def get_planlos_events(start_date: datetime.date, final_date: datetime.date):
    """
    Fetches events from Planlos Leipzig
    :param start_date:
    :param final_date:
    :return:
    """
    logger.info("Getting events from Planlos Leipzig...")
    entry_content = get_website_content(PLANLOS_URL)
    if not entry_content:
        return {}
    try:
        logger.info("Finding h3 tags with dates")
        date_headers = entry_content.find_all('h3')
    except AttributeError:
        logger.error("No date_headers found")
        return {}

    events = defaultdict(list)
    logger.info("Parsing each date")
    for date_header in date_headers:
        logger.info(f"Parsing date date_header: {date_header.text}")
        current_date = datetime.strptime(date_header.text, "%a., %d. %B %Y").date()
        if current_date < start_date:
            logger.info(f"Skipping {current_date} because it is before the start date")
            continue
        if current_date >= final_date:
            logger.info(f"Breaking the loop because {current_date} is after the final date")
            break

        event_date = str(current_date)
        logger.info(f"Fetching events for {event_date}")
        next_tr = date_header.find_next("tr")
        while next_tr and next_tr.find("h3") is None:
            event_row = next_tr
            event_cells = event_row.find_all("td")
            time_cell = event_cells[0]
            event_cell = event_cells[1]
            if event_cell.em:
                place = event_cell.em.text
            else:
                place = ""
            event = {
                "name": event_cell.a.text.strip(),
                "place": place,
                "time": add_spaces(time_cell.text.strip()),
                "URL": event_cell.a.get("href")
            }
            logger.info(f"Event is fetched")
            events[event_date].append(event)
            next_tr = event_row.find_next("tr")
    logger.info("Events from Planlos Leipzig are fetched")
    return events


def get_sachsenpunk_events(start_date: datetime.date, final_date: datetime.date):
    """
    Fetches events from Sachsenpunk
    :param start_date:
    :param final_date:
    :return:
    """
    logger.info("Getting events from Sachsenpunk...")
    entry_content = get_website_content(SACHSENPUNK_URL)
    if not entry_content:
        return {}
    try:
        logger.info("Finding p tags")
        p_tags = entry_content.find_all('p')
    except AttributeError:
        logger.error("No p tags found")
        return {}
    events = defaultdict(list)
    year_now = datetime.now().year
    month_now = datetime.now().month
    previous_month = 0
    year = year_now

    for p in p_tags:
        logger.info(f"Parsing p tag")
        if re.match(r"\d+\.\d+\.", p.text):
            logger.info("Checking if there is announcement for the new year")
            # Checking if there is announcement for the new year
            current_month = int(p.text[3:5])
            if current_month < previous_month or (month_now == 12 and current_month == 1):
                logger.info("Announcement for the new year is found")
                year = year_now + 1
            previous_month = current_month

            date_str = p.text[:6] + str(year)
            current_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            logger.info(f"Current date: {current_date}")
            if current_date < start_date:
                logger.info(f"Skipping {current_date} because it is before the start date")
                continue
            if current_date >= final_date:
                logger.info(f"Breaking the loop because {current_date} is after the final date")
                break

            events_date = str(current_date)
            current_events = p.find_next('p').text.split("\n")
            for event in current_events:
                logger.info(f"Event: {event} is fetched")
                if "Leipzig" in event:
                    logger.info("Checking if the event is in Leipzig")
                    event_str = event.lstrip("Leipzig – ")
                    events[events_date].append(event_str)
                    logger.info(f"Event: {event_str} is added to the events")
    logger.info("Events from Sachsenpunk are fetched")
    return events


def get_full_songkick_url(ending: str) -> str:
    """
    Returns full URL from the ending
    :param ending:
    :return:
    """
    return "https://www.songkick.com" + ending


def get_songkick_events(start_date: datetime.date, final_date: datetime.date):
    """
    Fetches events from Songkick
    :param start_date:
    :param final_date:
    :return:
    """
    logger.info("Getting events from Songkick...")
    soup = get_soup(SONGKICK_URL)
    if not soup:
        return {}
    try:
        logger.info("Finding event-listings-element")
        event_elements = soup.find_all('li', {"class": "event-listings-element"})
    except AttributeError:
        logger.error("No event-listings-element found")
        return {}
    events = defaultdict(list)
    for event_element in event_elements:
        logger.info("Parsing event element")
        event = {}
        time_tag = event_element.find("time")
        datetime_property = time_tag['datetime']
        if len(datetime_property) == 10:
            current_datetime = datetime.strptime(datetime_property, "%Y-%m-%d")
            time_str = None
        else:
            current_datetime = datetime.strptime(datetime_property, "%Y-%m-%dT%H:%M:%S%z")
            time_str = current_datetime.strftime("%H:%M")

        current_date = current_datetime.date()
        logger.info(f"Current date: {current_date}")
        if current_date < start_date:
            logger.info(f"Skipping {current_date} because it is before the start date")
            continue
        if current_date >= final_date:
            logger.info(f"Breaking the loop because {current_date} is after the final date")
            break

        date_str = str(current_datetime.date())
        events[date_str].append(event)
        event['time'] = time_str
        try:
            logger.info("Finding div with artist and venue location")
            div_artist = event_element.find('div', {"class": "artists-venue-location-wrapper"})
        except AttributeError:
            logger.error("No div with artist and venue location found")
            continue
        try:
            logger.info("Finding event-link and venue-link")
            event_link = div_artist.find('a', {"class": "event-link"})
            venue_link = div_artist.find('a', {"class": "venue-link"})
        except AttributeError:
            logger.error("No event-link and venue-link found")
            continue
        try:
            logger.info("Finding event name")
            event_name = div_artist.strong.text
        except AttributeError:
            logger.error("No event name found")
            continue
        event_url = get_full_songkick_url(event_link['href'])
        event['name'] = event_name
        event['URL'] = event_url
        venue_name = None
        venue_url = None

        if venue_link:
            venue_url = get_full_songkick_url(venue_link['href'])
            venue_name = venue_link.text
        event['venue_name'] = venue_name
        event['venue_URL'] = venue_url
        logger.info(f"Event: {event} is fetched")
    logger.info("Events from Songkick are fetched")
    return events


def get_all_events() -> dict:
    logger.info("Getting all events...")
    logger.info("Loading config")
    config = load_config()
    start_date = get_start_date(config)
    final_date = get_final_date(config)

    events = {
        "planlos": get_planlos_events(start_date, final_date),
        "sachsenpunk": get_sachsenpunk_events(start_date, final_date),
        "songkick": get_songkick_events(start_date, final_date)
    }
    move_start_date__forward = config["move_start_date_week_forward_after_parsing"]
    if move_start_date__forward:
        logger.info("Moving start date in config week forward")
        move_start_date_in_config_week_forward()
    logger.info("All events are fetched")
    return events
