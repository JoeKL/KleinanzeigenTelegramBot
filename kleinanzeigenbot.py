import asyncio
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import os.path
import requests
import json
import time
import sys

#header für req
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}

#erstelle timestamp im format: [Wed Jan  6 15:44:14 2021]
def timestamp():
    return '[' + time.asctime(time.localtime()) + '] '

def extract_list_item_data(item):
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

def return_items_from_req(searchterm):

    # URL und Header für Webrequest
    req_url = "https://www.kleinanzeigen.de/s-pc-zubehoer-software/" + searchterm + "/k0c255"

    # Webrequest
    print(timestamp() + 'sending web_request for term: \'' + searchterm + '\'')
    req = Request(url=req_url, headers=headers) 
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
        print(timestamp() + 'Error Exception: ' + str(e))
        item_list_html = ''

    #gebe die itemliste zurück
    return item_list_html


def append_items_to_json_file(item_list, filepath) :
    with open(filepath, 'r') as file:
        existing_items = json.load(file)

    existing_adids = set(item['data-adid'] for item in existing_items)

    # Initialisiere einen Zähler für die hinzugefügten Items
    added_count = 0

    for item in item_list:
        item_data = extract_list_item_data(item)
        # Überprüfen, ob item_data ein Dictionary ist und 'data-adid' enthält
        if item_data and 'data-adid' in item_data and item_data['data-adid'] not in existing_adids:
            existing_items.append(item_data)
            existing_adids.add(item_data['data-adid'])
            added_count += 1  # Erhöhe den Zähler

    with open(filepath, 'w') as file:
        json.dump(existing_items, file, indent=4)

    return added_count



def main():

    # sys.argv enthält den Skriptnamen und die übergebenen Argumente
    script_name = sys.argv[0]
    args = sys.argv[1:]  # Alle Argumente nach dem Skriptnamen

    stop_running = False
    
    searchterm = args[0]
    sleeptime = int(args[1])
    # min_price = args[3]
    # max_price = args[4]

    print("starting worker with searchterm " + searchterm + " and sleeptime " + str(sleeptime))

    # Erstelle den Dateipfad
    filepath = os.path.join(os.path.dirname(__file__), 'data', searchterm + '.json')

    # Wenn der Ordner nicht existiert, erstelle diesen
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Wenn die JSON-Datei nicht existiert, dann erstelle eine leere Datei
    if not os.path.isfile(filepath):
        with open(filepath, "w") as text_file:
            text_file.write("[]")

    while not stop_running:
        try:

            # hole aktuelle items
            item_list = return_items_from_req(searchterm)

            added_items_count = append_items_to_json_file(item_list, filepath)

            print(timestamp() + "added " + str(added_items_count) + " items")

            #rollback to prev list
            if item_list == '':
                raise Exception("Fehler beim request aufgetreten: item_list ist leer")
                
        except Exception as e:
            print(timestamp() + 'Error Exception: ' + str(e))

        # Asynchrones Warten
        time.sleep(sleeptime)
if __name__ == "__main__":
    main()