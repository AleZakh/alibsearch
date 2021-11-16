#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Searching books on alib.ru and scraping search results into txt file

import logging
import re
from collections import namedtuple

import requests
import bs4

logging.basicConfig(level=logging.INFO, format=' %(asctime)s -  %(levelname)s -  %(message)s')

Book = namedtuple('Book', ['name', 'isbn', 'price', 'buy_url'])

ISBN_REGEX = re.compile(r'\(ISBN: (.*?)\)')  # ISBN number
PRICE_REGEX = re.compile(r'Цена: (.*) руб.')  # price
URL_FILTER_REGEX = re.compile('find3')


def alib(url, query):  # parsing the 1st or/and next pages
    with requests.Session() as ses:
        yield from get_books(url=url, ses=ses, params={'tfind': query.encode('cp1251')})


def get_books(url, ses, params=None):
    res = ses.get(url, params=params)

    logging.info(res.url)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    yield from search_page(soup)

    if params:
        pages_links = soup.find_all('a', href=URL_FILTER_REGEX)
        pages_links = (a['href'] for a in pages_links)
        for page in pages_links:
            yield from get_books(url=f'https:{page}', ses=ses)


def search_page(soup):  # parsing one webpage to list
    for ent in soup.select(f'body > p:has(a[href*="bs.php"])'):
        name = re.sub(r'\s+', ' ', ent.b.text.strip())  # book name extraction and cleaning
        buy_url = ent.select_one('a:has(b)')['href']

        isbn_search = ISBN_REGEX.search(ent.text)
        price_search = PRICE_REGEX.search(ent.text)

        isbn = isbn_search.group(1) if isbn_search else None
        price = price_search.group(1) if price_search else None

        yield Book(name, isbn, price, buy_url)


def main():
    url = 'https://www.alib.ru/find3.php4'
    query = input('Query?')  # input query in russian

    # Write result to txt file named as query
    with open(query + '.txt', 'w', encoding='utf-8') as result_file:
        for book in alib(url, query):
            result_file.write(f'{book}\n')


if __name__ == '__main__':
    main()
