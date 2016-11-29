#!/usr/bin/env python3


import os
import sys
import json
import requests
from bs4 import BeautifulSoup


games = {'GEN': 2, '4U': 1}


def item_list(game):
    items = {}
    if game == games['GEN']:
        req = requests.get('http://mhgen.kiranico.com/item')
        soup = BeautifulSoup(req.text, 'html.parser')
        for item in soup.find_all('td'):
            link = item.find('a')
            items[link.get_text()] = {'url': link.get('href'), 'found': None}
    return items


def locate_item(item_obj, game):
    url = item_obj['url']
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')
    places = {}
    if game == games['GEN']:
        parent = soup.find('div', {'class': 'col-lg-9'})
        divs = []
        for item in parent.findChildren():
            text = item.get_text()
            if text == 'Usage':
                break
            divs.append(item)
        titles = {x.find('h5').get_text():i for i, x in enumerate(divs)
                  if x.find('h5') is not None}

        # Check if you can get it from a monster
        if 'Monsters' in titles:
            info = divs[titles['Monsters']]
            places['monsters'] = {}
            current_monster = None
            for place in info.find_all('tr'):
                name = place.find('a')
                if name is not None:
                    current_monster = name.get_text()
                    places['monsters'][current_monster] = []
                    continue
                elements = [x.get_text() for x in place.find_all('td')]
                elements[2] = int(elements[2][1:])
                elements[3] = int(elements[3][:-1])
                places['monsters'][current_monster].append(elements)
        
        # Check if you can get it from a quest reward
        if 'Quests' in titles:
            info = divs[titles['Quests']]
            places['quests'] = []
            for quest in info.find_all('tr'):
                elements = [x.get_text() for x in quest.find_all('td')]
                elements[1] = int(elements[1][1:])
                elements[2] = int(elements[2][:-1])
                places['quests'].append(elements)

        # Check if you can get it from a certain map
        if 'Maps' in titles:
            info = divs[titles['Maps']]
            places['maps'] = {}
            for point in info.find_all('tr'):
                elements = [x.get_text().strip() for x in point.find_all('td')]
                rank, map_name, area, spot_type, ammount = elements
                if map_name not in places['maps']:
                    places['maps'][map_name] = []
                places['maps'][map_name].append([rank, area, spot_type, ammount])

        # Check if you can buy it
        alert = soup.find('div', {'class': 'alert'})
        if alert is not None:
            text = alert.get_text()
            if 'Purchase from shop' in text:
                text = text.strip()
                places['shop'] = int(text.split(' ')[-1][:-1])

        # Check if you can make it
        if 'Combinations' in titles:
            info = divs[titles['Combinations']]
            places['combinations'] = []
            for combo in info.find_all('div'):
                items = [x.get_text() for x in combo.find_all('a')]
                places['combinations'].append(items)
    item_obj['found'] = places
    return None


def main():

    if not os.path.exists('gen.json'):
        items = item_list(games['GEN'])
        with open('gen.json', 'w') as f:
            f.write(json.dumps(items))
    else:
        with open('gen.json', 'r') as f:
            items = json.loads(f.read())

    for index, item in enumerate(items):
        while True:
            print('[{:.2f}%] {}'.format(index/len(items)*100, item))
            try:
                locate_item(items[item], games['GEN'])
            except Exception:
                continue
            else:
                break

    with open('gen.json', 'w') as f:
        f.write(json.dumps(items))
    return None


if __name__ == "__main__":
    main()
