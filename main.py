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

nameRegex = re.compile(r'<b>(.*?)</b>')  # Name of position
isbnRegex = re.compile(r'\(ISBN: (.*?)\)')  # ISBN number
priceRegex = re.compile(r'Цена: (.*) руб.')  # price
urlRegex = re.compile(r'"(.*)"')  # Position URL
url_filter = re.compile('find3')


def alib(url, inquire):  # parsing the 1st or/and next pages
    res = requests.get(url, params={'tfind': inquire.encode('cp1251')})
    logging.info(url + inquire)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    result = searchpage(soup)

    # finding other pages of search result, if there is only 1 page pages is empty
    pages = (a['href'] for a in soup.find_all('a', href=url_filter))

    for page in pages:
        logging.info(page)
        res = requests.get('https:' + page)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        result.extend(searchpage(soup))

    return result


def searchpage(soup):  # parsing one webpage to list
    i = 2
    result = []
    while soup.select('body > p:nth-of-type(' + str(i) + ') > b'):
        name_search = nameRegex.search(str(soup.select('body > p:nth-of-type(' + str(i) + ')')))
        isbn_search = isbnRegex.search(str(soup.select('body > p:nth-of-type(' + str(i) + ')')))
        price_search = priceRegex.search(str(soup.select('body > p:nth-of-type(' + str(i) + ')')))
        buy_url_search = urlRegex.search(str(soup.select('body > p:nth-of-type(' + str(i) + ')>a:nth-child(4)')))

        name, price, buy_url, isbn = 0, 0, 0, 0
        try:
            name = str(name_search.group(1))
            price = str(price_search.group(1))
            buy_url = str(buy_url_search.group(1))
            isbn = str(isbn_search.group(1))
        except:
            pass

        try:
            logging.debug(str(name_search.group(1)))
            logging.debug(str(price_search.group(1)))
            logging.debug(str(buy_url_search.group(1)))
            logging.debug(str(isbn_search.group(1)))
        except:
            logging.debug('Элемент не найден')

        result.append(Book(name, isbn, price, buy_url))
        i = i + 1

    return result


def main():
    url = 'https://www.alib.ru/find3.php4'
    query = input('Query?')  # input query in russian
    result = alib(url, query)

    # Write result to txt file named as query
    with open(query + '.txt', 'w', encoding='utf-8') as resultFile:
        resultFile.writelines(f'{result}\n' for result in result)


if __name__ == '__main__':
    main()
