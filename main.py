#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Searching books on alib.ru and scraping search results into txt file

import logging
import re
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Generator

import requests
import requests.adapters
import bs4

logging.basicConfig(level=logging.INFO, format=' %(asctime)s -  %(levelname)s -  %(message)s')

Book = namedtuple('Book', ['name', 'isbn', 'price', 'buy_url'])

MAX_PARALLEL = 500
ISBN_REGEX = re.compile(r'\(ISBN: (.*?)\)')  # ISBN number
PRICE_REGEX = re.compile(r'Цена: (.*) руб.')  # price
URL_FILTER_REGEX = re.compile('find3')


def alib(url: str, query: str) -> Generator[Book]:  # parsing the 1st or/and next pages
    with requests.Session() as ses:
        ses.mount('http://', requests.adapters.HTTPAdapter(pool_maxsize=MAX_PARALLEL))
        ses.mount('https://', requests.adapters.HTTPAdapter(pool_maxsize=MAX_PARALLEL))
        res = ses.get(url, params={'tfind': query.encode('cp1251')})
        yield from get_books(res, ses=ses)


def get_books(res: requests.Response, ses: Optional[requests.Session] = None) -> Generator[Book]:
    logging.info(res.url)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    yield from search_page(soup)

    if ses:
        pages_links = soup.find_all('a', href=URL_FILTER_REGEX)
        if len(pages_links) > 1:
            with ThreadPoolExecutor(min(len(pages_links), MAX_PARALLEL)) as ex:
                futures = (ex.submit(ses.get, f'https:{page["href"]}') for page in pages_links)
                for future in as_completed(futures):
                    yield from get_books(res=future.result())
        elif pages_links:
            res = ses.get(f'https:{pages_links[0]["href"]}')
            yield from get_books(res=res)


def search_page(soup: bs4.BeautifulSoup) -> Generator[Book]:  # parsing one webpage to list
    ent: bs4.Tag
    for ent in soup.select(f'body > p:has(a[href*="bs.php"])'):
        name = re.sub(r'\s+', ' ', ent.b.text.strip())  # book name extraction and cleaning
        buy_url: str = ent.select_one('a:has(b)')['href']

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
