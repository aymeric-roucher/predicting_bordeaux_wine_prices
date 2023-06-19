from bs4 import BeautifulSoup
import requests
import pandas as pd
import concurrent.futures
import time
from tqdm import tqdm
import numpy as np
import copy

# HEADERS = {
#    "user-agent": (
#        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
#        "(KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36"
#    )
# }
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
IDEALWINE_BASE_URL = "https://www.idealwine.com"
IDEALWINE_SEARCH_URL = IDEALWINE_BASE_URL + "/uk/wine-prices/{}.jsp"
WINESEARCHER_BASE_URL = "https://www.wine-searcher.com"
WINESEARCHER_SEARCH_URL = WINESEARCHER_BASE_URL + "/find/{}/2010#t5"

# Let us first create a list of all grands crus from the 1855 ranking of Medoc
left_bank = {
    "Château Latour": "https://www.idealwine.com/fr/prix-vin/418-2011-Bouteille-Bordeaux-Pauillac-Chateau-Latour-1er-Grand-Cru-Classe-Rouge.jsp",
    "Château Lafite Rothschild": "https://www.idealwine.com/fr/prix-vin/385-2018-Bouteille-Bordeaux-Pauillac-Chateau-Lafite-Rothschild-1er-Grand-Cru-Classe-Rouge.jsp",
    "Château Léoville-Las-Cases": "https://www.idealwine.com/fr/prix-vin/425-2017-Bouteille-Bordeaux-Saint-Julien-Chateau-Leoville-Las-Cases-2eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Margaux": "https://www.idealwine.com/fr/prix-vin/466-2018-Bouteille-Bordeaux-Margaux-Chateau-1er-Grand-Cru-Classe-Rouge.jsp",
    "Château Mouton-Rothschild": "https://www.idealwine.com/fr/prix-vin/508-2018-Bouteille-Bordeaux-Pauillac-Chateau-Mouton-Rothschild-1er-Grand-Cru-Classe-Rouge.jsp",
    "Château Pichon-Longueville Comtesse de Lalande": "https://www.idealwine.com/fr/prix-vin/551-2017-Bouteille-Bordeaux-Pauillac-Chateau-Pichon-Longueville-Comtesse-de-Lalande-2eme-Grand-Cru-Classe-Rouge.jsp",
    "Cos-d'Estournel": "https://www.idealwine.com/fr/prix-vin/170-2017-Bouteille-Bordeaux-Saint-Estephe-Cos-dEstournel-2eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Ducru-Beaucaillou": "https://www.idealwine.com/fr/prix-vin/227-2017-Bouteille-Bordeaux-Saint-Julien-Chateau-Ducru-Beaucaillou-2eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Palmer": "https://www.idealwine.com/fr/prix-vin/517-2017-Bouteille-Bordeaux-Margaux-Chateau-Palmer-3eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Léoville-Barton": "https://www.idealwine.com/fr/prix-vin/424-2017-Bouteille-Bordeaux-Saint-Julien-Chateau-Leoville-Barton-2eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Montrose": "https://www.idealwine.com/fr/prix-vin/494-2017-Bouteille-Bordeaux-Saint-Estephe-Chateau-Montrose-2eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Gruaud-Larose": "https://www.idealwine.com/fr/prix-vin/316-2017-Bouteille-Bordeaux-Saint-Julien-Chateau-Gruaud-Larose-2eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Lynch-Bages": "https://www.idealwine.com/fr/prix-vin/449-2017-Bouteille-Bordeaux-Pauillac-Chateau-Lynch-Bages-5eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Pichon-Longueville Baron": "https://www.idealwine.com/fr/prix-vin/550-2018-Bouteille-Bordeaux-Pauillac-Chateau-Pichon-Longueville-Baron-2eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Clerc-Milon": "https://www.idealwine.com/fr/prix-vin/144-2017-Bouteille-Bordeaux-Pauillac-Chateau-Clerc-Milon-5eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Pontet-Canet": "https://www.idealwine.com/fr/prix-vin/567-2017-Bouteille-Bordeaux-Pauillac-Chateau-Pontet-Canet-5eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Léoville-Poyferré": "https://www.idealwine.com/fr/prix-vin/426-2017-Bouteille-Bordeaux-Saint-Julien-Chateau-Leoville-Poyferre-2eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Beychevelle": "https://www.idealwine.com/fr/prix-vin/58-2018-Bouteille-Bordeaux-Saint-Julien-Chateau-Beychevelle-4eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Duhart-Milon": "https://www.idealwine.com/fr/prix-vin/228-2017-Bouteille-Bordeaux-Pauillac-Chateau-Duhart-Milon-4eme-Grand-Cru-Classe-Rouge.jsp",
    "Château Calon-Segur": "https://www.idealwine.com/fr/prix-vin/97-2018-Bouteille-Bordeaux-Saint-Estephe-Chateau-Calon-Segur-3eme-Grand-Cru-Classe-Rouge.jsp",
    "Château d'Armailhac": "https://www.idealwine.com/fr/prix-vin/12-2017-Bouteille-Bordeaux-Pauillac-Chateau-d-Armailhac-Mouton-Baronne-Philippe-5eme-Grand-Cru-Classe-Rouge.jsp",
}

