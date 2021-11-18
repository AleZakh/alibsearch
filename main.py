#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Searching books on alib.ru and scraping search results into txt file

import os
import logging
import re
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Optional, Generator
from time import sleep

import requests
import requests.adapters
import bs4

logging.basicConfig(level=logging.INFO, format=' %(asctime)s -  %(levelname)s -  %(message)s')

Book = namedtuple('Book', ['name', 'isbn', 'price', 'buy_url'])

MAX_PARALLEL = 500
ISBN_REGEX = re.compile(r'\(ISBN: (.*?)\)')  # ISBN number
PRICE_REGEX = re.compile(r'Цена: (.*) руб.')  # price
URL_FILTER_REGEX = re.compile('find3')
DELAY_REGEX = re.compile(r'Продолжить работу можно через (\d+) (\w+)')


def alib(url: str, query: str) -> Generator[Book, None, None]:
    """
    Parsing the 1st or/and next pages
    :param url:
    :param query:
    """
    with requests.Session() as ses:
        ses.mount('http://', requests.adapters.HTTPAdapter(pool_maxsize=MAX_PARALLEL))
        ses.mount('https://', requests.adapters.HTTPAdapter(pool_maxsize=MAX_PARALLEL))
        res = ses.get(url, params={'tfind': query.encode('cp1251')})
        with ProcessPoolExecutor(os.cpu_count() - 1) as p_ex:
            yield from get_books(res=res, p_ex=p_ex, ses=ses)


def get_books(
        res: requests.Response,
        p_ex: ProcessPoolExecutor,
        ses: Optional[requests.Session] = None
) -> Generator[Book, None, None]:
    """
    Process pages
    :param res:
    :param p_ex:
    :param ses:
    """
    logging.info(f'{res.url}\n{res.text[:200]}')
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    yield from search_page(soup=soup, p_ex=p_ex)

    if ses:
        pages_links = soup.find_all('a', href=URL_FILTER_REGEX)
        if len(pages_links) > 1:
            with ThreadPoolExecutor(min(len(pages_links), MAX_PARALLEL)) as ex:
                futures = (ex.submit(get_page, url=f'https:{page["href"]}', ses=ses) for page in pages_links)
                for future in as_completed(futures):
                    yield from get_books(res=future.result(), p_ex=p_ex)
        elif pages_links:
            for page in pages_links:
                res = get_page(url=f'https:{page["href"]}', ses=ses)
                yield from get_books(res=res, p_ex=p_ex)


def get_page(url: str, ses: requests.Session, params: Optional[dict] = None) -> requests.Response:
    """
    Get the page content considering rate limit
    :param url:
    :param ses:
    :param params:
    :return:
    """
    res = ses.get(url=url, params=params)

    delay_search = DELAY_REGEX.search(res.text)
    if delay_search:
        quantity = int(delay_search.group(1))
        scale = delay_search.group(2)
        if scale.startswith('секунд'):
            scale = 1
        elif scale.startswith('минут'):
            scale = 60
        elif scale.startswith('час'):
            scale = 60 * 60
        sleep(quantity * scale + 1)
        get_page(url=url, ses=ses, params=params)

    return res


def search_page(soup: bs4.BeautifulSoup, p_ex: ProcessPoolExecutor) -> Generator[Book, None, None]:
    """
    Parsing one webpage to list
    :param soup:
    :param p_ex:
    """
    tags = soup.select(f'body > p:has(a[href*="bs.php"])')
    futures = (p_ex.submit(parse_tag, ent) for ent in tags)
    for future in as_completed(futures):
        yield future.result()


def parse_tag(tag: bs4.Tag) -> Book:
    """
    Parse one entry
    :param tag:
    :return:
    """
    name = re.sub(r'\s+', ' ', tag.b.text.strip())  # book name extraction and cleaning
    buy_url: str = tag.select_one('a:has(b)')['href']

    isbn_search = ISBN_REGEX.search(tag.text)
    price_search = PRICE_REGEX.search(tag.text)

    isbn = isbn_search.group(1) if isbn_search else None
    price = price_search.group(1) if price_search else None

    return Book(name, isbn, price, buy_url)


def main():
    """
    Perform search and save result to file
    :return:
    """
    url = 'https://www.alib.ru/find3.php4'
    query = input('Query?')  # input query in russian

    # Write result to txt file named as query
    with open(query + '.txt', 'w', encoding='utf-8') as result_file:
        for book in alib(url, query):
            result_file.write(f'{book}\n')


if __name__ == '__main__':
    main()
