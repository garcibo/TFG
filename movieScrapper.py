import re

import requests
import time
from stem import Signal
from stem.control import Controller
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime

films= {'title': [], 'age_rating': [], 'rating': [], 'rank': [], 'genre': [],
               'director': [], 'year': [], 'producer': [], 'actor': [],'runtime': [], 'description': [], 'img': [], 'url': []}


def clearEntry():
    films['url'].pop()
    films['title'].pop()


def getTopPage(page):

    try:
        url = 'https://www.metacritic.com/browse/movies/score/metascore/all/filtered?page=' + str(page)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        result = requests.get(url, headers=headers)
        # print(page,"element" , i)
        soup = BeautifulSoup(result.text, 'html.parser')
        for review in soup.find_all('td', class_='clamp-summary-wrap'):
            # print(review)
            films['title'].append(review.find('h3').text)
            rank = review.find('span', class_=re.compile("title numbered")).text
            rank = re.findall(r'\d+', rank)
            rank = int(rank[0])

            url = review.find('a', class_=re.compile("title"))
            films['url'].append('https://www.metacritic.com' + url['href'])
            url = 'https://www.metacritic.com' + url['href']

            if rank in [1774, 1886] or getPage(url, headers) == 0:  # 620
                clearEntry()
                continue
            age_rating = review.find('span', class_=re.compile("cert_rating"))
            if age_rating is not None:
                films['age_rating'].append(age_rating.text)
            else:
                films['age_rating'].append("Not Rated")
            films['rating'].append(review.find('div', class_=re.compile("metascore_w user ")).text)

            films['rank'].append(rank)
            print(rank, "completado")
            if rank % 51 == 0:
                renew_ip()

            index = review.find('span', class_=re.compile("title numbered")).text
    except Exception as e:
        print(str(e))


def getPage(page, headers):
    resultPage = requests.get(page, headers=headers)

    soup = BeautifulSoup(resultPage.text, 'html.parser')

    if soup.find('script', type='application/ld+json') is None:
        return 0
    JSON = json.loads(
        soup.find('script', type='application/ld+json').get_text())  # comprobar si find devulve none, en ese caso
    runtimeRaw = soup.find('div', class_='runtime')

    if "description" in JSON:
        description = JSON["description"]
    else:
        return 0

    if "image" in JSON:
        img = JSON["image"]
    else:
        return 0
    if runtimeRaw is None:
        return 0
    runtime = re.findall(r'\d+', runtimeRaw.text)
    runtime = int(runtime[0])

    if "director" in JSON:
        director = JSON["director"]
        director = director[0]
    else:
        return 0
    if "datePublished" in JSON:
        date = JSON["datePublished"]
        year_re = JSON["datePublished"]
        if year_re == 'TBA':
            year = 2022
        else:

            if re.findall(r'\d{4}', year_re):
                year = re.findall(r'\d{4}', year_re)
                year = int(year[0])
            else:
                return 0
    else:
        return 0

    if "genre" in JSON:
        genres = JSON["genre"]
        genre = genres[0]
    else:
        genre = "untagged"

    if "publisher" in JSON:
        publisher = JSON["publisher"]
        publisher = publisher[0]
        publisher = publisher["name"]
    else:
        publisher = "untagged"

    if "actor" in JSON:
        actorList = JSON["actor"]
        mainActor = actorList[0]
        mainActorName = mainActor["name"]
    else:
        mainActorName = "untagged"

    films['director'].append(director["name"])
    films['genre'].append(genre)
    films['year'].append(year)
    films['producer'].append(publisher)
    films['actor'].append(mainActorName)
    films['description'].append(description)
    films['img'].append(img)
    films['runtime'].append(runtime)
    return 1


def renew_ip():
    print("Renovando IP, esto tomará unos segundos")
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password="Pablo0302")
        controller.signal(Signal.NEWNYM)
        time.sleep(5)


if __name__ == "__main__":
    # For every page
    session = requests.session()
    # TO Request URL with SOCKS over TOR
    session.proxies = {'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'}
    renew_ip()

    for i in range(0, 145):  # To 145
        getTopPage(i)
        print("Page ", i)
        pd.DataFrame(films).to_csv('file.csv', index=False)  # por si acaso escribo cada 100
pd.DataFrame(films).to_csv('file'+datetime.now().strftime("%m-%d-%Y_%H:%M")+'.csv', index=False)  # por si acaso escribo cada 100
