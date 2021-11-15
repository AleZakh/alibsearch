# Searching books on alib.ru and scraping search results into txt file

import bs4
import logging
import re
import requests

logging.basicConfig(level=logging.INFO, format=' %(asctime)s -  %(levelname)s -  %(message)s')


def alib(url, inquire): #parsing the 1st or/and next pages
    result = []
    res = requests.get(url + convert1251(inquire))
    print(url + convert1251(inquire))
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')

    arrPages = []
    for a in soup.find_all('a', href=True):
        if 'find3' in a['href']: #finding other pages of search result, if there is only 1 page arrPages=[]
            arrPages.append(a['href'])
    print(arrPages)

    n = 0
    while True:
        result.append(searchpage(soup))
        if len(arrPages) < 1: #if there is more than one pages of search result
            break
        else:
            res = requests.get('https:' + arrPages[n])
            res.raise_for_status()
            soup = bs4.BeautifulSoup(res.text, 'html.parser')
            n = n + 1
            if n == len(arrPages):
                break

    return result


def searchpage(curSoup): #parsing one webpage to list
    nameRegex = re.compile(r'<b>(.*?)</b>')  # Name of position
    isbnRegex = re.compile(r'\(ISBN: (.*?)\)')  # ISBN number
    priceRegex = re.compile(r'Цена: (.*) руб.')  # price
    urlRegex = re.compile(r'"(.*)"')  # Position URL

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
        except Exception as err:
            pass

        try:
            logging.debug(str(nameSearch.group(1)))
            logging.debug(str(priceSearch.group(1)))
            logging.debug(str(buyURLSearch.group(1)))
            logging.debug(str(ISBNSearch.group(1)))
        except Exception as err:
            logging.debug("Элемент не найден")

        pageResult.append([name, ISBN, price, buyURL])
        i = i + 1

    return pageResult


def convert1251(string):  # convert utf-8 query to microsoft 1251
    string = bytes(string, 'utf-8')
    string = string.decode('utf-8').encode('cp1251')
    string = str(string)
    string = string[2:(len(string) - 1)]
    string = string.split('\\x')
    string = '%'.join(string)
    return string


URL = 'https://www.alib.ru/find3.php4?tfind='
query = input() # input query in russian
resultList = alib(URL, query)

# Write resultList to txt file named as query
with open(query + '.txt', 'w') as resultFile:
    resultFile.writelines("%s\n" % result for result in resultList)
