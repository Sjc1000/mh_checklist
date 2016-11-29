#!/usr/bin/env python3


import os
import difflib
import json
import curses
import _curses


FILEDIR = os.path.expanduser('~/.mh_checklist')
VERSION = '0.1.2'


class WindowSize(Exception):
    pass


class ItemList:
    def __init__(self, items, item_info):
        self.pos = 1
        self.offset = 0
        self.info_offset = 0
        self.items = items
        self.item_info = item_info

    def __enter__(self):
        self.screen = curses.initscr()
        curses.noecho()
        curses.curs_set(0)
        curses.cbreak()
        self.screen.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        return self

    def __exit__(self, eclass, func, traceback):
        curses.echo()
        curses.nocbreak()
        self.screen.keypad(False)
        curses.endwin()
        return None

    def main(self):
        self.init_colors()
        key = None
        while True:
            try:
                self.draw_item_list()
            except _curses.error:
                raise WindowSize('Your terminal went too small for the text.') 
            #self.screen.addstr(1, 1, str(key))
            #self.screen.refresh()
            
            key = self.screen.getch()
            if key == 113:
                break
            keystr = 'k_{}'.format(key)
            keyfunc = getattr(self, keystr, None)
            if keyfunc is not None:
                keyfunc()
        return None

    def k_259(self):
        self.pos -= 1
        if self.pos < 1:
            self.pos = 1
            self.offset -= 1
        if self.offset < 0:
            self.offset = 0
        self.info_offset = 0
        return None

    def k_258(self):
        if self.pos + self.offset == len(self.items)-1:
            return None
        self.pos += 1
        if self.pos == self.height-4:
            self.pos -= 1
            self.offset += 1
        self.info_offset = 0
        return None
    
    def k_114(self):
        del self.items[self.items.index(self.active)]
        self.k_259()
        return None


    def k_339(self):
        self.info_offset -= 1
        if self.info_offset < 0:
            self.info_offset = 0
        return None

    def k_338(self):
        self.info_offset += 1
        if self.info_offset+self.height-3 > self.info_length:
            self.info_offset -= 1
        return None

    def k_43(self):
        self.k_61()
        return None

    def k_61(self):
        if self.active is None:
            return None
        self.active[1] = self.active[1] + 1
        return None

    def k_45(self):
        if self.active is None:
            return None
        self.active[1] = self.active[1] - 1
        if self.active[1] == 0:
            del self.items[self.items.index(self.active)]
            self.k_259()
        return None

    def k_95(self):
        self.k_45()
        return None

    def k_97(self):
        input_string = ''
        display_string = ''
        self.screen.addstr(self.height-1, 0, 'New Item: '.ljust(
                           self.item_width), curses.A_REVERSE)
        self.screen.refresh()
        matches = []
        while True:
            key = self.screen.getch()
            if key == 263:
                display_string = display_string[:-1]
                input_string = display_string
                matches = []
            elif key == 10:
                break
            elif key == 9:
                if len(matches) == 0:
                    match = [x for x in self.item_info if input_string in x]
                    match = sorted(match, key=len)
                    matches += match
                if len(matches) == 0:
                    continue
                display_string = matches[0]
                matches = matches[1:]
            else:
                input_string = display_string + chr(key)
                display_string = input_string
                matches = []
            self.screen.addstr(self.height-1, 0, 'New Item: {}'.format(
                               display_string).ljust(self.item_width),
                               curses.A_REVERSE)
        if display_string.strip() == '':
            return None
        match = difflib.get_close_matches(display_string, self.item_info, 1, 0)
        if len(match) == 0:
            return None
        match = match[0]
        self.items.append([match, 1])
        return None

    def draw_item_list(self):
        self.screen.clear()
        self.height, self.width = self.screen.getmaxyx()
        item_width = int(self.width//1.8)
        self.item_width = item_width
        title = 'Item List'
        self.screen.addstr(title.center(item_width), curses.color_pair(1)
                                                     | curses.A_BOLD)
        footer = '[A]dd [R]emove [Q]uit [+] Increase [-] Decrease'
        self.screen.addstr(1, 0, footer.center(item_width))

        visible = self.items[self.offset:self.offset+self.height-4]
        active = self.draw_items(visible)
        self.active = active
        self.draw_info(active)
        return None

    def draw_items(self, item_list):
        active = None
        for ypos, item in enumerate(item_list):
            params = 0
            if item is None or item[0] is None:
                continue
            name, count = item
            if ypos == self.pos:
                params |= curses.A_REVERSE
                active = item

            string = ' [{:>3d}] {}'.format(count, name)
            self.screen.addstr(ypos+3, 0, string.ljust(self.item_width), params)
        return active

    def draw_info(self, item):
        for y in range(self.height):
            self.screen.addstr(y, self.item_width, ' ', curses.color_pair(1))

        size_left = self.width-self.item_width
        self.screen.addstr(0, self.item_width, 'Info'.center(size_left),
                           curses.color_pair(1) | curses.A_BOLD)

        if item is None:
            return None
        name, count = item
        info = self.item_info[name]['found']
        string = []

        # Check if you can buy it

        if 'shop' in info:
            string.append(['', 0])
            string.append(['You can buy it from the shop for {}z'.format(
                            info['shop']), curses.A_BOLD])
            string.append(['Total: {}x{}z = {}z'.format(count, info['shop'],
                           count*info['shop']), 0])
        
        # Get monster info.

        if 'monsters' in info:
            string.append(['', 0])
            string.append(['Monsters:', curses.A_BOLD])
            for monster in info['monsters']:
                string.append(['', 0])
                string.append([' {}'.format(monster), curses.A_BOLD])
                carves = sorted(info['monsters'][monster], key=lambda x: x[3],
                                reverse=True)
                for carve in carves:
                    carve_string = '  - {0} rank, x{2} {3}% from {1}'.format(
                                   *carve)
                    string.append([carve_string, 0])

        # Get quest info

        if 'quests' in info:
            string.append(['', 0])
            string.append(['Quests:', curses.A_BOLD])
            quests = sorted(info['quests'], key=lambda x: x[2], reverse=True)
            for quest in quests:
                string.append([' - {0}, {2}% x{1}'.format(*quest), 0])

        # Get map info

        if 'maps' in info:
            map_info = {}
            string.append(['', 0])
            string.append(['Maps:', curses.A_BOLD])
            maps = sorted(info['maps'], key=lambda x: map_sort(info['maps'], x),
                          reverse=True)
            for map_ in info['maps']:
                if map_ not in map_info:
                    map_info[map_] = {}
                for group in info['maps'][map_]:
                    rank, area, type_, amount = group
                    amount = int(amount[1:])
                    if rank not in map_info[map_]:
                        map_info[map_][rank] = {}
                    if area not in map_info[map_][rank]:
                        map_info[map_][rank][area] = {}
                    if type_ not in map_info[map_][rank][area]:
                        map_info[map_][rank][area][type_] = 0
                    map_info[map_][rank][area][type_] += amount

            for map_ in maps:
                string.append(['', 0])
                string.append([' {}'.format(map_), curses.A_BOLD])
                for rank in map_info[map_]:
                    string.append(['  {}'.format(rank), curses.A_BOLD])
                    areas = sorted(map_info[map_][rank],
                                   key=lambda x: int(x.split(' ')[1]))
                    for area in areas:
                        info = map_info[map_][rank][area]
                        type_ = list(info.keys())[0]
                        amount = info[type_]
                        string.append(['   - {}, {} {} spots'.format(area,
                                        amount, type_), 0])

        if 'combinations' in info:
            string.append(['', 0])
            string.append(["Combo's:", curses.A_BOLD])
            for combo in info['combinations']:
                if combo == []:
                    continue
                string.append([' - {} + {}'.format(*combo), 0])

        self.info_length = len(string)

        for index, line in enumerate(string[self.info_offset:]):
            if index == self.height-1:
                break
            text = line[0][:self.width-self.item_width-4]
            self.screen.addstr(1+index, self.item_width+2, text, line[1])
        return None

    def init_colors(self):
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        return None


def map_sort(info, item):
    low = 0
    high = 0
    for group in info[item]:
        rank, area, type_, amount = group
        amount = int(amount[1:])
        if rank == 'Low':
            low += amount
        else:
            high += amount
    if low > high:
        return low
    return high


def main():
    if not os.path.isdir(FILEDIR):
        os.mkdir(FILEDIR)

    if not os.path.exists('{}/items.json'.format(FILEDIR)):
        with open('{}/items.json'.format(FILEDIR), 'w') as f:
            f.write('[[null, null]]')
    
    with open('{}/items.json'.format(FILEDIR)) as f:
        items = json.loads(f.read())

    with open('gen.json', 'r') as f:
        info = json.loads(f.read())

    try:
        with ItemList(items, info) as item_list:
            item_list.main()
    except WindowSize:
        print('Please make sure you window does not get too small.')

    with open('{}/items.json'.format(FILEDIR), 'w') as f:
        f.write(json.dumps(items))
    return None


if __name__ == "__main__":
    main()
