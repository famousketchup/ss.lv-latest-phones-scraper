#!/usr/bin/python3.11
"""SS.LV custom scraper for phones category."""

import threading
import time

# import webbrowser
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tinydb import Query, TinyDB

# Preparation
ROOT_URL = 'https://www.ss.lv'
SEARCH_URL = ROOT_URL + '/ru/electronics/phones/mobile-phones/search-result/'
SEARCH_URL_REQUESTS_POST_DATA = {
    'txt': '',  # Post text
    # Brands
    'opt[44][]': [
        '689',
        '6493',
        '697',
        '112388',
        '684',
        '17527',
        '113853',
        '690',
        '113837',
        '696',
        '687',
        '3453',
        '685',
        '695',
        '688',
        '6492',
        '694',
        '691',
        '686',
        '698',
        '114811',
    ],
    'topt[98]': '',  # Model
    'topt[42][min]': '64',  # Min. storage
    'topt[42][max]': '128',  # Max. storage
    # Any kind of phone types
    'opt[1608][]': ['112224', '112225', '112226', '112227'],
    'opt[352][]': '0',  # Any product condition
    'topt[8][min]': '55',  # Min. price
    'topt[8][max]': '85',  # Max. price
    'sid': '1',  # Only selling status
    'search_region': 'riga_f',  # Local offers only (Riga)
    'pr': '3',  # Period of being posted (3 days ago max.)
    'sort': '8',  # Sort by price
    'btn': 'Искать',
}
SELECTOR_POSTS_INNER = 'table#page_main tr td table tr td.msga2 > a'

db = TinyDB('ss-phones.json', ensure_ascii=False)
Item = Query()
where = Query()

CHECK_INTERVAL = 1800  # every 30 minutes


def get_search_results(limit=False):
    """Get search results from custom phone SS.LV search."""
    querying_items_count = 'all' if limit is False else limit
    print(f'Querying {querying_items_count} items')

    # Preamble
    response = requests.post(url=SEARCH_URL, data=SEARCH_URL_REQUESTS_POST_DATA)
    if limit is True:
        limit = 10

        # DEBUG
        #
        # html_content = response.content
        # soup = BeautifulSoup(html_content, 'html.parser')
        # with open('tmp.html', 'w') as f:
        #   f.write(str(soup.prettify()))
        # webbrowser.open_new_tab('tmp.html')
        #
        # END

        # Parse response and get all item element's rows
        soup = BeautifulSoup(response.text, 'html.parser')
        item_soups_inner = soup.select(SELECTOR_POSTS_INNER)
        item_soups = []
        for inner_item_soup in item_soups_inner:
            if inner_item_soup.parent is not None:
                item_soups.append(inner_item_soup.parent.parent)

        if limit is not False:  # Limit if necessary
            item_soups = item_soups[:limit]

            # Parse items and get all necessary info from their markup
            items = []
            for item in item_soups:
                item_parsed = {
                    'url': ROOT_URL + item.select_one('td.msga2 a').attrs['href'],
                    'category': item.select_one('.ads_cat_names').text,
                    'text': item.select_one('.d1 a.am').text,
                    'location': item.select_one('.ads_region').text,
                    'brand': item.select_one('td:nth-child(4)').text,
                    'model': item.select_one('td:nth-child(5)').text,
                    'storage': item.select_one('td:nth-child(6)').text,
                    'state': item.select_one('td:nth-child(7)').text,
                    'price': item.select_one('td:nth-child(8)').text,
                }
                items.append(item_parsed)

                return items


def add_new_items_to_db(items):
    """Add items to the local database (only if they do not exist).

    Also, supply the item with creation date and time and
    count how many items were added.
    """
    for item in items:
        added_items_count = 0
        item_exists = len(db.search(Item.url == item['url'])) > 0
        if not item_exists:
            item['created_at'] = datetime.now().isoformat()
            db.insert(item)
            added_items_count += 1


def get_and_add_items():
    """Get last X items and add non-existent ones to database"""
    items = get_search_results(limit=10)
    added_items_count = add_new_items_to_db(items)
    print(f'Added {added_items_count} items')


def run_function_every(seconds=CHECK_INTERVAL):
    while True:
        get_and_add_items()
        time.sleep(CHECK_INTERVAL)


# Start a thread to run your_function at specified CHECK_INTERVAL
thread = threading.Thread(target=run_function_every_1800_seconds)
# Set the thread as a daemon so it terminates when the main program exits
thread.daemon = True
thread.start()


# Keep the main program running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('Program terminated by user.')
