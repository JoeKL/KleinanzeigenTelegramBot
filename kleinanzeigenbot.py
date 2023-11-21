import threading
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import os.path
import json
import time

class KleinanzeigenBot(threading.Thread):

    #header für req
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}

    #erstelle timestamp im format: [Wed Jan  6 15:44:14 2021]
    def timestamp(self):
        return '[' + time.asctime(time.localtime()) + '] '

    def extract_list_item_data(self, item):
        article = item.find('article', class_='aditem')

        if article is None:
            return None  
        
        data = {
            'data-adid': article['data-adid'] if 'data-adid' in article.attrs else '',
            'link': article['data-href'] if 'data-href' in article.attrs else '',
            'image': item.find('img')['src'] if item.find('img') else '',
            'location': item.select_one('.aditem-main--top--left').get_text(strip=True) if item.select_one('.aditem-main--top--left') else '',
            'posted_time': item.select_one('.aditem-main--top--right').get_text(strip=True) if item.select_one('.aditem-main--top--right') else '',
            'title': item.select_one('h2 a').get_text(strip=True) if item.select_one('h2 a') else '',
            'description': item.select_one('.aditem-main--middle--description').get_text(strip=True) if item.select_one('.aditem-main--middle--description') else '',
            'price': item.select_one('.aditem-main--middle--price-shipping--price').get_text(strip=True) if item.select_one('.aditem-main--middle--price-shipping--price') else '',
            'shipping': item.select_one('.aditem-main--middle--price-shipping--shipping').get_text(strip=True) if item.select_one('.aditem-main--middle--price-shipping--shipping') else ''
        }
        return data

    def return_items_from_req(self, searchterm):

        # URL und Header für Webrequest
        req_url = f"https://www.kleinanzeigen.de/s/preis:{self.search_price_min}:{self.search_price_max}/{self.searchterm}/k0"

        # Webrequest
        print(self.timestamp() + 'sending web_request for term: \'' + searchterm + '\'')
        req = Request(url=req_url, headers=self.headers) 
        html = urlopen(req).read()
        
        # HTMLparsing
        data =  BeautifulSoup(html, "html.parser" ).encode('UTF-8')
        soup = BeautifulSoup(data, features="html.parser")

        # finden der artikelliste in html
        result = soup.find('ul', {'id':'srchrslt-adtable', 'class':'itemlist ad-list it3'})

        #setze leere itemliste
        item_list_html = ''

        #Error Handling if HTML parse empty
        try:
            item_list_html = result.find_all('li', class_="ad-listitem")

        #wenn ein error auftritt handle diesen
        except Exception as e:
            print(self.timestamp() + 'Error Exception: ' + str(e))
            item_list_html = ''

        #gebe die itemliste zurück
        return item_list_html


    def append_items_to_json_file(self, item_list, filepath) :
        with open(filepath, 'r') as file:
            existing_items = json.load(file)

        existing_adids = set(item['data-adid'] for item in existing_items)

        # Initialisiere einen Zähler für die hinzugefügten Items
        added_count = 0

        for item in item_list:
            item_data = self.extract_list_item_data(item)
            # Überprüfen, ob item_data ein Dictionary ist und 'data-adid' enthält
            if item_data and 'data-adid' in item_data and item_data['data-adid'] not in existing_adids:
                existing_items.append(item_data)
                existing_adids.add(item_data['data-adid'])
                added_count += 1  # Erhöhe den Zähler
                # Hier fügen wir das neue Item in die message_bus_queue ein
                self.message_bus_queue.put((self.searchterm, item_data))

        with open(filepath, 'w') as file:
            json.dump(existing_items, file, indent=4)

        return added_count



    def __init__(self, searchterm, sleeptime, message_bus_queue, search_category, search_price_min, search_price_max):
        threading.Thread.__init__(self)
        
        self.searchterm = searchterm
        self.sleeptime = sleeptime

        self.message_bus_queue = message_bus_queue

        self.search_category = search_category
        self.search_price_min = search_price_min
        self.search_price_max = search_price_max


        # Erstelle den Dateipfad
        self.filepath = os.path.join(os.path.dirname(__file__), 'data', searchterm + '.json')

        # Wenn der Ordner nicht existiert, erstelle diesen
        directory = os.path.dirname(self.filepath)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Wenn die JSON-Datei nicht existiert, dann erstelle eine leere Datei
        if not os.path.isfile(self.filepath):
            with open(self.filepath, "w") as text_file:
                text_file.write("[]")
        ("search initialized")
        self.run()

    def run(self):
        
        print("starting search")
        while True:
            try:

                # hole aktuelle items
                item_list = self.return_items_from_req(self.searchterm)

                added_items_count = self.append_items_to_json_file(item_list, self.filepath)

                print(self.timestamp() + "added " + str(added_items_count) + " items")

                #rollback to prev list
                if item_list == '':
                    raise Exception("Fehler beim request aufgetreten: item_list ist leer")
                    

            except Exception as e:
                print(self.timestamp() + 'Error Exception: ' + str(e))

            time.sleep(self.sleeptime)