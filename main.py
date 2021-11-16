#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Searching books on alib.ru and scraping search results into txt file

import logging
import re
from collections import namedtuple

import requests
import bs4

logging.basicConfig(level=logging.INFO, format=' %(asctime)s -  %(levelname)s -  %(message)s')

Book = namedtuple('Book', ['name', 'ISBN', 'price', 'buyURL'])

nameRegex = re.compile(r'<b>(.*?)</b>')  # Name of position
isbnRegex = re.compile(r'\(ISBN: (.*?)\)')  # ISBN number
priceRegex = re.compile(r'Цена: (.*) руб.')  # price
urlRegex = re.compile(r'"(.*)"')  # Position URL


def alib(url, inquire):  # parsing the 1st or/and next pages
    res = requests.get(url, params={'tfind': inquire.encode('cp1251')})
    logging.info(url + inquire)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    result = searchpage(soup)

    # finding other pages of search result, if there is only 1 page arrPages=[]
    arrPages = [a['href'] for a in soup.find_all('a', href=True) if 'find3' in a['href']]
    logging.info(arrPages)

    for page in arrPages:
        res = requests.get('https:' + page)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        result.extend(searchpage(soup))

    return result


def searchpage(curSoup):  # parsing one webpage to list
    i = 2
    pageResult = []
    while curSoup.select('body > p:nth-of-type(' + str(i) + ') > b'):
        nameSearch = nameRegex.search(str(curSoup.select('body > p:nth-of-type(' + str(i) + ')')))
        ISBNSearch = isbnRegex.search(str(curSoup.select('body > p:nth-of-type(' + str(i) + ')')))
        priceSearch = priceRegex.search(str(curSoup.select('body > p:nth-of-type(' + str(i) + ')')))
        buyURLSearch = urlRegex.search(str(curSoup.select('body > p:nth-of-type(' + str(i) + ')>a:nth-child(4)')))

        name, price, buyURL, ISBN = 0, 0, 0, 0
        try:
            name = str(nameSearch.group(1))
            price = str(priceSearch.group(1))
            buyURL = str(buyURLSearch.group(1))
            ISBN = str(ISBNSearch.group(1))
        except:
            pass

        try:
            logging.debug(str(nameSearch.group(1)))
            logging.debug(str(priceSearch.group(1)))
            logging.debug(str(buyURLSearch.group(1)))
            logging.debug(str(ISBNSearch.group(1)))
        except:
            logging.debug('Элемент не найден')

        pageResult.append(Book(name, ISBN, price, buyURL))
        i = i + 1

    return pageResult


def main():
    URL = 'https://www.alib.ru/find3.php4'
    query = input('Query?')  # input query in russian
    resultList = alib(URL, query)

    # Write resultList to txt file named as query
    with open(query + '.txt', 'w', encoding='utf-8') as resultFile:
        resultFile.writelines(f'{result}\n' for result in resultList)


if __name__ == '__main__':
    main()