graves = {
    "Domaine de Chevalier": "https://www.idealwine.com/fr/prix-vin/219-2017-Bouteille-Bordeaux-Pessac-Leognan-Domaine-de-Chevalier-Cru-Classe-Graves-Rouge.jsp",
    "Château Haut-Bailly": "https://www.idealwine.com/fr/prix-vin/327-2017-Bouteille-Bordeaux-Pessac-Leognan-Chateau-Haut-Bailly-Cru-Classe-de-Graves-Rouge.jsp",
    "Château Pape Clément": "https://www.idealwine.com/fr/prix-vin/520-2019-Bouteille-Bordeaux-Pessac-Leognan-Chateau-Pape-Clement-Cru-Classe-de-Graves-Rouge.jsp",
    "Château Smith Haut Lafitte": "https://www.idealwine.com/fr/prix-vin/657-2017-Bouteille-Bordeaux-Pessac-Leognan-Chateau-Smith-Haut-Lafitte-Cru-Classe-de-Graves-Rouge.jsp",
    "Château Haut-Brion": "https://www.idealwine.com/fr/prix-vin/335-2018-Bouteille-Bordeaux-Pessac-Leognan-Chateau-Haut-Brion-1er-Grand-Cru-Classe-Rouge.jsp",
    "Château La Tour Haut-Brion": "https://www.idealwine.com/fr/prix-vin/691-2010-Bouteille-Bordeaux-Pessac-Leognan-Chateau-La-Tour-Haut-Brion-Cru-Classe-de-Graves-Rouge.jsp",
    "Château Les Carmes Haut-Brion": "https://www.idealwine.com/fr/prix-vin/118-2018-Bouteille-Bordeaux-Pessac-Leognan-Chateau-les-Carmes-Haut-Brion-Rouge.jsp",
    "Château La Mission Haut-Brion": "https://www.idealwine.com/fr/prix-vin/485-2018-Bouteille-Bordeaux-Pessac-Leognan-Chateau-La-Mission-Haut-Brion-Cru-Classe-de-Graves-Rouge.jsp",
}

