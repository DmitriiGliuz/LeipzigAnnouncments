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
    result = string
    pattern = r'([a-zA-ZÄÃ¤ÖÜäöüß-]+)(\d{2}\.)|(\d{1,2}:\d{2})(\d{2}.\d{2}.\d{4})'
    if re.search(pattern, string):
        result = re.sub(pattern, r'\1\3 \2\4', string)
    return result


def get_soup(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        return BeautifulSoup(r.content, 'html.parser')
    except RequestException as e:
        logger.error(f"An error occurred while fetching data from {url}: {str(e)}")
        return None


def get_planlos_events(start_date: datetime.date, final_date: datetime.date):
    logger.info("Getting events from Planlos Leipzig...")
    soup = get_soup(PLANLOS_URL)
    if not soup:
        logger.error("No data from Planlos Leipzig")
        return {}
    try:
        entry_content = soup.find('div', {"class": "entry-content"})
    except AttributeError:
        logger.error("No entry-content found")
        return
    try:
        headers = entry_content.find_all('h3')
    except AttributeError:
        logger.error("No headers found")
        return

    events = defaultdict(list)

    for header in headers:
        logger.debug("Header:")
        logger.debug(header)
        current_date = datetime.strptime(header.text, "%a, %d. %B %Y").date()
        if current_date < start_date:
            continue
        if current_date >= final_date:
            break

        event_date = str(current_date)
        logger.info(f"Fetching events for {event_date}")
        next_tr = header.find_next("tr")
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
            events[event_date].append(event)
            next_tr = event_row.find_next("tr")
    logger.info("Events from Planlos Leipzig are fetched")
    return events


def get_sachsenpunk_events(start_date: datetime.date, final_date: datetime.date):
    logger.info("Getting events from Sachsenpunk...")
    soup = get_soup(SACHSENPUNK_URL)
    if not soup:
        logger.error("No data from Sachsenpunk")
        return {}
    entry_content = soup.find('div', {"class": "entry-content"})
    p_tags = entry_content.find_all('p')
    events = defaultdict(list)
    year_now = datetime.now().year
    month_now = datetime.now().month
    previous_month = 0
    year = year_now

    for p in p_tags:
        if re.match(r"\d+\.\d+\.", p.text):
            # Checking if there is announcement for the new year
            current_month = int(p.text[3:5])
            if current_month < previous_month or (month_now == 12 and current_month == 1):
                year = year_now + 1
            previous_month = current_month

            date_str = p.text[:6] + str(year)
            current_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            if current_date < start_date:
                continue
            if current_date >= final_date:
                break

            events_date = str(current_date)
            current_events = p.find_next('p').text.split("\n")
            for event in current_events:
                if "Leipzig" in event:
                    event_str = event.lstrip("Leipzig – ")
                    events[events_date].append(event_str)
    logger.info("Events from Sachsenpunk are fetched")
    return events


def get_songkick_events(start_date: datetime.date, final_date: datetime.date):
    logger.info("Getting events from Songkick...")
    soup = get_soup(SONGKICK_URL)
    if not soup:
        logger.error("No data from Songkick")
        return {}
    event_elements = soup.find_all('li', {"class": "event-listings-element"})
    events = defaultdict(list)

    def get_full_url(ending: str) -> str:
        return "https://www.songkick.com" + ending

    for event_element in event_elements:
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
        if current_date < start_date:
            continue
        if current_date >= final_date:
            break

        date_str = str(current_datetime.date())
        events[date_str].append(event)
        event['time'] = time_str

        div_artist = event_element.find('div', {"class": "artists-venue-location-wrapper"})
        event_link = div_artist.find('a', {"class": "event-link"})
        venue_link = div_artist.find('a', {"class": "venue-link"})
        event_name = div_artist.strong.text
        event_url = get_full_url(event_link['href'])
        event['name'] = event_name
        event['URL'] = event_url
        venue_name = None
        venue_url = None

        if venue_link:
            venue_url = get_full_url(venue_link['href'])
            venue_name = venue_link.text
        event['venue_name'] = venue_name
        event['venue_URL'] = venue_url
    logger.info("Events from Songkick are fetched")
    return events


def get_all_events() -> dict:
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
        move_start_date_in_config_week_forward()
    return events
