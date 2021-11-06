import re

import requests
import time
from stem import Signal
from stem.control import Controller
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime

reviewsDF = {'title': [], 'user': [], 'type': [], 'grade': [], 'review': [], }


def renew_ip():
    print("Enmascarando IP, esto tomará unos segundos")
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password="Pablo0302")
        controller.signal(Signal.NEWNYM)
        time.sleep(5)


def getSource(review):
    sourceRaw = review.find('span', class_="source")
    sourceLink = sourceRaw.find('a')
    source = sourceLink['href']
    prefinalSource = source.replace("/publication/", "")
    finalSource = prefinalSource.replace("?filter=movies", "")
    return finalSource


def processCriticReviewPage(soupReviewPage, title):
    reviews = soupReviewPage.find_all('div', class_='review')
    for review in reviews:
        reviewContent = review.find('a', class_='no_hover')
        if reviewContent is not None:
            grade = review.find('div', class_='metascore_w').text
            source = getSource(review)
            reviewsDF['user'].append(source)
            reviewsDF['grade'].append(grade)
            reviewsDF['title'].append(title)
            reviewsDF['review'].append(reviewContent.text)
            reviewsDF['type'].append("reviewer")


def processSingleReviewPage(soupReviewPage, title):
    reviews = soupReviewPage.find_all('div', class_='review')
    for review in reviews:
        grade = review.find('div', class_='metascore_w').text
        authorRaw = review.find('a')
        if authorRaw is not None:
            author=authorRaw.text
        else:
            author = review.find('span', class_='author').text

        reviewBody = review.find('div', class_='review_body').text

        reviewsDF['user'].append(author)
        reviewsDF['grade'].append(grade)
        reviewsDF['title'].append(title)
        reviewsDF['review'].append(reviewBody)
        reviewsDF['type'].append("user")


def processUserReviewPage(soupReviewPage, title):
    pages = soupReviewPage.findAll('a', class_='page_num')
    if pages:
        processSingleReviewPage(soupReviewPage, title)
        for page in pages:
            url = "https://www.metacritic.com" + page["href"]
            result = requests.get(url, headers=user_agent)
            soupSingleReview = BeautifulSoup(result.text, 'html.parser')
            processSingleReviewPage(soupSingleReview, title)

    else:
        processSingleReviewPage(soupReviewPage, title)


def processMoviePage(url, title):
    result = requests.get(url, headers=user_agent)
    soup = BeautifulSoup(result.text, 'html.parser')

    # la clase see_all tiene mas entradas ["see_all pad_btm1" y "see_all fwnorm fr"]
    # pero nos interesan justo las que tienen solo ese atributo,
    # en concreto esto redirige a todas las crticas de usuarios y todas las de criticos
    typeReview = 0
    for reviewList in soup.find_all('div', class_='see_all'):
        if len(reviewList["class"]) != 1:
            continue;
        href_tags = reviewList.find(href=True)
        urlReviewPage = "https://www.metacritic.com" + href_tags['href']
        review = requests.get(urlReviewPage, headers=user_agent)
        soupReviewPage = BeautifulSoup(review.text, 'html.parser')
        if typeReview == 0:
            processCriticReviewPage(soupReviewPage, title)
        if typeReview == 1:
            processUserReviewPage(soupReviewPage, title)
        typeReview += 1
        # print(index,urlReviewPage)


if __name__ == "__main__":
    # For every page
    session = requests.session()
    # TO Request URL with SOCKS over TOR
    session.proxies = {'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'}
    df = pd.read_csv(r'newdataset.csv')

    for index, row in df.iterrows():
        if index % 51 == 0:
            renew_ip()
            pd.DataFrame(reviewsDF).to_csv('fileReviewTemp.csv', index=False)  # por si acaso escribo cada 100

        user_agent = {'User-agent': 'Mozilla/5.0'}

        processMoviePage(row['url'], row['title'])
        print("Complatado",row['title'],index)
    pd.DataFrame(reviewsDF).to_csv('file' + datetime.now().strftime("%m-%d-%Y_%H:%M") + '.csv', index=False)
