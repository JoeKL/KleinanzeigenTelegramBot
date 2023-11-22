import threading
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import os.path
import json
import time

class KleinanzeigenBot(threading.Thread):

    # Standard-Header für HTTP-Anfragen, um sich als Browser zu identifizieren.
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}

    
    def timestamp(self):
        # Erstellt einen Zeitstempel im Format: [Wed Jan 6 15:44:14 2021].
        return '[' + time.asctime(time.localtime()) + '] '

    def extract_list_item_data(self, item):
        # Extrahiert Daten aus einem HTML-Element, das ein Kleinanzeigen-Listenelement repräsentiert.
        article = item.find('article', class_='aditem')

        if article is None:
            return None  
        
        # Sammelt relevante Daten wie ID, Link, Bild, etc. aus dem Artikel.
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

    def return_items_from_req(self):
        # Erzeugt die URL für die Kleinanzeigen-Suchanfrage basierend auf den Suchparametern.

        # Kategoriecode bauen
        if self.search_category != 0:
            category_code = f"k0c{self.search_category}"
        else: 
            category_code = "k0"

        # URL und Header für Webrequest
        req_url = f"https://www.kleinanzeigen.de/s/preis:{self.search_price_min}:{self.search_price_max}/{self.searchterm}/{category_code}"


        # Sendet eine HTTP-Anfrage zur angegebenen URL und lädt die HTML-Antwort.
        print(self.timestamp() + 'sending web_request to: \'' + req_url + '\'')
        req = Request(url=req_url, headers=self.headers) 
        html = urlopen(req).read()
        
        # Verwendet BeautifulSoup, um das HTML zu parsen und die relevanten Daten zu extrahieren.
        data =  BeautifulSoup(html, "html.parser" ).encode('UTF-8')
        soup = BeautifulSoup(data, features="html.parser")

        # Findet die Liste der Anzeigen im HTML.
        result = soup.find('ul', {'id':'srchrslt-adtable', 'class':'itemlist ad-list it3'})

        # Behandelt Fehler beim Parsen des HTMLs und extrahiert die Listenelemente.
        try:
            item_list_html = result.find_all('li', class_="ad-listitem")
        except Exception as e:
            print(self.timestamp() + 'Error Exception: ' + str(e))
            item_list_html = ''

        #gebe die itemliste zurück
        return item_list_html


    def append_items_to_json_file(self, item_list, filepath) :
        # Lädt bestehende Einträge aus einer JSON-Datei und fügt neue hinzu.
        with open(filepath, 'r') as file:
            existing_items = json.load(file)

        existing_adids = set(item['data-adid'] for item in existing_items)

        # Zählt, wie viele neue Einträge hinzugefügt werden.
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

        # Initialisiert den KleinanzeigenBot mit den gegebenen Parametern.
        self.searchterm = searchterm
        self.sleeptime = sleeptime

        self.message_bus_queue = message_bus_queue

        self.search_category = search_category
        self.search_price_min = search_price_min
        self.search_price_max = search_price_max


        # Erstellt den Dateipfad für die Speicherung von Anzeigendaten.
        self.filepath = os.path.join(os.path.dirname(__file__), 'data', searchterm + '.json')

        # Erstellt den Ordner und die Datei, falls sie nicht existieren.
        directory = os.path.dirname(self.filepath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        if not os.path.isfile(self.filepath):
            with open(self.filepath, "w") as text_file:
                text_file.write("[]")

        self.run()

    def run(self):
        # Hauptausführungsschleife des Bots, führt fortlaufend Suchanfragen durch.
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