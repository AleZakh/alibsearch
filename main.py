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
PRICE_REGEX = re.compile(r'Цена: (.*?) руб.')  # price
URL_FILTER_REGEX = re.compile('find3')


def alib(url, inquire):  # parsing the 1st or/and next pages
    res = requests.get(url, params={'tfind': inquire.encode('cp1251')})
    logging.info(url + inquire)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    result = searchpage(soup)

    # finding other pages of search result, if there is only 1 page pages is empty
    extra_pages = (a['href'] for a in soup.find_all('a', href=URL_FILTER_REGEX))

    for page in extra_pages:
        logging.info(page)
        res = requests.get('https:' + page)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        result.extend(searchpage(soup))

    return result


def searchpage(soup):  # parsing one webpage to list
    result = []
    for ent in soup.select(f'body > p:has(a[href*="bs.php"])'):
        name = ent.b.text
        buy_url = ent.select_one('a:has(b)')['href']

        isbn_search = ISBN_REGEX.search(ent.text)
        price_search = PRICE_REGEX.search(ent.text)

        isbn = isbn_search.group(1) if isbn_search else None
        price = int(price_search.group(1)) if price_search else None

        result.append(Book(name, isbn, price, buy_url))

    return result


def main(query):
    url = 'https://www.alib.ru/find3.php4'
    #query = input('Query?')  # input query in russian
    result = alib(url, query)

    # Write result to txt file named as query
    with open(query + '.txt', 'w', encoding='utf-8') as resultFile:
        resultFile.writelines(f'{result}\n' for result in result)
    return result

if __name__ == '__main__':
    main()
