from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
from tqdm import tqdm
import numpy as np
import copy
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

HEADERS = {
    "authority": "scrapeme.live",
    "dnt": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "sec-fetch-site": "none",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
}

CHATEAUNET_BASE_URL = "https://primeurs.chateaunet.com/primeurs-2022/les-dernieres-sorties?product_state=2"
session = requests.Session()


def create_browser():
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk", "application/x-gzip"
    )
    options.set_preference("reader.parse-on-load.enabled", False)
    options.set_preference("browser.pocket.enabled", False)  # Duck pocket too!
    options.set_preference("permissions.default.image", 2)
    options.set_preference("browser.startup.page", 0)  # blank
    options.set_preference("permissions.default.stylesheet", 2)
    return webdriver.Firefox(options=options)


def scrape(browser, retry_count=0):
    primeur_prices = pd.DataFrame(index=[], columns=["Vineyard", "Price"])

    browser.get(CHATEAUNET_BASE_URL)
    time.sleep(10)
    soup = BeautifulSoup(browser.page_source, "html.parser")
    wine_soups = soup.find_all("div", {"class": "product-item-details"})
    for wine_soup in wine_soups:
        name = wine_soup.find(
            'div', {"class": "product-item-name"}).text.strip().replace(' 2022', '')
        price_soup = wine_soup.find(
            'div', {"class": "total-simple-product"})
        if price_soup and ('BLANC' not in name):
            price = price_soup.text
            price = price.split("€")[0]
            price = int(price.split(',')[0]) + 0.01 * int(price.split(',')[1])
            primeur_prices.loc[len(primeur_prices)] = [name, price]
    return primeur_prices


if __name__ == "__main__":
    browser = create_browser()
    table = scrape(browser)
    print(table.iloc[:5, -10:].to_string())
    table.to_excel("../data/primeurs_19_juin.xlsx", index=False)