st_emilion = {
    "Château Angélus": "https://www.idealwine.com/fr/prix-vin/4-2017-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Angelus-1er-Classe-A-Rouge.jsp",
    "Château Ausone": "https://www.idealwine.com/fr/prix-vin/16-2018-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Ausone-1er-Classe-A-Rouge.jsp",
    "Château Cheval Blanc": "https://www.idealwine.com/fr/prix-vin/136-2018-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Cheval-Blanc-1er-Classe-A-Rouge.jsp",
    "Château Pavie": "https://www.idealwine.com/fr/prix-vin/527-2017-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Pavie-1er-Classe-A-Rouge.jsp",
    "Château Beau-Séjour Bécot": "https://www.idealwine.com/fr/prix-vin/36-2017-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Beau-Sejour-Becot-1er-Classe-B-Rouge.jsp",
    "Château Beauséjour": "https://www.idealwine.com/fr/prix-vin/37-2017-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Beausejour-Duffau-Lagarrosse-1er-Classe-B-Rouge.jsp",
    "Château Belair-Monange": "https://www.idealwine.com/fr/prix-vin/43-2016-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Belair-Belair-Monange-1er-Classe-B-Rouge.jsp",
    "Château Canon": "https://www.idealwine.com/fr/prix-vin/100-2017-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Canon-1er-Classe-B-Rouge.jsp",
    "Château Canon la Gaffelière": "https://www.idealwine.com/fr/prix-vin/102-2017-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Canon-la-Gaffeliere-1er-Classe-B-Rouge.jsp",
    "Château la Gaffelière": "https://www.idealwine.com/fr/prix-vin/272-2018-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-la-Gaffeliere-1er-Classe-B-Rouge.jsp",
    "Château Figeac": "https://www.idealwine.com/fr/prix-vin/248-2017-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Figeac-1er-Classe-B-Rouge.jsp",
    "Château Larcis-Ducasse": "https://www.idealwine.com/fr/prix-vin/408-2017-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Larcis-Ducasse-1er-Classe-B-Rouge.jsp",
    "Château Pavie-Macquin": "https://www.idealwine.com/fr/prix-vin/529-2017-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Pavie-Macquin-1er-Classe-B-Rouge.jsp",
    "Château Troplong-Mondot": "https://www.idealwine.com/fr/prix-vin/707-2018-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Troplong-Mondot-1er-Classe-B-Rouge.jsp",
    "Château Trotte Vieille": "https://www.idealwine.com/fr/prix-vin/709-2017-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Trotte-Vieille-1er-Classe-B-Rouge.jsp",
    "Clos Fourtet": "https://www.idealwine.com/fr/prix-vin/152-2018-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Clos-Fourtet-1er-Classe-B-Rouge.jsp",
    "Château Magdelaine": "https://www.idealwine.com/fr/prix-vin/452-2013-Bouteille-Bordeaux-Saint-Emilion-Grand-Cru-Chateau-Magdelaine-Rouge.jsp",
}

pomerol = {
    "Petrus": "https://www.idealwine.com/fr/prix-vin/541-2018-Bouteille-Bordeaux-Pomerol-Petrus-Rouge.jsp",
    "Château L'Evangile": "https://www.idealwine.com/fr/prix-vin/236-2017-Bouteille-Bordeaux-Pomerol-Chateau-Evangile-Rouge.jsp",
    "Château La Fleur-Pétrus": "https://www.idealwine.com/fr/prix-vin/256-2017-Bouteille-Bordeaux-Pomerol-Chateau-la-Fleur-Petrus-Rouge.jsp",
    "Château Trotanoy": "https://www.idealwine.com/fr/prix-vin/708-2017-Bouteille-Bordeaux-Pomerol-Chateau-Trotanoy-Rouge.jsp",
    "Vieux Château Certan": "https://www.idealwine.com/fr/prix-vin/724-2017-Bouteille-Bordeaux-Pomerol-Vieux-Chateau-Certan-Rouge.jsp",
    "Château Le Bon pasteur": "https://www.idealwine.com/fr/prix-vin/62-2017-Bouteille-Bordeaux-Pomerol-Chateau-le-Bon-Pasteur-Rouge.jsp",
    "Château La Conseillante": "https://www.idealwine.com/fr/prix-vin/167-2017-Bouteille-Bordeaux-Pomerol-Chateau-la-Conseillante-Rouge.jsp",
    "Château Gazin": "https://www.idealwine.com/fr/prix-vin/279-2017-Bouteille-Bordeaux-Pomerol-Chateau-Gazin-Rouge.jsp",
    "Château Le Gay": "https://www.idealwine.com/fr/prix-vin/278-2017-Bouteille-Bordeaux-Pomerol-Chateau-Le-Gay-Rouge.jsp",
    "Clos l'Eglise": "https://www.idealwine.com/fr/prix-vin/157-2016-Bouteille-Bordeaux-Pomerol-Clos-lEglise-Rouge.jsp",
    "Château Clinet": "https://www.idealwine.com/fr/prix-vin/146-2017-Bouteille-Bordeaux-Pomerol-Chateau-Clinet-Rouge.jsp",
    "Château l'Eglise Clinet": "https://www.idealwine.com/fr/prix-vin/234-2017-Bouteille-Bordeaux-Pomerol-Chateau-Eglise-Clinet-Rouge.jsp",
    "Château Nenin": "https://www.idealwine.com/fr/prix-vin/511-2017-Bouteille-Bordeaux-Pomerol-Chateau-Nenin-Rouge.jsp",
}

