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
        books = get_page(url=url, ses=ses, params={'tfind': query.encode('cp1251')})

        extra_pages = next(books)
        yield from books

        for page in extra_pages:
            yield from get_page(url=f'https:{page}', ses=ses)


def get_page(url, ses, params=None):
    res = ses.get(url, params=params, verify=r'C:\Users\pstroganov\cert\usergate-ssl-inspection.pem')

    logging.info(res.url)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')

    if params:
        yield (a['href'] for a in soup.find_all('a', href=URL_FILTER_REGEX))

    yield from search_page(soup)


def search_page(soup):  # parsing one webpage to list
    for ent in soup.select(f'body > p:has(a[href*="bs.php"])'):
        name = re.sub(r'\s+', ' ', ent.b.text.strip())
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