categories = {
    "Médoc": left_bank,
    "Saint-Emilion": st_emilion,
    "Pomerol": pomerol,
    "Graves": graves,
}


class Vineyard:
    def __init__(self, name, url, category):
        self.name = name
        self.url = url
        self.category = category


VINEYARD_LIST = []
for category in categories.keys():
    wines = categories[category]
    for vineyard_name in wines.keys():
        VINEYARD_LIST.append(
            Vineyard(vineyard_name, wines[vineyard_name], category))


class Scraper:
    """Scraper that collects wine prices and critics. Adapted from @zackthoutt webscraper."""

    def __init__(self, vineyard_list, min_vintage, num_workers):
        self.start_time = time.time()
        self.session = requests.Session()
        self.vineyard_list = vineyard_list
        self.prices_idealwine = pd.DataFrame(
            index=[vineyard.name for vineyard in self.vineyard_list],
            columns=["Category"] + list(range(min_vintage, 2021, 1)),
        )
        self.min_vintage = min_vintage
        self.num_workers = num_workers

    def scrape(self):
        print("Beginning to scrape iDealwine...")
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.num_workers
        ) as executor:
            print(self.vineyard_list)
            res = list(
                tqdm(
                    executor.map(self.scrape_vineyard, self.vineyard_list),
                    total=len(self.vineyard_list),
                )
            )
        print("Scraping finished in ", int(
            time.time() - self.start_time), "s.\n")
        return self.prices_idealwine

    def scrape_vineyard(self, vineyard, retry_count=0):
        wine_url = copy.copy(vineyard.url)
        wine_response = self.session.get(wine_url, headers=HEADERS)
        wine_soup = BeautifulSoup(wine_response.content, "html.parser")
        max_vintage_str = wine_soup.find_all("a", {"class": "ola"})[
            0
        ].text
        max_vintage = int(max_vintage_str)
        print(max_vintage)

        self.prices_idealwine.loc[vineyard.name,
                                  "Category"] = vineyard.category
        print("Vintages:", range(max_vintage, self.min_vintage - 1, -1))
        for vintage in range(max_vintage, self.min_vintage - 1, -1):
            transformed_url_list = wine_url.split('-')
            transformed_url_list[2] = str(vintage)
            transformed_url = '-'.join(transformed_url_list)
            print(transformed_url)
            wine_response = self.session.get(transformed_url, headers=HEADERS)
            wine_soup = BeautifulSoup(wine_response.content, "html.parser")
            try:
                price = int(
                    wine_soup.find_all("article", {"class": "indice-table"})[0]
                    .text.split("€")[0]
                    .replace(" ", "")
                )
                self.prices_idealwine.loc[vineyard.name, vintage] = price
            except:
                self.prices_idealwine.loc[vineyard.name, vintage] = np.nan
        print(vineyard.name, self.prices_idealwine.loc[vineyard.name])
        return


if __name__ == "__main__":
    scraper = Scraper(VINEYARD_LIST, 1950, num_workers=1)
    table = scraper.scrape()
    print(table.iloc[:5, -10:].to_string())
    table.to_excel("../data/prices_june_23.xlsx", encoding="utf-16")
